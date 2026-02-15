#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEP数据解析脚本 V2
从DCI Arrangements of NGSS文件中提取Science and Engineering Practices数据
添加调试输出和改进逻辑
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
    for i in range(max(0, start_idx - 30), min(len(lines), start_idx + 10)):
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

def parse_sep_section(lines, start_idx):
    """解析一个页面中的SEP部分"""
    seps = []
    i = start_idx
    max_lines = len(lines)
    
    # 提取学段
    grade = extract_grade_from_page(lines, start_idx)
    if not grade:
        print(f"  警告: 在行 {start_idx} 附近无法提取学段信息")
        return [], i + 1
    
    print(f"  正在解析学段 {grade} 的SEP (起始行: {start_idx})")
    
    # 找到 "Science and Engineering Practices" 部分，并跳过标题行
    found_sep_section = False
    while i < max_lines and i < start_idx + 50:  # 限制搜索范围
        line = lines[i].strip()
        if "Science and Engineering Practices" in line:
            i += 1
            found_sep_section = True
            # 跳过可能的空行和三列标题（Science and Engineering Practices / Disciplinary Core Ideas / Crosscutting Concepts）
            skip_count = 0
            while i < max_lines and skip_count < 10:
                next_line = lines[i].strip()
                # 如果是空行或者是三个标题之一（独立一行的），跳过
                if not next_line:
                    i += 1
                    skip_count += 1
                    continue
                if next_line == "Disciplinary Core Ideas" or next_line == "Crosscutting Concepts":
                    i += 1
                    skip_count += 1
                    continue
                # 找到实际内容，停止跳过
                break
            break
        i += 1
    
    if not found_sep_section:
        print(f"    未找到SEP部分")
        return [], i
    
    # 解析SEP条目
    current_sep = None
    point_number = 0
    sep_count = 0
    
    while i < max_lines:
        line = lines[i].strip()
        
        # 遇到分隔线或下一个部分，结束SEP解析
        if '---' in line or 'Connections to Nature of Science' in line:
            print(f"    找到SEP结束标记: {line[:50]}")
            i += 1
            break
        
        # 遇到DCI的实际内容（以领域代码开头，如PS2.A:, LS1.C:, ESS2.D:等）结束
        if re.match(r'^[A-Z]{2,3}\d+\.[A-Z]:', line):
            print(f"    遇到DCI内容，结束SEP解析: {line[:50]}")
            break
        
        # 检查是否是新的SEP标题
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
            point_number = 0
            print(f"    找到SEP: {sep_name}")
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
                max_lookahead = 20  # 限制前向查找的行数
                lookahead = 0
                
                while j < max_lines and lookahead < max_lookahead:
                    next_line = lines[j].strip()
                    lookahead += 1
                    
                    if not next_line:
                        j += 1
                        continue
                    if next_line.startswith('▪') or '---' in next_line:
                        break
                    # 检查是否遇到DCI内容
                    if re.match(r'^[A-Z]{2,3}\d+\.[A-Z]:', next_line):
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
                clean_content = re.sub(r'\s*\([A-Z0-9\-,\s]+\)\s*$', '', point_content).strip()
                
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
                sep_count += 1
                
                i = j
                continue
        
        i += 1
    
    print(f"    完成，提取了 {sep_count} 条SEP要点")
    return seps, i

def parse_file(file_path):
    """解析文件，提取全部SEP"""
    print(f"读取文件: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    total_lines = len(lines)
    print(f"总行数: {total_lines}")
    
    seps = []
    i = 0
    section_count = 0
    
    while i < total_lines:
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
            section_count += 1
            print(f"\n找到第 {section_count} 个SEP部分 (行 {i})")
            section_seps, next_idx = parse_sep_section(lines, i)
            seps.extend(section_seps)
            i = next_idx
            continue
        
        i += 1
        
        # 每处理1000行打印一次进度
        if i % 1000 == 0:
            print(f"处理进度: {i}/{total_lines} 行 ({100*i//total_lines}%)")
    
    return seps

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    output_file = os.path.join(project_root, "web", "data", "sep_data.json")
    
    print("=" * 60)
    print("开始解析SEP数据 (V2版本)")
    print("=" * 60)
    
    seps = parse_file(input_file)
    
    print("\n" + "=" * 60)
    print("解析完成:")
    print("=" * 60)
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
    print("=" * 60)

if __name__ == "__main__":
    main()
