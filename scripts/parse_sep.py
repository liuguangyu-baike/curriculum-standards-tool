#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEP数据解析脚本
从DCI Arrangements of NGSS文件中提取Science and Engineering Practices数据
"""

import re
import json
import os

# SEP编号与内容的对应关系
SEP_MAPPING = {
    1: "提出和定义问题",
    2: "开发和使用模型", 
    3: "策划和实施调查",
    4: "分析和解释数据",
    5: "使用数学和计算思维",
    6: "构建解释和设计解决方案",
    7: "依据证据进行辩论",
    8: "获取、评估和交流信息"
}

# 英文SEP名称到编号的映射
SEP_NAME_TO_NUMBER = {
    "Asking Questions and Defining Problems": 1,
    "Developing and Using Models": 2,
    "Planning and Carrying Out Investigations": 3,
    "Analyzing and Interpreting Data": 4,
    "Using Mathematics and Computational Thinking": 5,
    "Constructing Explanations and Designing Solutions": 6,
    "Engaging in Argument from Evidence": 7,
    "Obtaining, Evaluating, and Communicating Information": 8
}

def extract_grade_from_page(lines, start_idx):
    """从页面标题中提取学段信息"""
    # 向前查找页面标题（如 K-PS2, 1-PS4, MS-PS1, HS-LS1等）
    for i in range(max(0, start_idx - 20), start_idx + 1):
        line = lines[i].strip()
        # 匹配格式如 K-PS2, 1-PS4, MS-PS1, HS-LS1
        match = re.match(r'^(K|[1-5]|MS|HS)-([A-Z]{2,3})(\d+)\s+', line)
        if match:
            return match.group(1)
    return None

def extract_pe_codes(text):
    """从文本中提取PE编码"""
    # 匹配括号中的PE编码，如 (K-PS2-1) 或 (K-PS2-1),(K-PS2-2)
    pe_pattern = r'\(([A-Z0-9\-,\s]+)\)'
    matches = re.findall(pe_pattern, text)
    
    pe_codes = []
    for match in matches:
        # 分割多个PE编码
        codes = [code.strip() for code in match.split(',')]
        for code in codes:
            # 验证是否为有效的PE编码格式
            if re.match(r'^(K|[1-5]|MS|HS)-[A-Z]{2,3}\d+-\d+$', code):
                pe_codes.append(code)
    
    return pe_codes

def normalize_sep_name(name):
    """规范化SEP名称，去除额外的文字"""
    # 移除常见的描述性前缀
    name = re.sub(r'\s+in\s+(K–\d+|kindergarten|grade).*$', '', name, flags=re.IGNORECASE)
    return name.strip()

def parse_sep_section(lines, start_idx):
    """解析一个页面中的SEP部分"""
    seps = []
    i = start_idx
    
    # 提取学段
    grade = extract_grade_from_page(lines, start_idx)
    if not grade:
        return [], i
    
    # 找到 "Science and Engineering Practices" 部分
    while i < len(lines):
        line = lines[i].strip()
        if "Science and Engineering Practices" in line:
            i += 1
            break
        # 如果遇到 "Disciplinary Core Ideas"，说明没有SEP部分
        if "Disciplinary Core Ideas" in line:
            return [], i
        i += 1
        if i >= len(lines):
            return [], i
    
    # 解析SEP条目
    current_sep = None
    current_description = []
    point_number = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 遇到分隔线或下一个部分，结束SEP解析
        if '---' in line or 'Connections to Nature of Science' in line:
            i += 1
            break
        
        # 遇到 "Disciplinary Core Ideas" 结束
        if "Disciplinary Core Ideas" in line:
            break
        
        # 检查是否是新的SEP标题
        # SEP标题通常是独立一行的，且在映射表中
        is_sep_title = False
        sep_name = None
        sep_number = None
        
        for eng_name, num in SEP_NAME_TO_NUMBER.items():
            if eng_name in line:
                is_sep_title = True
                sep_name = eng_name
                sep_number = num
                break
        
        if is_sep_title:
            current_sep = {
                'sep_number': sep_number,
                'sep_name': SEP_MAPPING[sep_number],
                'sep_name_en': sep_name,
                'grade': grade
            }
            current_description = []
            point_number = 0
            i += 1
            continue
        
        # 如果有当前SEP，检查是否是要点
        if current_sep:
            # 要点以 ▪ 开头
            if line.startswith('▪'):
                point_number += 1
                
                # 提取要点内容（去除 ▪ 符号）
                point_text = line[1:].strip()
                
                # 可能跨多行，继续读取直到遇到下一个要点或分隔线
                full_point = [point_text]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if next_line.startswith('▪') or '---' in next_line:
                        break
                    if "Disciplinary Core Ideas" in next_line:
                        break
                    if "Connections to Nature of Science" in next_line:
                        break
                    # 检查是否是新的SEP标题
                    is_new_sep = any(name in next_line for name in SEP_NAME_TO_NUMBER.keys())
                    if is_new_sep:
                        break
                    
                    full_point.append(next_line)
                    j += 1
                
                point_content = ' '.join(full_point)
                
                # 提取PE编码
                pe_codes = extract_pe_codes(point_content)
                
                # 移除括号中的PE编码，保留纯文本内容
                clean_content = re.sub(r'\([A-Z0-9\-,\s]+\)$', '', point_content).strip()
                
                # 创建SEP条目
                sep_entry = {
                    'id': f"SEP-{current_sep['sep_number']}-{grade}-{point_number}",
                    'sepNumber': current_sep['sep_number'],
                    'sepName': current_sep['sep_name'],
                    'sepNameEn': current_sep['sep_name_en'],
                    'pointNumber': point_number,
                    'pointContent': clean_content,
                    'grade': grade,
                    'relatedPE': pe_codes
                }
                
                seps.append(sep_entry)
                
                i = j
                continue
            elif line and not line.startswith('Connections'):
                # 可能是SEP的描述性文本，暂时跳过
                # 根据需求文档，我们只需要提取要点内容
                pass
        
        i += 1
    
    return seps, i

def parse_file(file_path):
    """解析文件，提取全部SEP"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    seps = []
    i = 0
    
    while i < len(lines):
        line = lines[i].replace('\f', '').strip()
        
        # 跳过空行、版权信息、页码等
        if not line or line.startswith('©') or 'of 103' in line or line.startswith('September'):
            i += 1
            continue
        
        # 跳过目录和说明部分
        if 'Table of Contents' in line or 'Introduction' in line or 'Storyline' in line:
            i += 1
            continue
        
        # 查找包含 "Science and Engineering Practices" 的部分
        if "Science and Engineering Practices" in line:
            section_seps, next_idx = parse_sep_section(lines, i)
            seps.extend(section_seps)
            i = next_idx
            continue
        
        i += 1
    
    return seps

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    output_file = os.path.join(project_root, "web", "data", "sep_data.json")
    
    print("开始解析SEP数据...")
    seps = parse_file(input_file)
    
    print(f"\n解析完成:")
    print(f"  SEP条目总数: {len(seps)}")
    
    # 按SEP编号统计
    sep_counts = {}
    for sep in seps:
        sep_num = sep['sepNumber']
        sep_counts[sep_num] = sep_counts.get(sep_num, 0) + 1
    
    print("\n各SEP条目数量:")
    for sep_num in sorted(sep_counts.keys()):
        print(f"  SEP{sep_num} ({SEP_MAPPING[sep_num]}): {sep_counts[sep_num]}条")
    
    # 按学段统计
    grade_counts = {}
    for sep in seps:
        grade = sep['grade']
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    print("\n各学段条目数量:")
    grade_order = ['K', '1', '2', '3', '4', '5', 'MS', 'HS']
    for grade in grade_order:
        if grade in grade_counts:
            print(f"  {grade}: {grade_counts[grade]}条")
    
    # 显示前几条示例
    print("\n前5条SEP示例:")
    for sep in seps[:5]:
        print(f"\n{sep['id']}:")
        print(f"  SEP: {sep['sepName']} ({sep['sepNameEn']})")
        print(f"  学段: {sep['grade']}")
        print(f"  要点: {sep['pointContent'][:80]}..." if len(sep['pointContent']) > 80 else f"  要点: {sep['pointContent']}")
        print(f"  关联PE: {', '.join(sep['relatedPE']) if sep['relatedPE'] else '无'}")
    
    # 保存JSON文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"seps": seps}, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
