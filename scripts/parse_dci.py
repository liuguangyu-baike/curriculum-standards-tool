#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCI数据解析脚本
从DCI_NGSS_extracted.txt提取结构化数据，生成JSON格式
"""

import re
import json
from collections import defaultdict

# SEP映射（8个科学与工程实践）
SEP_MAPPING = {
    1: {"en": "Asking Questions and Defining Problems", "zh": "提出和定义问题"},
    2: {"en": "Developing and Using Models", "zh": "开发和使用模型"},
    3: {"en": "Planning and Carrying Out Investigations", "zh": "策划和实施调查"},
    4: {"en": "Analyzing and Interpreting Data", "zh": "分析和解释数据"},
    5: {"en": "Using Mathematics and Computational Thinking", "zh": "使用数学和计算思维"},
    6: {"en": "Constructing Explanations and Designing Solutions", "zh": "构建解释和设计解决方案"},
    7: {"en": "Engaging in Argument from Evidence", "zh": "依据证据进行辩论"},
    8: {"en": "Obtaining, Evaluating, and Communicating Information", "zh": "获取、评估和交流信息"}
}

# CCC映射（7个跨学科概念）
CCC_MAPPING = {
    1: {"en": "Patterns", "zh": "模式"},
    2: {"en": "Cause and Effect", "zh": "因果关系"},
    3: {"en": "Scale, Proportion, and Quantity", "zh": "尺度、比例和数量"},
    4: {"en": "Systems and System Models", "zh": "系统与系统模型"},
    5: {"en": "Energy and Matter", "zh": "能量与物质"},
    6: {"en": "Structure and Function", "zh": "结构与功能"},
    7: {"en": "Stability and Change", "zh": "稳定与变化"}
}

def extract_pe_code(text):
    """提取PE编码信息"""
    pattern = r'^([K1-5MSHS])-([A-Z]{2,3})(\d+)-(\d+)'
    match = re.match(pattern, text)
    if match:
        grade, domain, core_concept, standard = match.groups()
        return {
            "grade": grade,
            "domain": domain,
            "coreConceptNumber": int(core_concept),
            "standardNumber": int(standard)
        }
    return None

def extract_pe_references(text):
    """从文本中提取PE引用，如 (K-PS2-1),(K-PS2-2)"""
    pattern = r'\(([K1-5MSHS]-[A-Z]{2,3}\d+-\d+)\)'
    return re.findall(pattern, text)

def extract_clarification_and_boundary(text):
    """提取Clarification Statement和Assessment Boundary"""
    clarification = ""
    boundary = ""
    
    # 提取Clarification Statement
    cs_match = re.search(r'\[Clarification Statement:\s*(.+?)\]', text, re.DOTALL)
    if cs_match:
        clarification = cs_match.group(1).strip()
    
    # 提取Assessment Boundary
    ab_match = re.search(r'\[Assessment Boundary:\s*(.+?)\]', text, re.DOTALL)
    if ab_match:
        boundary = ab_match.group(1).strip()
    
    return clarification, boundary

def parse_file(file_path):
    """解析DCI文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 存储解析结果
    pes = []
    dcis = []
    seps = []
    cccs = []
    
    # 当前状态
    current_section = None  # 'pe', 'sep', 'dci', 'ccc'
    current_sep = None
    current_dci = None
    current_ccc = None
    current_core_concept_title = None
    current_pe_block = []  # 当前PE的多行内容
    
    # 要点计数器（用于生成唯一ID）
    dci_bullet_counter = defaultdict(lambda: defaultdict(int))
    sep_bullet_counter = defaultdict(lambda: defaultdict(int))
    ccc_bullet_counter = defaultdict(lambda: defaultdict(int))
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        original_line = lines[i]
        
        # 跳过空行和页眉页脚
        if not line or line.startswith('©') or 'of 103' in line or line.startswith('September') or line.startswith('DCI Arrangements'):
            i += 1
            continue
        
        # 跳过目录和介绍性文字
        if 'Table of Contents' in line or 'Elementary Introduction' in line or 'Storyline' in line:
            i += 1
            continue
        
        # 检测PE标题行（如 "K-PS2 Motion and Stability: Forces and Interactions"）
        pe_title_match = re.match(r'^([K1-5MSHS])-([A-Z]{2,3})(\d+)\s+(.+)$', line)
        if pe_title_match and 'Students who demonstrate' not in lines[i+1] if i+1 < len(lines) else True:
            grade, domain, core_concept_num, title = pe_title_match.groups()
            current_core_concept_title = title
            current_section = None
            i += 1
            continue
        
        # 检测PE条目开始（如 "K-PS2-1." 或 "MS-PS1-2."）
        pe_match = re.match(r'^([K1-5MSHS]-[A-Z]{2,3}\d+-\d+)\.?\s*(.*)$', line)
        if pe_match:
            pe_code = pe_match.group(1)
            pe_info = extract_pe_code(pe_code)
            if pe_info:
                pe_info["id"] = pe_code
                pe_info["coreConceptTitle"] = current_core_concept_title or ""
                
                # 收集PE的完整内容（可能跨多行）
                pe_content_lines = []
                if pe_match.group(2).strip():
                    pe_content_lines.append(pe_match.group(2))
                i += 1
                
                # 继续读取直到遇到下一个PE、章节标题或分隔线
                while i < len(lines):
                    next_line = lines[i].strip()
                    original_next = lines[i]
                    
                    # 检查是否是下一个PE（必须在一行开头）
                    if re.match(r'^[K1-5MSHS]-[A-Z]{2,3}\d+-\d+', next_line):
                        break
                    # 检查是否是章节分隔
                    if next_line.startswith('The performance expectations'):
                        break
                    if next_line.startswith('Science and Engineering Practices'):
                        break
                    if next_line.startswith('Disciplinary Core Ideas'):
                        break
                    if next_line.startswith('Crosscutting Concepts'):
                        break
                    # 检查是否是下一个主题（如 "K-PS3 Energy"）
                    if re.match(r'^[K1-5MSHS]-[A-Z]{2,3}\d+\s+', next_line):
                        break
                    # 检查是否是分隔线
                    if next_line.startswith('---') or next_line.startswith('==='):
                        break
                    # 如果下一行是空行且我们已经有一些内容，可能是PE结束
                    if not next_line and pe_content_lines:
                        # 检查再下一行是否是PE或章节标题
                        if i + 1 < len(lines):
                            next_next = lines[i + 1].strip()
                            if re.match(r'^[K1-5MSHS]-[A-Z]{2,3}\d+', next_next) or \
                               next_next.startswith('The performance expectations') or \
                               next_next.startswith('Science and Engineering Practices'):
                                break
                    
                    pe_content_lines.append(original_next)
                    i += 1
                
                # 合并内容并提取信息
                full_content = ' '.join(pe_content_lines)
                clarification, boundary = extract_clarification_and_boundary(full_content)
                
                # 清理内容（移除Clarification和Boundary标记）
                clean_content = full_content
                clean_content = re.sub(r'\[Clarification Statement:.*?\]', '', clean_content, flags=re.DOTALL)
                clean_content = re.sub(r'\[Assessment Boundary:.*?\]', '', clean_content, flags=re.DOTALL)
                clean_content = clean_content.strip()
                
                pe_info["content"] = clean_content
                pe_info["clarificationStatement"] = clarification
                pe_info["assessmentBoundary"] = boundary
                
                pes.append(pe_info)
                continue
        
        # 检测章节标题
        if line == "Science and Engineering Practices":
            current_section = 'sep'
            current_sep = None
            i += 1
            continue
        elif line == "Disciplinary Core Ideas":
            current_section = 'dci'
            current_dci = None
            i += 1
            continue
        elif line == "Crosscutting Concepts":
            current_section = 'ccc'
            current_ccc = None
            i += 1
            continue
        
        # 解析SEP
        if current_section == 'sep':
            # 检测SEP标题（完全匹配SEP英文名称的行）
            for sep_num, sep_info in SEP_MAPPING.items():
                if sep_info["en"] == line:
                    current_sep = sep_num
                    i += 1
                    # 跳过描述性文字，直到遇到要点
                    while i < len(lines):
                        next_line = lines[i].strip()
                        if next_line.startswith('▪'):
                            i -= 1  # 回退一行，让要点解析逻辑处理
                            break
                        if next_line in [info["en"] for info in SEP_MAPPING.values()]:
                            i -= 1
                            break
                        i += 1
                    continue
            
            # 检测SEP要点（以▪开头）
            if line.startswith('▪') and current_sep:
                # 收集可能跨多行的要点内容
                bullet_lines = [line[1:].strip()]
                j = i + 1
                while j < len(lines):
                    next_bullet_line = lines[j].strip()
                    # 如果下一行也是要点，停止收集
                    if next_bullet_line.startswith('▪'):
                        break
                    # 如果下一行是新的SEP标题，停止
                    if next_bullet_line in [info["en"] for info in SEP_MAPPING.values()]:
                        break
                    # 如果下一行是章节标题，停止
                    if next_bullet_line in ["Disciplinary Core Ideas", "Crosscutting Concepts"]:
                        break
                    # 如果遇到分隔线，停止
                    if next_bullet_line.startswith('---') or next_bullet_line.startswith('==='):
                        break
                    # 如果下一行包含PE引用，继续收集
                    if re.search(r'\([K1-5MSHS]-[A-Z]{2,3}\d+-\d+\)', next_bullet_line):
                        bullet_lines.append(next_bullet_line)
                        j += 1
                        break  # PE引用通常在要点末尾
                    # 如果下一行不为空，继续收集
                    if next_bullet_line:
                        bullet_lines.append(next_bullet_line)
                        j += 1
                    else:
                        break
                
                bullet_text = ' '.join(bullet_lines)
                pe_refs = extract_pe_references(bullet_text)
                
                if pe_refs:
                    # 使用内容作为key来去重和计数
                    content_key = bullet_text.split('(')[0].strip()
                    sep_bullet_counter[current_sep][content_key] += 1
                    bullet_num = sep_bullet_counter[current_sep][content_key]
                    
                    sep_id = f"SEP-{current_sep}-{bullet_num}"
                    grades = list(set([extract_pe_code(pe)["grade"] for pe in pe_refs if extract_pe_code(pe)]))
                    
                    sep_entry = {
                        "id": sep_id,
                        "sepNumber": current_sep,
                        "sepTitle": SEP_MAPPING[current_sep]["zh"],
                        "sepEnglishTitle": SEP_MAPPING[current_sep]["en"],
                        "bulletPointNumber": bullet_num,
                        "content": content_key,
                        "relatedPEs": pe_refs,
                        "grades": grades
                    }
                    seps.append(sep_entry)
                
                i = j - 1
        
        # 解析DCI
        elif current_section == 'dci':
            # 检测DCI标题（如 "PS2.A: Forces and Motion"）
            dci_match = re.match(r'^([A-Z]{2,3})(\d+)\.([A-Z]):\s*(.+)$', line)
            if dci_match:
                domain, core_concept, sub_concept, title = dci_match.groups()
                current_dci = {
                    "domain": domain,
                    "coreConceptNumber": int(core_concept),
                    "subConceptCode": sub_concept,
                    "subConceptTitle": title
                }
                i += 1
                continue
            
            # 检测DCI要点（以▪开头）
            if line.startswith('▪') and current_dci:
                # 收集可能跨多行的要点内容
                bullet_lines = [line[1:].strip()]
                j = i + 1
                while j < len(lines):
                    next_bullet_line = lines[j].strip()
                    if next_bullet_line.startswith('▪') or re.match(r'^[A-Z]{2,3}\d+\.', next_bullet_line):
                        break
                    if not next_bullet_line or next_bullet_line.startswith('---'):
                        break
                    bullet_lines.append(next_bullet_line)
                    j += 1
                
                bullet_text = ' '.join(bullet_lines)
                pe_refs = extract_pe_references(bullet_text)
                
                if pe_refs or bullet_text.strip():  # 有些DCI要点可能没有PE引用
                    dci_key = f"{current_dci['domain']}{current_dci['coreConceptNumber']}.{current_dci['subConceptCode']}"
                    content_key = bullet_text.split('(')[0].strip()
                    dci_bullet_counter[dci_key][content_key] += 1
                    bullet_num = dci_bullet_counter[dci_key][content_key]
                    
                    dci_id = f"{dci_key}-{bullet_num}"
                    grades = list(set([extract_pe_code(pe)["grade"] for pe in pe_refs if extract_pe_code(pe)]))
                    
                    dci_entry = {
                        "id": dci_id,
                        "domain": current_dci["domain"],
                        "coreConceptNumber": current_dci["coreConceptNumber"],
                        "coreConceptTitle": current_core_concept_title or "",
                        "subConceptCode": current_dci["subConceptCode"],
                        "subConceptTitle": current_dci["subConceptTitle"],
                        "bulletPointNumber": bullet_num,
                        "content": content_key,
                        "relatedPEs": pe_refs,
                        "grades": grades
                    }
                    dcis.append(dci_entry)
                
                i = j - 1
        
        # 解析CCC
        elif current_section == 'ccc':
            # 检测CCC标题
            for ccc_num, ccc_info in CCC_MAPPING.items():
                if ccc_info["en"] == line:
                    current_ccc = ccc_num
                    i += 1
                    continue
            
            # 检测CCC要点（以▪开头）
            if line.startswith('▪') and current_ccc:
                # 收集可能跨多行的要点内容
                bullet_lines = [line[1:].strip()]
                j = i + 1
                while j < len(lines):
                    next_bullet_line = lines[j].strip()
                    if next_bullet_line.startswith('▪') or next_bullet_line in [info["en"] for info in CCC_MAPPING.values()]:
                        break
                    if not next_bullet_line or next_bullet_line.startswith('---'):
                        break
                    bullet_lines.append(next_bullet_line)
                    j += 1
                
                bullet_text = ' '.join(bullet_lines)
                pe_refs = extract_pe_references(bullet_text)
                
                if pe_refs:
                    content_key = bullet_text.split('(')[0].strip()
                    ccc_bullet_counter[current_ccc][content_key] += 1
                    bullet_num = ccc_bullet_counter[current_ccc][content_key]
                    
                    ccc_id = f"CCC-{current_ccc}-{bullet_num}"
                    grades = list(set([extract_pe_code(pe)["grade"] for pe in pe_refs if extract_pe_code(pe)]))
                    
                    ccc_entry = {
                        "id": ccc_id,
                        "cccNumber": current_ccc,
                        "cccTitle": CCC_MAPPING[current_ccc]["zh"],
                        "cccEnglishTitle": CCC_MAPPING[current_ccc]["en"],
                        "bulletPointNumber": bullet_num,
                        "content": content_key,
                        "relatedPEs": pe_refs,
                        "grades": grades
                    }
                    cccs.append(ccc_entry)
                
                i = j - 1
        
        i += 1
    
    return {
        "pes": pes,
        "dcis": dcis,
        "seps": seps,
        "cccs": cccs
    }

def main():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    output_file = os.path.join(project_root, "web", "data", "dci_data.json")
    
    print("开始解析DCI文件...")
    data = parse_file(input_file)
    
    print(f"解析完成:")
    print(f"  PE数量: {len(data['pes'])}")
    print(f"  DCI数量: {len(data['dcis'])}")
    print(f"  SEP数量: {len(data['seps'])}")
    print(f"  CCC数量: {len(data['cccs'])}")
    
    # 保存JSON文件
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
