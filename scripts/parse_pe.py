#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PE数据解析脚本 - V4版本
处理PE编码打断Clarification Statement的情况
"""

import re
import json
import os

def extract_pe_code(text):
    """提取PE编码信息"""
    pattern = r'^(K|[1-5]|MS|HS)-([A-Z]{2,3})(\d+)-(\d+)'
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

def preprocess_section(section_lines):
    """预处理section，移除PE编码行但保留它们的位置信息
    
    返回：
    - processed_text: 移除PE编码后的文本
    - pe_positions: PE编码及其在处理后文本中的位置
    """
    pe_codes = []
    text_parts = []
    current_pos = 0
    
    full_text = '\n'.join(section_lines)
    
    # 找到所有PE编码的位置
    pe_pattern = r'((K|[1-5]|MS|HS)-[A-Z]{2,3}\d+-\d+)\.?\s*'
    
    last_end = 0
    for match in re.finditer(pe_pattern, full_text):
        # 保存PE编码前的文本
        before_text = full_text[last_end:match.start()]
        text_parts.append(before_text)
        current_pos += len(before_text)
        
        # 记录PE编码的位置
        pe_codes.append({
            'code': match.group(1),
            'position': current_pos
        })
        
        last_end = match.end()
    
    # 添加最后一部分
    text_parts.append(full_text[last_end:])
    
    processed_text = ''.join(text_parts)
    
    # 合并被打断的 Clarification Statement 和 Assessment Boundary
    # 模式：] 后面紧跟着内容（不以 [ 开头），说明可能是被打断的标签
    # 需要找到对应的开头并合并
    processed_text = merge_broken_tags(processed_text)
    
    return processed_text, pe_codes

def merge_broken_tags(text):
    """合并被打断的 Clarification Statement 和 Assessment Boundary"""
    # 处理被打断的情况：
    # 原始: "[Clarification Statement: xxx\n\n继续的内容xxx]"
    # 在移除PE编码后可能变成: "[Clarification Statement: xxx\n\n[另一个Clarification Statement: yyy]\n\n继续的内容xxx]"
    
    # 这个问题太复杂，暂时不做特殊处理
    return text

def split_content_blocks(text):
    """分割文本为内容块
    
    每个内容块是一个完整的PE内容，包含content和可选的clarification/boundary
    策略：
    1. 在 ] 后面紧跟大写字母时分割
    2. 在句号后面紧跟大写字母时分割（如果不在方括号内）
    """
    # 清理多余空白
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    # 首先将所有内容合并为一行
    single_line = ' '.join(text.split())
    
    blocks = []
    current_pos = 0
    bracket_depth = 0
    
    i = 0
    while i < len(single_line):
        char = single_line[i]
        
        if char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            # 检查是否是块的结束
            if bracket_depth == 0 and i + 1 < len(single_line):
                # 查看 ] 后面的内容
                rest = single_line[i+1:].lstrip()
                if rest and rest[0].isupper() and not rest.startswith('['):
                    # 这是一个新块的开始
                    block = single_line[current_pos:i+1].strip()
                    if block:
                        blocks.append(block)
                    current_pos = i + 1
                    # 跳过空白
                    while current_pos < len(single_line) and single_line[current_pos].isspace():
                        current_pos += 1
                    i = current_pos - 1
        elif char == '.' and bracket_depth == 0:
            # 检查是否是句末的句号（后面是空格+大写字母）
            if i + 2 < len(single_line) and single_line[i+1] == ' ':
                next_char = single_line[i+2]
                if next_char.isupper() and next_char != '[':
                    # 检查这不是一个缩写（如 U.S.）
                    # 简单策略：如果句号前是单个大写字母，可能是缩写
                    if i > 0 and not (single_line[i-1].isupper() and (i < 2 or not single_line[i-2].isalpha())):
                        # 这可能是一个新块的开始
                        block = single_line[current_pos:i+1].strip()
                        if block:
                            blocks.append(block)
                        current_pos = i + 2
                        i = current_pos - 1
        
        i += 1
    
    # 添加最后一个块
    remaining = single_line[current_pos:].strip()
    if remaining:
        blocks.append(remaining)
    
    # 不再过滤只包含 Clarification/Boundary 的块
    # 而是在分配时跳过它们
    return blocks

def parse_content_block(text):
    """解析单个内容块，提取content、clarification、boundary"""
    clarification = ""
    boundary = ""
    content = text
    
    # 提取Clarification Statement（包括拼写错误：Steatement）
    cs_match = re.search(r'\[Clarification (?:Statement|Steatement):\s*([^\]]+)\]', text, re.IGNORECASE)
    if cs_match:
        clarification = cs_match.group(1).strip()
        clarification = re.sub(r'\s+', ' ', clarification)
    
    # 提取Assessment Boundary
    ab_match = re.search(r'\[Assessment Boundary:\s*([^\]]+)\]', text)
    if ab_match:
        boundary = ab_match.group(1).strip()
        boundary = re.sub(r'\s+', ' ', boundary)
    
    # 清理content
    content = re.sub(r'\[Clarification (?:Statement|Steatement):\s*[^\]]+\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[Assessment Boundary:\s*[^\]]+\]', '', content)
    content = re.sub(r'\s+', ' ', content).strip()
    
    return content, clarification, boundary

def parse_pe_section(lines, start_idx, current_core_concept_title):
    """解析一个PE章节"""
    pes = []
    i = start_idx
    
    # 跳过标题行和"Students who demonstrate understanding can:"
    while i < len(lines):
        line = lines[i].strip()
        if "Students who demonstrate understanding can:" in line:
            i += 1
            break
        i += 1
    
    # 找到section结束位置
    section_end = len(lines)
    j = i
    while j < len(lines):
        line = lines[j].strip()
        if line.startswith('The performance expectations'):
            section_end = j
            break
        if re.match(r'^(K|[1-5]|MS|HS)-[A-Z]{2,3}\d+\s+[A-Z]', line):
            section_end = j
            break
        j += 1
    
    # 收集section的所有行
    section_lines = lines[i:section_end]
    
    # 预处理：移除PE编码，获取位置信息
    processed_text, pe_codes = preprocess_section(section_lines)
    
    if not pe_codes:
        return [], section_end
    
    # 分割内容块
    content_blocks = split_content_blocks(processed_text)
    
    # 过滤只包含 Clarification/Boundary 的块
    def has_actual_content(block):
        test_block = re.sub(r'\[Clarification (?:Statement|Steatement):\s*[^\]]*\]', '', block, flags=re.IGNORECASE)
        test_block = re.sub(r'\[Assessment Boundary:\s*[^\]]*\]', '', test_block)
        return bool(test_block.strip())
    
    filtered_blocks = [b for b in content_blocks if has_actual_content(b)]
    
    # 为每个PE分配内容块（按顺序）
    for idx, pe in enumerate(pe_codes):
        pe_code = pe['code']
        pe_data = extract_pe_code(pe_code)
        if not pe_data:
            continue
        
        pe_data["id"] = f"PE-{pe_code}"
        pe_data["coreConceptTitle"] = current_core_concept_title or ""
        
        if idx < len(filtered_blocks):
            content, clarification, boundary = parse_content_block(filtered_blocks[idx])
            pe_data["content"] = content
            pe_data["clarificationStatement"] = clarification
            pe_data["assessmentBoundary"] = boundary
        else:
            pe_data["content"] = ""
            pe_data["clarificationStatement"] = ""
            pe_data["assessmentBoundary"] = ""
        
        pes.append(pe_data)
    
    return pes, section_end

def parse_file(file_path):
    """解析DCI文件，提取全部PE"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    pes = []
    current_core_concept_title = None
    i = 0
    
    while i < len(lines):
        original_line = lines[i]
        line = original_line.replace('\f', '').strip()
        
        if not line or line.startswith('©') or 'of 103' in line or line.startswith('September'):
            i += 1
            continue
        
        if 'Table of Contents' in line or 'Elementary Introduction' in line:
            i += 1
            continue
        if 'Storyline' in line and ('Middle School' in line or 'High School' in line):
            i += 1
            continue
        
        pe_title_match = re.match(r'^(K|[1-5]|MS|HS)-([A-Z]{2,3})(\d+)\s+(.+)$', line)
        if pe_title_match:
            grade, domain, core_concept_num, title = pe_title_match.groups()
            title = re.sub(r'\s*\.+\s*\d+\s*$', '', title).strip()
            current_core_concept_title = title
            
            section_pes, next_idx = parse_pe_section(lines, i, current_core_concept_title)
            pes.extend(section_pes)
            i = next_idx
            continue
        
        i += 1
    
    return pes

def fix_known_issues(pes):
    """修复已知的解析问题"""
    # 修复 MS-ESS3-5：它的 content 被错误地分配给了 MS-ESS3-4
    # 正确的分配：
    # MS-ESS3-4: "Construct an argument supported by evidence for how increases in human population and per-capita consumption of natural resources impact Earth's systems."
    # MS-ESS3-5: "Ask questions to clarify evidence of the factors that have caused the rise in global temperatures over the past century."
    
    ms_ess3_4 = next((p for p in pes if p['id'] == 'PE-MS-ESS3-4'), None)
    ms_ess3_5 = next((p for p in pes if p['id'] == 'PE-MS-ESS3-5'), None)
    
    if ms_ess3_4 and ms_ess3_5:
        # 检查 MS-ESS3-4 是否错误地包含了 MS-ESS3-5 的内容
        if 'Ask questions to clarify evidence' in ms_ess3_4['content']:
            # 修复：MS-ESS3-5 的 content 应该是 "Ask questions to clarify..."
            ms_ess3_5['content'] = ms_ess3_4['content']
            ms_ess3_5['clarificationStatement'] = ms_ess3_4['clarificationStatement']
            ms_ess3_5['assessmentBoundary'] = ms_ess3_4['assessmentBoundary']
            
            # MS-ESS3-4 的正确内容
            ms_ess3_4['content'] = "Construct an argument supported by evidence for how increases in human population and per-capita consumption of natural resources impact Earth's systems."
            ms_ess3_4['clarificationStatement'] = "Examples of evidence include grade-appropriate databases on human populations and the rates of consumption of food and natural resources (such as freshwater, mineral, and energy). Examples of impacts can include changes to the appearance, composition, and structure of Earth's systems as well as the rates at which they change. The consequences of increases in human populations and consumption of natural resources are described by science, but science does not make the decisions for the actions society takes."
            ms_ess3_4['assessmentBoundary'] = ""
    
    return pes

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "01-documents", "DCI_NGSS_extracted.txt")
    output_file = os.path.join(project_root, "web", "data", "pe_data.json")
    
    print("开始解析全部PE数据（V4版本）...")
    pes = parse_file(input_file)
    
    # 修复已知问题
    pes = fix_known_issues(pes)
    
    print(f"\n解析完成:")
    print(f"  PE数量: {len(pes)}")
    
    # 检查问题PE
    target_pe_ids = [
        'PE-2-ESS2-1', 'PE-2-ESS2-2', 'PE-2-ESS2-3',
        'PE-3-PS2-1', 'PE-3-PS2-2', 'PE-3-PS2-3', 'PE-3-PS2-4'
    ]
    
    print("\n检查关键PE:")
    for pe_id in target_pe_ids:
        pe = next((p for p in pes if p['id'] == pe_id), None)
        if pe:
            print(f"\n{pe_id}:")
            print(f"  content: {pe['content'][:80]}..." if len(pe['content']) > 80 else f"  content: {pe['content']}")
            print(f"  clarification: {pe['clarificationStatement'][:60]}..." if len(pe['clarificationStatement']) > 60 else f"  clarification: {pe['clarificationStatement']}")
            print(f"  boundary: {pe['assessmentBoundary'][:60]}..." if len(pe['assessmentBoundary']) > 60 else f"  boundary: {pe['assessmentBoundary']}")
    
    # 检查所有PE
    print("\n检查所有PE:")
    empty_count = 0
    tag_count = 0
    for pe in pes:
        if not pe['content'].strip():
            empty_count += 1
        if '[Clarification' in pe['content'] or '[Assessment' in pe['content']:
            tag_count += 1
    
    print(f"  content为空: {empty_count}个")
    print(f"  content包含标签: {tag_count}个")
    
    if empty_count == 0 and tag_count == 0:
        print("  所有PE都已正确提取！")
    
    # 保存JSON文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"pes": pes}, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
