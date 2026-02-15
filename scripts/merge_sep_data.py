#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEP数据合并去重脚本
1. grade改为数组
2. 按pointContent合并去重，grade和relatedPE去重后合并
"""

import json
import os
import re
from collections import defaultdict

def normalize_content(text):
    """标准化pointContent用于比较"""
    if not text:
        return ""
    # 去除多余空白，统一为单个空格
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def grade_sort_key(grade):
    """年级排序顺序"""
    order = {'K': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 'MS': 6, 'HS': 7}
    return order.get(grade, 999)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "web", "data", "sep_data.json")
    
    print("=" * 60)
    print("SEP数据合并去重")
    print("=" * 60)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    seps = data.get('seps', [])
    print(f"\n原始条目数: {len(seps)}")
    
    # 按 (sepNumber, normalized pointContent) 分组
    groups = defaultdict(list)
    for sep in seps:
        key = (sep['sepNumber'], normalize_content(sep['pointContent']))
        groups[key].append(sep)
    
    # 合并每组
    merged = []
    for (sep_number, norm_content), items in groups.items():
        # 取第一条的sepName, sepNameEn, pointContent（使用第一条的原始内容）
        first = items[0]
        
        # 合并grades，去重，排序（兼容grade为字符串或数组）
        grades = []
        seen_grade = set()
        for item in items:
            g_val = item.get('grade') or item.get('grades', [])
            g_list = g_val if isinstance(g_val, list) else [g_val]
            for g in g_list:
                if g and g not in seen_grade:
                    seen_grade.add(g)
                    grades.append(g)
        grades.sort(key=grade_sort_key)
        
        # 合并relatedPE，去重，保持顺序（兼容relatedPE或relatedPEs）
        related_pe = []
        seen_pe = set()
        for item in items:
            pe_list = item.get('relatedPE') or item.get('relatedPEs', [])
            for pe in pe_list:
                if pe and pe not in seen_pe:
                    seen_pe.add(pe)
                    related_pe.append(pe)
        
        merged.append({
            'id': '',  # 稍后分配
            'sepNumber': sep_number,
            'sepName': first['sepName'],
            'sepNameEn': first['sepNameEn'],
            'pointNumber': 0,  # 稍后分配
            'pointContent': first['pointContent'],
            'grades': grades,
            'relatedPEs': related_pe
        })
    
    # 排序：SEP编号 -> 年级（取第一个）-> pointContent
    def sort_key(m):
        first_grade = m['grades'][0] if m['grades'] else 'Z'
        return (m['sepNumber'], grade_sort_key(first_grade), m['pointContent'])
    
    merged.sort(key=sort_key)
    
    # 分配pointNumber和id
    point_counters = defaultdict(int)
    for m in merged:
        sep_num = m['sepNumber']
        point_counters[sep_num] += 1
        m['pointNumber'] = point_counters[sep_num]
        m['id'] = f"SEP-{sep_num}-{m['pointNumber']}"
    
    print(f"合并后条目数: {len(merged)}")
    print(f"去重减少: {len(seps) - len(merged)} 条")
    
    # 示例：展示合并效果
    print("\n合并示例（同pointContent的条目）:")
    for (sep_number, norm_content), items in groups.items():
        if len(items) > 1:
            all_grades = []
            for i in items:
                g = i.get('grade') or i.get('grades', [])
                all_grades.extend(g if isinstance(g, list) else [g])
            grades_merged = sorted(set(all_grades), key=grade_sort_key)
            pe_list = [pe for i in items for pe in (i.get('relatedPE') or i.get('relatedPEs', []))]
            pe_merged = list(dict.fromkeys(pe_list))
            print(f"  {len(items)}条合并 -> grade:{grades_merged}, relatedPE:{len(pe_merged)}个")
            print(f"    内容: {norm_content[:60]}...")
    
    # 保存
    data['seps'] = merged
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 已保存到: {input_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
