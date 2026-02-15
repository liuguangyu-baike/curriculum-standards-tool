#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCI数据解析脚本
提取Disciplinary Core Ideas（领域核心知识）
"""

import re
import json
import os

def extract_related_pes(text):
    """从文本中提取关联的PE编码"""
    # 匹配括号中的PE编码，支持多种格式：
    # - (K-PS2-1) 标准格式
    # - (KPS2-1) 缺少连字符
    # - (K-PS2-1),(K-PS2-2) 多个PE
    # - (secondary to K-PS2-1) secondary格式
    
    pes = []
    
    # 标准格式: (K-PS2-1) 或 (MS-PS2-1)
    pattern1 = r'\((?:secondary to\s+)?([K1-5]|MS|HS)-([A-Z]{2,3}\d+-\d+)\)'
    for match in re.finditer(pattern1, text):
        grade, code = match.groups()
        pes.append(f"{grade}-{code}")
    
    # 缺少连字符格式: (KPS2-1) 或 (K-PS2-1 without final parenthesis
    pattern2 = r'\(([K1-5])(PS|LS|ESS|ETS)(\d+-\d+)\)'
    for match in re.finditer(pattern2, text):
        grade, domain, num = match.groups()
        pes.append(f"{grade}-{domain}{num}")
    
    # 移除重复
    return list(dict.fromkeys(pes))

def extract_grades_from_pes(pes):
    """从PE编码列表中提取学段"""
    grades = set()
    for pe in pes:
        match = re.match(r'^(K|[1-5]|MS|HS)-', pe)
        if match:
            grades.add(match.group(1))
    return sorted(list(grades), key=lambda x: {'K': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'MS': 6, 'HS': 7}.get(x, 99))

def parse_dci_file(file_path, limit=None):
    """解析DCI文件，提取DCI数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    dcis = []
    current_dci_header = None  # 当前DCI标题行，例如 "PS2.A: Forces and Motion"
    current_domain = None
    current_core_concept_num = None
    current_sub_concept_letter = None
    current_sub_concept_title = None
    bullet_number = 0
    in_dci_section = False  # 是否在DCI部分
    
    # DCI标题模式，例如 "PS2.A: Forces and Motion"
    dci_header_pattern = r'^(PS|LS|ESS|ETS)(\d+)\.([A-Z]):\s*(.+)$'
    
    # 要点模式，例如 "▪ Pushes and pulls can have different strengths and directions. (K-PS2-1),(K-PS2-2)"
    # 或 "• Some text here" 或 " Some text here"（以空格开头的缩进行）
    bullet_pattern = r'^[▪•]\s*(.+)$'
    
    # 非DCI section标题（这些标题后面的内容不是DCI）
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
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检查是否是DCI标题行
        header_match = re.match(dci_header_pattern, line)
        if header_match:
            domain, core_num, sub_letter, sub_title = header_match.groups()
            current_domain = domain
            current_core_concept_num = int(core_num)
            current_sub_concept_letter = sub_letter
            current_sub_concept_title = sub_title.strip()
            in_dci_section = True  # 进入DCI部分
            
            # 处理跨行的标题（下一行不以▪开头，也不是新的DCI标题）
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
                # 继续收集标题
                current_sub_concept_title += ' ' + next_line
                j += 1
            
            current_sub_concept_title = re.sub(r'\s+', ' ', current_sub_concept_title).strip()
            bullet_number = 0
            i = j
            continue
        
        # 检查是否是非DCI section标题
        is_non_dci = False
        for section in non_dci_sections:
            if line.startswith(section) or line == section:
                is_non_dci = True
                in_dci_section = False
                current_domain = None  # 重置当前DCI
                break
        
        if is_non_dci:
            i += 1
            continue
        
        # 检查是否是分隔线
        if line.startswith('---') or line.startswith('==='):
            in_dci_section = False
            current_domain = None
            i += 1
            continue
        
        # 检查是否是要点行
        bullet_match = re.match(bullet_pattern, line)
        if bullet_match and current_domain and in_dci_section:
            bullet_number += 1
            bullet_content = bullet_match.group(1).strip()
            
            # 处理跨行的要点（下一行不以▪或•开头，也不是新的DCI标题）
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                # 如果是空行、新的要点、新的DCI标题、或其他section，停止
                if not next_line:
                    break
                if re.match(bullet_pattern, next_line):
                    break
                if re.match(dci_header_pattern, next_line):
                    break
                # 检查是否是其他section的开始（如Crosscutting Concepts, Science and Engineering Practices等）
                if next_line in ['Crosscutting Concepts', 'Science and Engineering Practices', 
                                 'Disciplinary Core Ideas', 'Common Core State Standards Connections:',
                                 'ELA/Literacy –', 'Mathematics –']:
                    break
                if next_line.startswith('Connections to'):
                    break
                if re.match(r'^(K|[1-5]|MS|HS)-[A-Z]{2,3}\d+\s+', next_line):
                    break
                
                # 继续收集内容
                bullet_content += ' ' + next_line
                j += 1
            
            # 清理内容
            bullet_content = re.sub(r'\s+', ' ', bullet_content).strip()
            
            # 提取关联PE
            related_pes = extract_related_pes(bullet_content)
            
            # 提取学段
            grades = extract_grades_from_pes(related_pes)
            
            # 清理要点内容（移除PE编码和括号）
            # 移除各种格式的PE编码括号
            clean_content = re.sub(r'\s*\((?:secondary to\s+)?[K1-5]?-?(?:MS|HS)?-?[A-Z]{2,3}\d+-\d+\)', '', bullet_content)
            clean_content = re.sub(r'\s*\([K1-5][A-Z]{2,3}\d+-\d+\)', '', clean_content)
            # 移除剩余的括号注释（如 "Note: ..." 或 "Boundary: ..."）
            clean_content = re.sub(r'\s*\((?:Note|Boundary|secondary)[^)]*\)', '', clean_content, flags=re.IGNORECASE)
            # 移除连续的逗号和多余空格
            clean_content = re.sub(r',\s*,', ',', clean_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            # 移除末尾的逗号
            clean_content = clean_content.rstrip(',')
            
            # 创建DCI条目
            dci_id = f"DCI-{current_domain}{current_core_concept_num}.{current_sub_concept_letter}-{bullet_number}"
            
            dci = {
                "id": dci_id,
                "domain": current_domain,
                "coreConceptNumber": current_core_concept_num,
                "subConceptLetter": current_sub_concept_letter,
                "subConceptTitle": current_sub_concept_title,
                "bulletNumber": bullet_number,
                "content": clean_content,
                "fullContent": bullet_content,  # 保留完整内容用于调试
                "grades": grades,
                "relatedPEs": related_pes
            }
            
            dcis.append(dci)
            
            if limit and len(dcis) >= limit:
                break
            
            i = j
            continue
        
        i += 1
    
    return dcis

def deduplicate_dcis(dcis):
    """去重DCI，同一个DCI id只保留一条，合并grades和relatedPEs"""
    seen = {}
    for dci in dcis:
        dci_id = dci['id']
        if dci_id in seen:
            # 合并grades和relatedPEs
            existing = seen[dci_id]
            for grade in dci['grades']:
                if grade not in existing['grades']:
                    existing['grades'].append(grade)
            for pe in dci['relatedPEs']:
                if pe not in existing['relatedPEs']:
                    existing['relatedPEs'].append(pe)
            # 如果新的content更长，使用新的
            if len(dci['content']) > len(existing['content']):
                existing['content'] = dci['content']
                existing['fullContent'] = dci['fullContent']
        else:
            seen[dci_id] = dci
    
    # 排序grades
    for dci in seen.values():
        dci['grades'] = sorted(dci['grades'], key=lambda x: {'K': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'MS': 6, 'HS': 7}.get(x, 99))
    
    return list(seen.values())

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    output_file = os.path.join(project_root, "web", "data", "dci_data.json")
    
    print("开始解析DCI数据（前20条）...")
    dcis = parse_dci_file(input_file, limit=20)
    dcis = deduplicate_dcis(dcis)
    
    print(f"\n解析完成，共 {len(dcis)} 条DCI")
    
    # 显示前20条
    print("\n前20条DCI:")
    for dci in dcis:
        print(f"\n{dci['id']}:")
        print(f"  subConceptTitle: {dci['subConceptTitle']}")
        print(f"  content: {dci['content'][:80]}..." if len(dci['content']) > 80 else f"  content: {dci['content']}")
        print(f"  grades: {dci['grades']}")
        print(f"  relatedPEs: {dci['relatedPEs']}")
    
    # 保存JSON文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"dcis": dcis}, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
