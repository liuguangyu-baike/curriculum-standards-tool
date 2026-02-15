#!/usr/bin/env python3
"""
第1步：从JSON数据中提取各级别对应学段的课标内容，按领域和核心概念分组输出汇总文档。

级别对应关系：
- L1 (G5-G6): 中国UP学段 / NGSS 3-5年级
- L2 (G7-G8): 中国MS学段 / NGSS MS
- L3 (G9-G10): 中国MS学段(部分) + 高中 / NGSS HS

排除 ETS(工程技术) 领域。
"""

import json
import os
from collections import defaultdict

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "web", "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "主题图谱")

CN_FILE = os.path.join(DATA_DIR, "cn_compulsory_science_knowledge.json")
DCI_FILE = os.path.join(DATA_DIR, "dci_data.json")

# 级别→学段映射
LEVEL_CN_GRADES = {
    "L1": ["UP"],           # 5-6年级
    "L2": ["MS"],           # 初中(7-9年级)
    "L3": ["MS"],           # 初中(部分，与L2有重叠，后续人工区分) + 高中(PDF补充)
}

# NGSS grade到级别的映射
# L1: 3-5年级 (grade "3", "5")
# L2: MS
# L3: HS
def ngss_grade_to_level(grade):
    if grade in ("K", "2"):
        return None  # 太低，不纳入
    elif grade in ("3", "5"):
        return "L1"
    elif grade == "MS":
        return "L2"
    elif grade == "HS":
        return "L3"
    else:
        return None

# 排除的领域
EXCLUDED_DOMAINS_NGSS = {"ETS"}


def load_cn_data():
    with open(CN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cnCompulsoryScienceKnowledge"]


def load_dci_data():
    with open(DCI_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["dcis"]


def extract_cn_by_level(items):
    """提取中国课标数据，按级别→领域→核心概念→主题分组"""
    # L1 = UP, L2+L3 = MS (L2和L3共享MS，输出时标注)
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    for item in items:
        grade_band = item["gradeBand"]
        domain = item["domain"]
        domain_code = item["domainCode"]
        core_concept = item["coreConcept"]
        topic = item["topic"]
        requirement = item["requirement"]
        req_id = item["id"]

        if grade_band == "HP":  # HP = Higher Primary = 5-6年级
            level = "L1"
        elif grade_band == "MS":
            level = "L2/L3"  # MS学段同时对应L2和L3，后续根据内容深度人工分配
        elif grade_band in ("LP", "MP"):
            continue  # 低年级不纳入
        else:
            continue

        result[level][f"{domain_code} {domain}"][core_concept][topic].append({
            "id": req_id,
            "requirement": requirement,
        })

    return result


def extract_dci_by_level(items):
    """提取NGSS DCI数据，按级别→领域→核心概念→子概念分组"""
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    for item in items:
        domain = item["domain"]
        if domain in EXCLUDED_DOMAINS_NGSS:
            continue

        grade = item["grade"]
        level = ngss_grade_to_level(grade)
        if level is None:
            continue

        core = f"{domain}{item['coreConceptNumber']} {item['coreConceptTitleZH']}（{item['coreConceptTitle']}）"
        sub = f"{item['subConceptLetter']}. {item['subConceptTitleZH']}（{item['subConceptTitle']}）"
        content_zh = item.get("contentZH", "")
        content_en = item.get("content", "")

        result[level][domain][core][sub].append({
            "id": item["id"],
            "grade": grade,
            "content_zh": content_zh,
            "content": content_en,
        })

    return result


def format_cn_output(cn_data):
    """格式化中国课标数据为markdown"""
    lines = []
    lines.append("# 中国义务教育科学课标 - 按级别汇总\n")

    for level in sorted(cn_data.keys()):
        lines.append(f"\n## {level}\n")
        domains = cn_data[level]
        for domain_key in sorted(domains.keys()):
            lines.append(f"\n### {domain_key}\n")
            concepts = domains[domain_key]
            for concept in sorted(concepts.keys()):
                lines.append(f"\n#### {concept}\n")
                topics = concepts[concept]
                for topic in sorted(topics.keys()):
                    lines.append(f"\n**{topic}**\n")
                    for req in topics[topic]:
                        lines.append(f"- `{req['id']}` {req['requirement']}")
    return "\n".join(lines)


def format_dci_output(dci_data):
    """格式化NGSS DCI数据为markdown"""
    lines = []
    lines.append("# NGSS DCI - 按级别汇总\n")

    domain_names = {
        "PS": "PS 物质科学",
        "LS": "LS 生命科学",
        "ESS": "ESS 地球与空间科学",
    }

    for level in ["L1", "L2", "L3"]:
        if level not in dci_data:
            continue
        lines.append(f"\n## {level}\n")
        domains = dci_data[level]
        for domain in ["PS", "LS", "ESS"]:
            if domain not in domains:
                continue
            lines.append(f"\n### {domain_names.get(domain, domain)}\n")
            concepts = domains[domain]
            for concept in sorted(concepts.keys()):
                lines.append(f"\n#### {concept}\n")
                subs = concepts[concept]
                for sub in sorted(subs.keys()):
                    lines.append(f"\n**{sub}**\n")
                    for item in subs[sub]:
                        lines.append(f"- `{item['id']}` [{item['grade']}] {item['content_zh']}")
    return "\n".join(lines)


def generate_statistics(cn_data, dci_data):
    """生成统计信息"""
    lines = []
    lines.append("# 课标数据统计\n")

    # 中国课标统计
    lines.append("## 中国义务教育科学课标\n")
    for level in sorted(cn_data.keys()):
        total = 0
        domain_counts = {}
        for domain_key in cn_data[level]:
            count = sum(
                len(reqs)
                for topics in cn_data[level][domain_key].values()
                for reqs in topics.values()
            )
            domain_counts[domain_key] = count
            total += count
        lines.append(f"### {level} (共{total}条)\n")
        for d, c in sorted(domain_counts.items()):
            lines.append(f"- {d}: {c}条")
        lines.append("")

    # NGSS统计
    lines.append("\n## NGSS DCI\n")
    domain_names = {"PS": "PS 物质科学", "LS": "LS 生命科学", "ESS": "ESS 地球与空间科学"}
    for level in ["L1", "L2", "L3"]:
        if level not in dci_data:
            continue
        total = 0
        domain_counts = {}
        for domain in ["PS", "LS", "ESS"]:
            if domain not in dci_data[level]:
                continue
            count = sum(
                len(items)
                for subs in dci_data[level][domain].values()
                for items in subs.values()
            )
            domain_counts[domain_names[domain]] = count
            total += count
        lines.append(f"### {level} (共{total}条)\n")
        for d, c in sorted(domain_counts.items()):
            lines.append(f"- {d}: {c}条")
        lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 加载数据
    cn_items = load_cn_data()
    dci_items = load_dci_data()

    # 提取并分组
    cn_data = extract_cn_by_level(cn_items)
    dci_data = extract_dci_by_level(dci_items)

    # 生成统计
    stats = generate_statistics(cn_data, dci_data)

    # 生成详细输出
    cn_output = format_cn_output(cn_data)
    dci_output = format_dci_output(dci_data)

    # 写入文件
    output_path = os.path.join(OUTPUT_DIR, "00-课标分析汇总.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 课标分析汇总\n\n")
        f.write("> 自动生成，用于支撑9+主题图谱设计\n\n")
        f.write("---\n\n")
        f.write(stats)
        f.write("\n\n---\n\n")
        f.write(cn_output)
        f.write("\n\n---\n\n")
        f.write(dci_output)

    print(f"输出完成: {output_path}")

    # 打印统计摘要
    print("\n" + stats)


if __name__ == "__main__":
    main()
