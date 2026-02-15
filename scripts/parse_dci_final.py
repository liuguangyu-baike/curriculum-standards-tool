#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCI数据解析脚本 v3
提取Disciplinary Core Ideas（领域核心知识）

新的ID格式：DCI-[领域][核心概念序号].[子概念序号]-[学段]-[要点序号]
例如：DCI-PS2.A-K-1
"""

import re
import json
import os

# 核心概念标题映射（从PE数据中提取）
CORE_CONCEPT_TITLES = {
    # PS - Physical Science
    "PS1": "Matter and Its Interactions",
    "PS2": "Motion and Stability: Forces and Interactions",
    "PS3": "Energy",
    "PS4": "Waves and Their Applications in Technologies for Information Transfer",
    # LS - Life Science
    "LS1": "From Molecules to Organisms: Structures and Processes",
    "LS2": "Ecosystems: Interactions, Energy, and Dynamics",
    "LS3": "Heredity: Inheritance and Variation of Traits",
    "LS4": "Biological Evolution: Unity and Diversity",
    # ESS - Earth and Space Science
    "ESS1": "Earth's Place in the Universe",
    "ESS2": "Earth's Systems",
    "ESS3": "Earth and Human Activity",
    # ETS - Engineering, Technology, and Applications of Science
    "ETS1": "Engineering Design",
}

def extract_related_pes(text):
    """从文本中提取关联的PE编码"""
    pes = []
    
    # 标准格式: (K-PS2-1) 或 (MS-PS2-1) 或 (secondary to K-PS2-1)
    pattern1 = r'\((?:secondary to\s+)?([K1-5]|MS|HS)-([A-Z]{2,3}\d+-\d+)\)'
    for match in re.finditer(pattern1, text):
        grade, code = match.groups()
        pe = f"{grade}-{code}"
        if pe not in pes:
            pes.append(pe)
    
    # 缺少连字符格式: (KPS2-1) 或 (KESS2-2)
    pattern2 = r'\(([K1-5])(PS|LS|ESS|ETS)(\d+-\d+)\)'
    for match in re.finditer(pattern2, text):
        grade, domain, num = match.groups()
        pe = f"{grade}-{domain}{num}"
        if pe not in pes:
            pes.append(pe)
    
    # 处理特殊格式如 (K-ESS33) -> K-ESS3-3
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
    
    # 返回排序后的第一个学段
    sorted_grades = sorted(list(grades), key=lambda x: {'K': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'MS': 6, 'HS': 7}.get(x, 99))
    return sorted_grades[0] if sorted_grades else None

def parse_dci_file(file_path, limit=None):
    """解析DCI文件，提取DCI数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 第一阶段：收集所有DCI条目（按学段和子概念分组）
    # key: (domain, coreConceptNum, subConceptLetter, grade)
    # value: list of bullets
    dci_groups = {}
    
    current_domain = None
    current_core_concept_num = None
    current_sub_concept_letter = None
    current_sub_concept_title = None
    in_dci_section = False
    
    # DCI标题模式，例如 "PS2.A: Forces and Motion"
    dci_header_pattern = r'^(PS|LS|ESS|ETS)(\d+)\.([A-Z]):\s*(.+)$'
    
    # 要点模式（支持▪、•、-、\uf0a7等bullet符号）
    # \uf0a7 是PDF提取时的特殊bullet字符（3-5年级和部分HS使用）
    # 注意：要区分bullet的-和分隔线的---
    bullet_pattern = r'^([▪•\uf0a7]|-(?!--))\s*(.+)$'
    
    # 非DCI section标题
    non_dci_sections = [
        'Cause and Effect',
        'Patterns',
        'Scale, Proportion, and Quantity',
        'Systems and System Models',
        'Energy and Matter',
        'Structure and Function',
        'Stability and Change',
        'Scientific Investigations Use a Variety of Methods',
        'Science Models, Laws, Mechanisms, and Theories Explain Natural Phenomena',
        'Science is a Human Endeavor',
        'Science Addresses Questions About the Natural and Material World',
        'Scientific Knowledge is Based on Empirical Evidence',
        'Scientific Knowledge Assumes an Order and Consistency in Natural Systems',
        'Connections to Nature of Science',
        'Connections to Engineering',
        'Influence of Engineering',
        'Interdependence of Science',
        'Common Core State Standards',
        'ELA/Literacy',
        'Mathematics',
        'Crosscutting Concepts',
        'Science and Engineering Practices',
        'Disciplinary Core Ideas',  # 这是section标题，不是DCI本身
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检查是否是非DCI section标题
        is_non_dci = False
        for section in non_dci_sections:
            if line.startswith(section) or line == section:
                is_non_dci = True
                in_dci_section = False
                break
        
        if is_non_dci:
            i += 1
            continue
        
        # 检查是否是分隔线
        if line.startswith('---') or line.startswith('==='):
            in_dci_section = False
            i += 1
            continue
        
        # 检查是否是DCI标题行
        header_match = re.match(dci_header_pattern, line)
        if header_match:
            domain, core_num, sub_letter, sub_title = header_match.groups()
            current_domain = domain
            current_core_concept_num = int(core_num)
            current_sub_concept_letter = sub_letter
            current_sub_concept_title = sub_title.strip()
            in_dci_section = True
            
            # 处理跨行的标题（只收集真正的标题，避免收集SEP描述）
            # 3-5年级和HS格式中，标题后面紧跟bullet内容，不需要收集跨行
            # K-2和MS格式中，标题可能跨行
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    break
                if re.match(bullet_pattern, next_line):
                    break
                if re.match(dci_header_pattern, next_line):
                    break
                # 检查是否是非DCI section
                is_non_dci = False
                for section in non_dci_sections:
                    if next_line.startswith(section):
                        is_non_dci = True
                        break
                if is_non_dci:
                    break
                # 检查是否是SEP描述（包含学段描述如"K–2", "3–5", "6–8", "in K–"等）
                if re.search(r'K[–-]2|3[–-]5|6[–-]8|9[–-]12|in K[–-]|in \d|builds on|progresses to', next_line):
                    break
                # 检查是否是以大写字母开头的完整句子（通常是SEP/CCC描述）
                if re.match(r'^[A-Z][a-z]+ing |^[A-Z][a-z]+ and [A-Z]', next_line):
                    break
                # 如果标题已经很长了（>60字符），停止收集
                if len(current_sub_concept_title) > 60:
                    break
                # 继续收集标题
                current_sub_concept_title += ' ' + next_line
                j += 1
            
            current_sub_concept_title = re.sub(r'\s+', ' ', current_sub_concept_title).strip()
            i = j
            continue
        
        # 检查是否是要点行（有bullet符号）或缩进行（3-5年级和HS格式）
        bullet_match = re.match(bullet_pattern, line)
        is_indented_line = (not bullet_match and current_domain and in_dci_section and 
                           lines[i] and len(lines[i]) > 0 and lines[i][0] == ' ' and line)
        
        if (bullet_match or is_indented_line) and current_domain and in_dci_section:
            if bullet_match:
                bullet_content = bullet_match.group(2).strip()  # group(2)是内容，group(1)是bullet符号
            else:
                bullet_content = line
            
            # 处理跨行的要点
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    break
                # 检查是否是新的bullet或新的DCI标题
                if re.match(bullet_pattern, next_line):
                    break
                if re.match(dci_header_pattern, next_line):
                    break
                # 检查是否是非DCI section
                is_non_dci = False
                for section in non_dci_sections:
                    if next_line.startswith(section):
                        is_non_dci = True
                        break
                if is_non_dci:
                    break
                if next_line.startswith('Connections to') or next_line.startswith('Articulation of'):
                    break
                # 继续收集内容
                bullet_content += ' ' + next_line
                j += 1
            
            # 清理内容
            bullet_content = re.sub(r'\s+', ' ', bullet_content).strip()
            
            # 提取关联PE
            related_pes = extract_related_pes(bullet_content)
            
            # 提取学段
            grade = extract_grade_from_pes(related_pes)
            
            if grade:
                # 创建分组key
                key = (current_domain, current_core_concept_num, current_sub_concept_letter, grade)
                
                if key not in dci_groups:
                    dci_groups[key] = {
                        'domain': current_domain,
                        'coreConceptNumber': current_core_concept_num,
                        'subConceptLetter': current_sub_concept_letter,
                        'subConceptTitle': current_sub_concept_title,
                        'grade': grade,
                        'bullets': []
                    }
                
                # 检查是否已存在相同内容的bullet
                # 清理content用于比较
                clean_content = clean_bullet_content(bullet_content)
                
                existing = False
                for bullet in dci_groups[key]['bullets']:
                    if bullet['cleanContent'] == clean_content:
                        # 合并PE
                        for pe in related_pes:
                            if pe not in bullet['relatedPEs']:
                                bullet['relatedPEs'].append(pe)
                        existing = True
                        break
                
                if not existing:
                    dci_groups[key]['bullets'].append({
                        'fullContent': bullet_content,
                        'cleanContent': clean_content,
                        'relatedPEs': related_pes
                    })
            
            i = j
            continue
        
        # 检查是否是没有bullet符号但有缩进的DCI内容行（3-5年级格式）
        # 这种行以空格开头，不是bullet pattern，但在DCI section中
        if current_domain and in_dci_section and not line and i > 0:
            # 空行，可能是要收集DCI内容的开始
            j = i + 1
            if j < len(lines):
                next_line_raw = lines[j]
                next_line = next_line_raw.strip()
                # 检查下一行是否是缩进内容（以空格开头，不是DCI标题，不是非DCI section）
                if next_line_raw and next_line_raw[0] == ' ' and next_line:
                    # 收集所有缩进内容直到下一个DCI标题或非DCI section
                    content_block = []
                    while j < len(lines):
                        line_raw = lines[j]
                        line_stripped = line_raw.strip()
                        
                        # 检查是否结束
                        if not line_stripped:
                            j += 1
                            continue
                        if re.match(dci_header_pattern, line_stripped):
                            break
                        # 检查是否是非DCI section
                        is_non_dci = False
                        for section in non_dci_sections:
                            if line_stripped.startswith(section):
                                is_non_dci = True
                                break
                        if is_non_dci:
                            break
                        if line_stripped.startswith('Connections to'):
                            break
                        if line_stripped.startswith('Articulation of DCIs'):
                            break
                        
                        # 收集内容
                        content_block.append(line_stripped)
                        j += 1
                    
                    # 将内容块按PE编码分割
                    if content_block:
                        full_text = ' '.join(content_block)
                        # 按PE编码分割（寻找(X-XXX-X)模式）
                        pe_split_pattern = r'(\([K1-5]|MS|HS-[A-Z]{2,3}\d+-\d+\))'
                        parts = re.split(pe_split_pattern, full_text)
                        
                        current_bullet = ""
                        current_pes = []
                        
                        for part in parts:
                            if re.match(pe_split_pattern, part):
                                # 这是PE编码
                                pes = extract_related_pes(part)
                                current_pes.extend(pes)
                            else:
                                # 这是内容
                                part = part.strip()
                                if part:
                                    if current_bullet and current_pes:
                                        # 保存之前的bullet
                                        grade = extract_grade_from_pes(current_pes)
                                        if grade:
                                            key = (current_domain, current_core_concept_num, current_sub_concept_letter, grade)
                                            if key not in dci_groups:
                                                dci_groups[key] = {
                                                    'domain': current_domain,
                                                    'coreConceptNumber': current_core_concept_num,
                                                    'subConceptLetter': current_sub_concept_letter,
                                                    'subConceptTitle': current_sub_concept_title,
                                                    'grade': grade,
                                                    'bullets': []
                                                }
                                            
                                            clean_content = clean_bullet_content(current_bullet)
                                            full_content = current_bullet + ' ' + ''.join([f'({pe})' for pe in current_pes])
                                            
                                            # 检查重复
                                            existing = False
                                            for bullet in dci_groups[key]['bullets']:
                                                if bullet['cleanContent'] == clean_content:
                                                    for pe in current_pes:
                                                        if pe not in bullet['relatedPEs']:
                                                            bullet['relatedPEs'].append(pe)
                                                    existing = True
                                                    break
                                            
                                            if not existing:
                                                dci_groups[key]['bullets'].append({
                                                    'fullContent': full_content,
                                                    'cleanContent': clean_content,
                                                    'relatedPEs': current_pes
                                                })
                                    
                                    # 开始新的bullet
                                    current_bullet = part
                                    current_pes = []
                        
                        # 保存最后一个bullet
                        if current_bullet and current_pes:
                            grade = extract_grade_from_pes(current_pes)
                            if grade:
                                key = (current_domain, current_core_concept_num, current_sub_concept_letter, grade)
                                if key not in dci_groups:
                                    dci_groups[key] = {
                                        'domain': current_domain,
                                        'coreConceptNumber': current_core_concept_num,
                                        'subConceptLetter': current_sub_concept_letter,
                                        'subConceptTitle': current_sub_concept_title,
                                        'grade': grade,
                                        'bullets': []
                                    }
                                
                                clean_content = clean_bullet_content(current_bullet)
                                full_content = current_bullet + ' ' + ''.join([f'({pe})' for pe in current_pes])
                                
                                # 检查重复
                                existing = False
                                for bullet in dci_groups[key]['bullets']:
                                    if bullet['cleanContent'] == clean_content:
                                        for pe in current_pes:
                                            if pe not in bullet['relatedPEs']:
                                                bullet['relatedPEs'].append(pe)
                                        existing = True
                                        break
                                
                                if not existing:
                                    dci_groups[key]['bullets'].append({
                                        'fullContent': full_content,
                                        'cleanContent': clean_content,
                                        'relatedPEs': current_pes
                                    })
                    
                    i = j
                    continue
        
        i += 1
    
    # 第二阶段：生成DCI列表
    dcis = []
    
    # 自定义排序：领域(PS/LS/ESS/ETS) -> 核心概念序号 -> 子概念字母 -> 学段
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
            
            # 获取coreConceptTitle
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

def clean_bullet_content(text):
    """清理要点内容，移除PE编码和注释"""
    # 移除各种格式的PE编码括号
    clean = re.sub(r'\s*\((?:secondary to\s+)?[K1-5]?-?(?:MS|HS)?-?[A-Z]{2,3}\d+-\d+\)', '', text)
    clean = re.sub(r'\s*\([K1-5][A-Z]{2,3}\d+-\d+\)', '', clean)
    clean = re.sub(r'\s*\([K1-5]|MS|HS-[A-Z]{2,3}\d+\d+\)', '', clean)
    # 移除 (Note: ...) 和 (Boundary: ...) 和 (secondary ...)
    clean = re.sub(r'\s*\((?:Note|Boundary|secondary)[^)]*\)', '', clean, flags=re.IGNORECASE)
    # 移除空括号
    clean = re.sub(r'\(\s*\)', '', clean)
    # 清理多余空格
    clean = re.sub(r'\s+', ' ', clean).strip()
    # 移除末尾的逗号
    clean = clean.rstrip(',')
    return clean

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    output_file = os.path.join(project_root, "web", "data", "dci_data.json")
    
    print("开始解析DCI数据（全部）...")
    dcis = parse_dci_file(input_file, limit=None)
    
    print(f"\n解析完成，共 {len(dcis)} 条DCI")
    
    # 显示前20条
    print("\n前20条DCI:")
    for dci in dcis:
        print(f"\n{dci['id']}:")
        print(f"  coreConceptTitle: {dci['coreConceptTitle']}")
        print(f"  subConceptTitle: {dci['subConceptTitle']}")
        print(f"  content: {dci['content'][:80]}..." if len(dci['content']) > 80 else f"  content: {dci['content']}")
        print(f"  grade: {dci['grade']}")
        print(f"  relatedPEs: {dci['relatedPEs']}")
    
    # 保存JSON文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"dcis": dcis}, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
