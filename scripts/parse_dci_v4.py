#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCI数据解析脚本 v4
简化的提取逻辑，处理两种格式：
1. K-2和MS-HS格式：使用bullet符号（▪）
2. 3-5年级格式：缩进内容，按PE编码分段
"""

import re
import json
import os

# 核心概念标题映射
CORE_CONCEPT_TITLES = {
    "PS1": "Matter and Its Interactions",
    "PS2": "Motion and Stability: Forces and Interactions",
    "PS3": "Energy",
    "PS4": "Waves and Their Applications in Technologies for Information Transfer",
    "LS1": "From Molecules to Organisms: Structures and Processes",
    "LS2": "Ecosystems: Interactions, Energy, Dynamics",
    "LS3": "Heredity: Inheritance and Variation of Traits",
    "LS4": "Biological Evolution: Unity and Diversity",
    "ESS1": "Earth's Place in the Universe",
    "ESS2": "Earth's Systems",
    "ESS3": "Earth and Human Activity",
    "ETS1": "Engineering Design",
}

def extract_related_pes(text):
    """从文本中提取关联的PE编码"""
    pes = []
    
    # 标准格式: (K-PS2-1) 或 (MS-PS2-1)
    pattern1 = r'\((?:secondary to\s+)?([K1-5]|MS|HS)-([A-Z]{2,3}\d+-\d+)\)'
    for match in re.finditer(pattern1, text):
        grade, code = match.groups()
        pe = f"{grade}-{code}"
        if pe not in pes:
            pes.append(pe)
    
    # 缺少连字符格式: (KPS2-1)
    pattern2 = r'\(([K1-5])(PS|LS|ESS|ETS)(\d+-\d+)\)'
    for match in re.finditer(pattern2, text):
        grade, domain, num = match.groups()
        pe = f"{grade}-{domain}{num}"
        if pe not in pes:
            pes.append(pe)
    
    # 特殊格式: (K-ESS33) -> K-ESS3-3
    pattern3 = r'\(([K1-5]|MS|HS)-([A-Z]{2,3})(\d)(\d)\)'
    for match in re.finditer(pattern3, text):
        grade, domain, num1, num2 = match.groups()
        pe = f"{grade}-{domain}{num1}-{num2}"
        if pe not in pes:
            pes.append(pe)
    
    return pes

def extract_grade_from_pes(pes):
    """从PE编码列表中提取主要学段"""
    grades = set()
    for pe in pes:
        match = re.match(r'^(K|[1-5]|MS|HS)-', pe)
        if match:
            grades.add(match.group(1))
    
    sorted_grades = sorted(list(grades), key=lambda x: {'K': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'MS': 6, 'HS': 7}.get(x, 99))
    return sorted_grades[0] if sorted_grades else None

def clean_bullet_content(text):
    """清理要点内容"""
    clean = re.sub(r'\s*\((?:secondary to\s+)?[K1-5]?-?(?:MS|HS)?-?[A-Z]{2,3}\d+-\d+\)', '', text)
    clean = re.sub(r'\s*\([K1-5][A-Z]{2,3}\d+-\d+\)', '', clean)
    clean = re.sub(r'\s*\([K1-5]|MS|HS-[A-Z]{2,3}\d+\d+\)', '', clean)
    clean = re.sub(r'\s*\((?:Note|Boundary|secondary)[^)]*\)', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\(\s*\)', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = clean.rstrip(',')
    return clean

def split_by_pe_codes(text):
    """按PE编码分割文本，返回(content, pe_codes)列表"""
    # 找到所有PE编码及其位置
    pe_pattern = r'\((?:secondary to\s+)?([K1-5]|MS|HS)-([A-Z]{2,3}\d+-\d+)\)'
    matches = list(re.finditer(pe_pattern, text))
    
    if not matches:
        return [(text, [])]
    
    segments = []
    last_end = 0
    current_pes = []
    
    for i, match in enumerate(matches):
        # 如果这是第一个PE编码之前的内容
        if i == 0 and match.start() > 0:
            content = text[last_end:match.start()].strip()
            if content:
                segments.append((content, []))
        
        # 收集当前内容段的所有相邻PE编码
        current_pes = [f"{match.group(1)}-{match.group(2)}"]
        pe_end = match.end()
        
        # 查找紧跟的PE编码
        j = i + 1
        while j < len(matches):
            next_match = matches[j]
            between_text = text[pe_end:next_match.start()].strip()
            if not between_text or between_text in [',', '.', ';']:
                current_pes.append(f"{next_match.group(1)}-{next_match.group(2)}")
                pe_end = next_match.end()
                j += 1
            else:
                break
        
        # 提取PE编码之前的内容
        content_start = last_end if i > 0 else 0
        content = text[content_start:match.start()].strip()
        
        if content:
            segments.append((content, current_pes))
        
        last_end = pe_end
        i = j - 1
    
    return segments

def parse_dci_file(file_path, limit=None):
    """解析DCI文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    dci_groups = {}
    
    dci_header_pattern = r'^(PS|LS|ESS|ETS)(\d+)\.([A-Z]):\s*(.+)$'
    bullet_pattern = r'^[▪•]\s*(.+)$'
    
    non_dci_sections = [
        'Cause and Effect', 'Patterns', 'Scale, Proportion, and Quantity',
        'Systems and System Models', 'Energy and Matter', 'Structure and Function',
        'Stability and Change', 'Connections to Nature of Science',
        'Connections to Engineering', 'Common Core State Standards',
        'ELA/Literacy', 'Mathematics', 'Crosscutting Concepts',
        'Science and Engineering Practices',
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检查DCI标题
        header_match = re.match(dci_header_pattern, line)
        if not header_match:
            i += 1
            continue
        
        domain, core_num, sub_letter, sub_title = header_match.groups()
        core_num = int(core_num)
        sub_title = sub_title.strip()
        
        # 收集标题（处理跨行）
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if not next_line or re.match(bullet_pattern, next_line) or re.match(dci_header_pattern, next_line):
                break
            if any(next_line.startswith(s) for s in non_dci_sections):
                break
            if re.search(r'K[–-]2|3[–-]5|6[–-]8|builds on|progresses to', next_line):
                break
            sub_title += ' ' + next_line
            j += 1
        
        sub_title = re.sub(r'\s+', ' ', sub_title).strip()
        
        # 收集DCI内容
        content_lines = []
        while j < len(lines):
            line_raw = lines[j]
            line_stripped = line_raw.strip()
            
            # 停止条件
            if re.match(dci_header_pattern, line_stripped):
                break
            if any(line_stripped.startswith(s) for s in non_dci_sections):
                break
            if line_stripped.startswith('Connections to') or line_stripped.startswith('Articulation of'):
                break
            if not line_stripped:
                j += 1
                continue
            
            # 检查是否是bullet行或缩进行
            if re.match(bullet_pattern, line_stripped) or (line_raw and line_raw[0] == ' '):
                content_lines.append(line_stripped)
            else:
                # 可能是表格分隔或其他非DCI内容
                break
            
            j += 1
        
        # 处理收集到的内容
        if content_lines:
            # 区分两种格式：
            # 1. 有bullet符号（▪•）的格式：每个bullet是一个独立条目
            # 2. 没有bullet符号的格式（3-5年级）：需要按PE编码分割
            
            has_bullets = any(re.match(r'^[▪•]\s*', line) for line in content_lines)
            
            if has_bullets:
                # K-2和MS-HS格式：每个bullet是独立条目
                for line in content_lines:
                    # 移除bullet符号
                    line = re.sub(r'^[▪•]\s*', '', line).strip()
                    if not line:
                        continue
                    
                    # 提取PE编码
                    pes = extract_related_pes(line)
                    if not pes:
                        continue
                    
                    grade = extract_grade_from_pes(pes)
                    if not grade:
                        continue
                    
                    key = (domain, core_num, sub_letter, grade)
                    if key not in dci_groups:
                        dci_groups[key] = {
                            'domain': domain,
                            'coreConceptNumber': core_num,
                            'subConceptLetter': sub_letter,
                            'subConceptTitle': sub_title,
                            'grade': grade,
                            'bullets': []
                        }
                    
                    clean_content = clean_bullet_content(line)
                    
                    # 检查重复
                    existing = False
                    for bullet in dci_groups[key]['bullets']:
                        if bullet['cleanContent'] == clean_content:
                            for pe in pes:
                                if pe not in bullet['relatedPEs']:
                                    bullet['relatedPEs'].append(pe)
                            existing = True
                            break
                    
                    if not existing:
                        dci_groups[key]['bullets'].append({
                            'fullContent': line,
                            'cleanContent': clean_content,
                            'relatedPEs': pes
                        })
            else:
                # 3-5年级格式：按PE编码分割
                full_text = ' '.join(content_lines)
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                
                # 按PE编码分割
                segments = split_by_pe_codes(full_text)
                
                for content, pes in segments:
                    if not content or not pes:
                        continue
                    
                    grade = extract_grade_from_pes(pes)
                    if not grade:
                        continue
                    
                    key = (domain, core_num, sub_letter, grade)
                    if key not in dci_groups:
                        dci_groups[key] = {
                            'domain': domain,
                            'coreConceptNumber': core_num,
                            'subConceptLetter': sub_letter,
                            'subConceptTitle': sub_title,
                            'grade': grade,
                            'bullets': []
                        }
                    
                    clean_content = clean_bullet_content(content)
                    full_content = content + ' ' + ','.join([f'({pe})' for pe in pes])
                    
                    # 检查重复
                    existing = False
                    for bullet in dci_groups[key]['bullets']:
                        if bullet['cleanContent'] == clean_content:
                            for pe in pes:
                                if pe not in bullet['relatedPEs']:
                                    bullet['relatedPEs'].append(pe)
                            existing = True
                            break
                    
                    if not existing:
                        dci_groups[key]['bullets'].append({
                            'fullContent': full_content,
                            'cleanContent': clean_content,
                            'relatedPEs': pes
                        })
        
        i = j
    
    # 生成DCI列表
    dcis = []
    
    def sort_key(item):
        key, group = item
        domain, core_num, sub_letter, grade = key
        domain_order = {'PS': 0, 'LS': 1, 'ESS': 2, 'ETS': 3}.get(domain, 9)
        grade_order = {'K': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'MS': 6, 'HS': 7}.get(grade, 9)
        return (domain_order, core_num, sub_letter, grade_order)
    
    for key, group in sorted(dci_groups.items(), key=sort_key):
        domain = group['domain']
        core_num = group['coreConceptNumber']
        sub_letter = group['subConceptLetter']
        grade = group['grade']
        
        for idx, bullet in enumerate(group['bullets'], 1):
            dci_id = f"DCI-{domain}{core_num}.{sub_letter}-{grade}-{idx}"
            core_concept_key = f"{domain}{core_num}"
            core_concept_title = CORE_CONCEPT_TITLES.get(core_concept_key, "")
            
            dci = {
                "id": dci_id,
                "domain": domain,
                "coreConceptNumber": core_num,
                "coreConceptTitle": core_concept_title,
                "subConceptLetter": sub_letter,
                "subConceptTitle": group['subConceptTitle'],
                "grade": grade,
                "bulletNumber": idx,
                "content": bullet['cleanContent'],
                "fullContent": bullet['fullContent'],
                "relatedPEs": bullet['relatedPEs']
            }
            
            dcis.append(dci)
            
            if limit and len(dcis) >= limit:
                return dcis
    
    return dcis

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    output_file = os.path.join(project_root, "web", "data", "dci_data.json")
    
    print("开始解析DCI数据（前50条用于验证）...")
    dcis = parse_dci_file(input_file, limit=50)
    
    print(f"\n解析完成，共 {len(dcis)} 条DCI")
    
    # 按领域分组统计
    by_domain = {}
    for dci in dcis:
        key = f"{dci['domain']}{dci['coreConceptNumber']}.{dci['subConceptLetter']}-{dci['grade']}"
        if key not in by_domain:
            by_domain[key] = 0
        by_domain[key] += 1
    
    print("\n各DCI统计:")
    for key in sorted(by_domain.keys()):
        print(f"  {key}: {by_domain[key]}条")
    
    # 保存JSON
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"dcis": dcis}, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
