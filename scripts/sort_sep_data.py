#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEP数据排序脚本
按照SEP编号-年级-要点编号的顺序排序
"""

import json
import os

def grade_sort_key(grade):
    """定义年级的排序顺序"""
    grade_order = {
        'K': 0,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        'MS': 6,
        'HS': 7
    }
    return grade_order.get(grade, 999)

def sort_seps(seps):
    """按照SEP编号-年级-要点编号排序"""
    return sorted(seps, key=lambda x: (
        x['sepNumber'],           # 首先按SEP编号
        grade_sort_key(x['grade']),  # 然后按年级
        x['pointNumber']          # 最后按要点编号
    ))

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "web", "data", "sep_data.json")
    
    print("=" * 60)
    print("SEP数据排序")
    print("=" * 60)
    
    # 读取数据
    print(f"\n读取文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    seps = data.get('seps', [])
    print(f"原始数据条目数: {len(seps)}")
    
    # 排序前显示前5条
    print("\n排序前的前5条:")
    for sep in seps[:5]:
        print(f"  {sep['id']}: SEP{sep['sepNumber']}-{sep['grade']}-{sep['pointNumber']}")
    
    # 排序
    sorted_seps = sort_seps(seps)
    
    # 排序后显示前5条
    print("\n排序后的前5条:")
    for sep in sorted_seps[:5]:
        print(f"  {sep['id']}: SEP{sep['sepNumber']}-{sep['grade']}-{sep['pointNumber']}")
    
    # 统计
    print("\n按SEP编号和年级的分布:")
    from collections import defaultdict
    distribution = defaultdict(lambda: defaultdict(int))
    for sep in sorted_seps:
        distribution[sep['sepNumber']][sep['grade']] += 1
    
    for sep_num in sorted([1, 2, 3, 4, 5, 6, 7, 8]):
        if sep_num in distribution:
            print(f"\nSEP{sep_num}:")
            for grade in ['K', '1', '2', '3', '4', '5', 'MS', 'HS']:
                if grade in distribution[sep_num]:
                    count = distribution[sep_num][grade]
                    print(f"  {grade}: {count}条")
    
    # 保存排序后的数据
    data['seps'] = sorted_seps
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 排序完成，数据已保存到: {input_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
