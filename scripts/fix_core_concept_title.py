#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复PE数据中的coreConceptTitle错位问题
只修改coreConceptTitle，不改动其他字段
"""

import re
import json
import os

def extract_core_concept_titles(file_path):
    """从原始文件中提取所有core concept的标题"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 映射：(grade, domain, coreConceptNumber) -> title
    titles = {}
    
    # 匹配PE标题行，例如 "K-PS2 Motion and Stability: Forces and Interactions"
    title_pattern = r'^(K|[1-5]|MS|HS)-([A-Z]{2,3})(\d+)\s+(.+)$'
    
    for line in lines:
        line = line.replace('\f', '').strip()
        match = re.match(title_pattern, line)
        if match:
            grade, domain, core_concept_num, title = match.groups()
            # 清理标题（移除页码等）
            title = re.sub(r'\s*\.+\s*\d+\s*$', '', title).strip()
            key = (grade, domain, int(core_concept_num))
            titles[key] = title
    
    return titles

def fix_core_concept_titles(pe_data, titles):
    """修复PE数据中的coreConceptTitle"""
    fixed_count = 0
    
    for pe in pe_data['pes']:
        grade = pe['grade']
        domain = pe['domain']
        core_concept_num = pe['coreConceptNumber']
        
        key = (grade, domain, core_concept_num)
        if key in titles:
            correct_title = titles[key]
            if pe['coreConceptTitle'] != correct_title:
                print(f"修复 {pe['id']}: '{pe['coreConceptTitle']}' -> '{correct_title}'")
                pe['coreConceptTitle'] = correct_title
                fixed_count += 1
    
    return pe_data, fixed_count

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_txt = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    pe_json = os.path.join(project_root, "web", "data", "pe_data.json")
    
    print("从原始文件提取core concept标题...")
    titles = extract_core_concept_titles(input_txt)
    print(f"找到 {len(titles)} 个core concept标题")
    
    # 打印提取到的标题
    print("\n提取到的标题:")
    for key, title in sorted(titles.items()):
        print(f"  {key[0]}-{key[1]}{key[2]}: {title}")
    
    print("\n读取PE数据...")
    with open(pe_json, 'r', encoding='utf-8') as f:
        pe_data = json.load(f)
    print(f"共 {len(pe_data['pes'])} 条PE")
    
    print("\n修复coreConceptTitle...")
    pe_data, fixed_count = fix_core_concept_titles(pe_data, titles)
    
    print(f"\n共修复 {fixed_count} 个coreConceptTitle")
    
    # 保存修复后的数据
    with open(pe_json, 'w', encoding='utf-8') as f:
        json.dump(pe_data, f, ensure_ascii=False, indent=2)
    print(f"已保存到: {pe_json}")

if __name__ == "__main__":
    main()
