#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEP数据解析脚本 V4
从DCI Arrangements of NGSS文件中提取Science and Engineering Practices数据
改进策略：先收集所有要点，然后智能过滤
"""

import re
import json
import os
from collections import defaultdict

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
    for i in range(max(0, start_idx - 30), min(len(lines), start_idx + 10)):
        line = lines[i].strip()
        match = re.match(r'^(K|[1-5]|MS|HS)-([A-Z]{2,3})(\d+)\s+', line)
        if match:
            return match.group(1)
    return None

def extract_pe_codes(text):
    """从文本中提取PE编码"""
    pe_pattern = r'\(([A-Z0-9\-,\s]+)\)'
    matches = re.findall(pe_pattern, text)
    
    pe_codes = []
    for match in matches:
        codes = [code.strip() for code in match.split(',')]
        for code in codes:
            # 修复格式错误：如 K-PS32 -> K-PS3-2, 1-LS31 -> 1-LS3-1
            fixed_code = re.sub(r'^([A-Z0-9\-]+)([A-Z]{2,3})(\d)(\d+)$', r'\1\2\3-\4', code)
            if re.match(r'^(K|[1-5]|MS|HS)-[A-Z]{2,3}\d+-\d+$', fixed_code):
                pe_codes.append(fixed_code)
            elif re.match(r'^(K|[1-5]|MS|HS)-[A-Z]{2,3}\d+-\d+$', code):
                pe_codes.append(code)
    
    return pe_codes

def clean_point_content(text):
    """清理要点内容"""
    # 移除PE编码
    text = re.sub(r'\s*\([A-Z0-9\-,\s]+\)\s*$', '', text).strip()
    # 移除末尾的标题文本
    text = re.sub(r'\s*(Disciplinary Core Ideas|Crosscutting Concepts|Science and Engineering Practices)\s*$', '', text, flags=re.IGNORECASE).strip()
    # 移除多余的空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_likely_sep_content(text):
    """判断文本是否可能是SEP内容"""
    # DCI内容通常以领域代码开头
    if re.match(r'^[A-Z]{2,3}\d+\.[A-Z]:', text):
        return False
    # CCC内容通常较短，且不包含动词
    if len(text) < 30 and not any(word in text.lower() for word in ['ask', 'develop', 'plan', 'analyze', 'use', 'construct', 'engage', 'obtain']):
        return False
    return True

def parse_sep_section(lines, start_idx, point_counters):
    """解析一个页面中的SEP部分 - 改进版"""
    seps = []
    i = start_idx
    max_lines = len(lines)
    
    # 提取学段
    grade = extract_grade_from_page(lines, start_idx)
    if not grade:
        print(f"  警告: 在行 {start_idx} 附近无法提取学段信息")
        return [], i + 1
    
    print(f"  正在解析学段 {grade} 的SEP (起始行: {start_idx})")
    
    # 找到 "Science and Engineering Practices" 部分
    found_sep_section = False
    while i < max_lines and i < start_idx + 50:
        line = lines[i].strip()
        if "Science and Engineering Practices" in line:
            i += 1
            found_sep_section = True
            # 跳过空行和标题行
            skip_count = 0
            while i < max_lines and skip_count < 10:
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    skip_count += 1
                    continue
                if next_line == "Disciplinary Core Ideas" or next_line == "Crosscutting Concepts":
                    i += 1
                    skip_count += 1
                    continue
                break
            break
        i += 1
    
    if not found_sep_section:
        print(f"    未找到SEP部分")
        return [], i
    
    # 收集SEP部分的所有内容，直到遇到明确的结束标记
    sep_section_end = i
    for j in range(i, min(i + 200, max_lines)):  # 限制搜索范围
        line = lines[j].strip()
        if '---' in line or 'Connections to other DCIs' in line:
            sep_section_end = j
            break
        if 'Common Core State Standards' in line:
            sep_section_end = j
            break
    
    # 解析这个范围内的内容
    current_sep = None
    sep_count = 0
    j = i
    
    while j < sep_section_end:
        line = lines[j].strip()
        
        # 检查是否是SEP标题
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
            print(f"    找到SEP: {sep_name}")
            j += 1
            continue
        
        # 如果有当前SEP，检查是否是要点
        if current_sep:
            # 要点以 ▪ 开头
            if line.startswith('▪'):
                # 提取要点内容
                point_text = line[1:].strip()
                
                # 读取跨行内容
                full_point = [point_text]
                k = j + 1
                max_lookahead = 15
                lookahead = 0
                
                while k < sep_section_end and lookahead < max_lookahead:
                    next_line = lines[k].strip()
                    lookahead += 1
                    
                    if not next_line:
                        k += 1
                        continue
                    # 遇到新要点或SEP标题，停止
                    if next_line.startswith('▪'):
                        break
                    if any(name in next_line for name in SEP_NAME_TO_NUMBER.keys()):
                        break
                    # 如果遇到明显的DCI或CCC内容，停止
                    if re.match(r'^[A-Z]{2,3}\d+\.[A-Z]:', next_line):
                        break
                    if next_line in ["Cause and Effect", "Patterns", "Scale, Proportion, and Quantity", 
                                   "Systems and System Models", "Energy and Matter", "Structure and Function",
                                   "Stability and Change"]:
                        break
                    
                    full_point.append(next_line)
                    k += 1
                
                point_content = ' '.join(full_point)
                
                # 检查是否是合理的SEP内容
                if not is_likely_sep_content(point_content):
                    j = k
                    continue
                
                # 提取PE编码
                pe_codes = extract_pe_codes(point_content)
                
                # 清理内容
                clean_content = clean_point_content(point_content)
                
                # 如果内容过短或为空，跳过
                if len(clean_content) < 15:
                    j = k
                    continue
                
                # 使用全局计数器生成唯一ID
                sep_grade_key = (current_sep['sep_number'], grade)
                point_counters[sep_grade_key] += 1
                point_number = point_counters[sep_grade_key]
                
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
                
                j = k
                continue
        
        j += 1
    
    print(f"    完成，提取了 {sep_count} 条SEP要点")
    return seps, sep_section_end

def parse_file(file_path):
    """解析文件，提取全部SEP"""
    print(f"读取文件: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    total_lines = len(lines)
    print(f"总行数: {total_lines}")
    
    # 全局计数器
    point_counters = defaultdict(int)
    
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
        
        # 查找 "Science and Engineering Practices"
        if "Science and Engineering Practices" in line:
            section_count += 1
            print(f"\n找到第 {section_count} 个SEP部分 (行 {i})")
            section_seps, next_idx = parse_sep_section(lines, i, point_counters)
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
    print("开始解析SEP数据 (V4版本)")
    print("=" * 60)
    
    seps = parse_file(input_file)
    
    print("\n" + "=" * 60)
    print("解析完成:")
    print("=" * 60)
    print(f"  SEP条目总数: {len(seps)}")
    
    # 检查ID唯一性
    ids = [sep['id'] for sep in seps]
    unique_ids = set(ids)
    if len(ids) == len(unique_ids):
        print(f"  ✓ 所有ID唯一")
    else:
        print(f"  ✗ 发现重复ID: {len(ids) - len(unique_ids)}个")
    
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
        content_preview = sep['pointContent'][:80] + "..." if len(sep['pointContent']) > 80 else sep['pointContent']
        print(f"  要点: {content_preview}")
        print(f"  关联PE: {', '.join(sep['relatedPE']) if sep['relatedPE'] else '无'}")
    
    # 保存JSON文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"seps": seps}, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
