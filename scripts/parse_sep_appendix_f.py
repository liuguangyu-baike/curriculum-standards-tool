#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Appendix F Science and Engineering Practices.pdf 第17-32页提取SEP数据
按照需求文档格式：SEP-[Practice序号]-[学段]-[类目序号]-[项目序号]
"""

import re
import json
import os
import pdfplumber

# SEP编号与中英文名称
SEP_MAPPING = {
    1: ("Asking Questions and Defining Problems", "提出和定义问题"),
    2: ("Developing and using models", "开发和使用模型"),
    3: ("Planning and carrying out investigations", "策划和实施调查"),
    4: ("Analyzing and interpreting data", "分析和解释数据"),
    5: ("Using mathematics and computational thinking", "使用数学和计算思维"),
    6: ("Constructing explanations and designing solutions", "构建解释和设计解决方案"),
    7: ("Engaging in argument from evidence", "依据证据进行辩论"),
    8: ("Obtaining, evaluating, and communicating information", "获取、评估和交流信息"),
}

GRADE_BANDS = ["K-2", "3-5", "6-8", "9-12"]
GRADE_ID_MAP = {"K-2": "K_2", "3-5": "3_5", "6-8": "6_8", "9-12": "9_12"}

# 每个Practice开始的页码（1-based）
PRACTICE_PAGES = {
    1: 17, 2: 19, 3: 21, 4: 23, 5: 25, 6: 27, 7: 29, 8: 31
}

def normalize_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def parse_bullet_cell(cell_text):
    """
    解析包含bullet的单元格，返回 [(类目号, 项目号, 内容), ...]
    主bullet • 为类目，子bullet o 为项目
    """
    if not cell_text or ('\uf0b7' not in cell_text and '•' not in cell_text):
        return []
    
    items = []
    # 按主bullet分割
    main_parts = re.split(r'\s*[•\uf0b7]\s*', cell_text)
    
    for part in main_parts:
        part = part.strip()
        if not part:
            continue
        
        # 检查子bullet (o that, o to, ...)
        sub_parts = re.split(r'(?=\no\s+)', '\n' + part)
        if len(sub_parts) > 1:
            first = sub_parts[0].replace('\no ', '').strip()
            if first:
                items.append((1, 1, first))  # 类目1项目1
            for i, sp in enumerate(sub_parts[1:], 1):
                sp = re.sub(r'^\no\s+', '', sp).strip()
                if sp:
                    items.append((1, i+1, sp))  # 同一类目下多个项目
        else:
            items.append((1, 1, part))
    
    # 重新编号类目和项目
    result = []
    cat_num, item_num = 1, 1
    for _, _, content in items:
        result.append((cat_num, item_num, content))
        item_num += 1
    return result

def extract_tables_by_column(pdf_path):
    """提取表格，按列分组到4个学段"""
    # 收集所有页面的表格数据
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in range(16, min(32, len(pdf.pages))):
            p = pdf.pages[page_idx]
            tables = p.find_tables()
            for t in tables:
                data = t.extract()
                if data:
                    # 获取表格的列边界
                    cells = t.cells
                    if cells:
                        # 按x坐标分组列
                        pass
                    all_data.append((page_idx + 1, data, t.bbox))
    
    return all_data

def extract_seps_from_pdf(pdf_path):
    """主提取逻辑"""
    seps = []
    grade_goals = {g: "" for g in GRADE_BANDS}
    
    with pdfplumber.open(pdf_path) as pdf:
        # 策略：提取每页文本，按practice和学段解析
        full_text_by_page = {}
        for i in range(16, min(32, len(pdf.pages))):
            text = pdf.pages[i].extract_text()
            full_text_by_page[i + 1] = text or ""
        
        # 根据页码确定practice (每2页一个practice)
        cat_counter = {g: 1 for g in GRADE_BANDS}
        last_practice = 0
        
        for page_num in range(17, 33):
            text = full_text_by_page.get(page_num, "")
            current_practice = 0
            if page_num <= 18:
                current_practice = 1
            elif page_num <= 20:
                current_practice = 2
            elif page_num <= 22:
                current_practice = 3
            elif page_num <= 24:
                current_practice = 4
            elif page_num <= 26:
                current_practice = 5
            elif page_num <= 28:
                current_practice = 6
            elif page_num <= 30:
                current_practice = 7
            else:
                current_practice = 8
            
            # 新practice时重置类目计数器
            if current_practice != last_practice:
                cat_counter = {g: 1 for g in GRADE_BANDS}
                last_practice = current_practice
            
            # 提取学段目标
            for gband in GRADE_BANDS:
                gpat = gband.replace('-', '[–\-]')
                match = re.search(rf'[Aa]sking questions and defining problems in {gpat} builds on[^.]+\.', text)
                if not match:
                    match = re.search(rf'[Mm]odeling in {gpat} builds on[^.]+\.', text)
                if not match:
                    match = re.search(rf'[Pp]lanning and carrying out investigations[^.]*in {gpat}[^.]*builds on[^.]+\.', text)
                if not match:
                    match = re.search(rf'[Aa]nalyzing data in {gpat}[^.]*builds on[^.]+\.', text)
                if not match:
                    match = re.search(rf'[Mm]athematical and computational thinking in {gpat}[^.]*builds on[^.]+\.', text)
                if not match:
                    match = re.search(rf'[Cc]onstructing explanations[^.]*in {gpat}[^.]*builds on[^.]+\.', text)
                if not match:
                    match = re.search(rf'[Ee]ngaging in argument from evidence in {gpat}[^.]*builds on[^.]+\.', text)
                if not match:
                    match = re.search(rf'[Oo]btaining, evaluating, and communicating information in {gpat}[^.]*builds on[^.]+\.', text)
                if match and not grade_goals.get(gband):
                    grade_goals[gband] = normalize_text(match.group(0))
            
            tables = pdf.pages[page_num - 1].find_tables()
            for table in tables:
                data = table.extract()
                if not data:
                    continue
                
                # 动态检测4个学段列：找包含bullet的列，取前4个（从左到右）
                bullet_cols = set()
                for row in data:
                    for col_idx, cell in enumerate(row):
                        if cell and ('\uf0b7' in str(cell) or '•' in str(cell)):
                            bullet_cols.add(col_idx)
                bullet_cols = sorted(bullet_cols)
                if len(bullet_cols) >= 4:
                    # 取最右边的4列（排除最左可能是practice名的列）
                    cols_4 = bullet_cols[-4:]
                    col_to_grade = {cols_4[i]: GRADE_BANDS[i] for i in range(4)}
                elif len(bullet_cols) > 0:
                    col_to_grade = {c: GRADE_BANDS[min(i, 3)] for i, c in enumerate(bullet_cols)}
                else:
                    continue
                
                # 提取学段目标：每列第一个含"builds on"的单元格（无bullet）
                for row in data:
                    for col_idx, cell in enumerate(row):
                        if col_idx not in col_to_grade:
                            continue
                        if not cell:
                            continue
                        cell_str = str(cell).strip()
                        grade = col_to_grade[col_idx]
                        # 学段目标：包含builds on且不含bullet
                        if 'builds on' in cell_str.lower() and '\uf0b7' not in cell_str and '•' not in cell_str:
                            if not grade_goals.get(grade) or len(cell_str) > len(grade_goals.get(grade, "")):
                                grade_goals[grade] = normalize_text(cell_str)
                
                for row in data:
                    for col_idx, cell in enumerate(row):
                        if col_idx not in col_to_grade:
                            continue
                        if not cell:
                            continue
                        cell_str = str(cell).strip()
                        if '\uf0b7' not in cell_str and '•' not in cell_str:
                            continue
                        
                        grade = col_to_grade[col_idx]
                        cat_num = cat_counter[grade]
                        
                        # 同一单元格=同一类目，每个主bullet=一个项目(itemNumber 1,2,3...)
                        # 只按第一级bullet(•)提取，子bullet(o)合并到同一项目
                        parts = re.split(r'\s*[•\uf0b7]\s*', cell_str)
                        item_num = 1
                        for part in parts:
                            part = part.strip()
                            if not part or len(part) < 3:
                                continue
                            
                            # 合并子bullet内容到主bullet（只取第一级，子级合并为一条）
                            sub_parts = re.split(r'\no\s+', '\n' + part)
                            if len(sub_parts) > 1:
                                # 主bullet + 所有子bullet 合并为一条内容
                                main_text = sub_parts[0].strip()
                                sub_texts = [normalize_text(s.strip()) for s in sub_parts[1:] if s.strip()]
                                content = normalize_text(main_text)
                                if sub_texts:
                                    content = content + " " + "; ".join(sub_texts)
                            else:
                                content = normalize_text(part)
                            
                            if content and len(content) >= 5:
                                sep = create_sep_entry(
                                    current_practice, grade, cat_num, item_num,
                                    content, grade_goals.get(grade, "")
                                )
                                if sep:
                                    seps.append(sep)
                                item_num += 1
                        if item_num > 1:  # 该单元格有提取到内容
                            cat_counter[grade] += 1
    
    return seps

def create_sep_entry(practice_num, grade_band, category_num, item_num, content, grade_goal):
    if practice_num < 1 or practice_num > 8 or not content or len(content) < 5:
        return None
    
    en_name, zh_name = SEP_MAPPING[practice_num]
    grade_id = GRADE_ID_MAP.get(grade_band, grade_band.replace('-', '_'))
    
    return {
        "id": f"SEP-{practice_num}-{grade_id}-{category_num}-{item_num}",
        "practiceNumber": practice_num,
        "practiceNameEn": en_name,
        "practiceName": zh_name,
        "gradeBand": grade_band,
        "gradeBandGoal": grade_goal,
        "categoryNumber": category_num,
        "itemNumber": item_num,
        "pointContent": content
    }

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    pdf_path = os.path.join(project_root, "01-documents", "Appendix F  Science and Engineering Practices.pdf")
    output_path = os.path.join(project_root, "web", "data", "sep_data.json")
    
    print("正在从 Appendix F 提取SEP数据...")
    seps = extract_seps_from_pdf(pdf_path)
    
    # 去重（基于 practice+grade+content）
    seen = set()
    unique_seps = []
    for s in seps:
        key = (s["practiceNumber"], s["gradeBand"], normalize_text(s["pointContent"])[:80])
        if key not in seen:
            seen.add(key)
            unique_seps.append(s)
    
    # 按 practiceNumber, gradeBand, categoryNumber, itemNumber 排序
    def sort_key(s):
        gorder = {"K-2": 0, "3-5": 1, "6-8": 2, "9-12": 3}
        return (s["practiceNumber"], gorder.get(s["gradeBand"], 99), s["categoryNumber"], s["itemNumber"])
    
    unique_seps.sort(key=sort_key)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"seps": unique_seps}, f, ensure_ascii=False, indent=2)
    
    print(f"提取完成，共 {len(unique_seps)} 条SEP")
    print(f"已保存到: {output_path}")
    
    # 统计
    for p in range(1, 9):
        count = sum(1 for s in unique_seps if s["practiceNumber"] == p)
        print(f"  Practice {p}: {count} 条")

if __name__ == "__main__":
    main()
