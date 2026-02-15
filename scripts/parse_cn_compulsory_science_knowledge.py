#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 xlsx 中的「中国 | 义务教育 | 科学」sheet（4-322行，“科学知识/观念”部分）
转换为结构化 JSON，输出到 web/data/ 目录，供后续检索使用。

注意：该工作簿包含不规范的样式 XML，openpyxl 可能无法读取。
本脚本采用“把 xlsx 当作 zip + 解析 worksheet xml”的方式，仅提取需要的单元格值，
从而绕过样式解析问题。
"""

from __future__ import annotations

import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, Tuple


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


SHEET_NAME = "中国 | 义务教育 | 科学"
ROW_START = 4
ROW_END = 322

# 领域映射（B列）
DOMAIN_CODE_MAP = {
    "物质科学": "PS",
    "生命科学": "LS",
    "地球与空间科学": "ESS",
}

# 年级段列：G-J（勾选）
GRADE_BAND_COLUMNS = {
    "G": ("LP", ["1", "2"]),  # 1-2
    "H": ("MP", ["3", "4"]),  # 3-4
    "I": ("HP", ["5", "6"]),  # 5-6
    "J": ("MS", ["7", "8", "9"]),  # 7-9
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def _is_checked(v: Any) -> bool:
    """
    兼容常见“勾选/是/TRUE/1/√/✓”等形式。
    注意：我们读取的是 worksheet xml 的缓存值，通常会是 bool 或字符串/数字。
    """
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    s = _as_str(v)
    if not s:
        return False
    s_upper = s.upper()
    return s_upper in {"TRUE", "T", "Y", "YES", "1", "是", "对", "√", "✓", "☑", "✔"}


def _col_letter(cell_ref: str) -> str:
    i = 0
    while i < len(cell_ref) and cell_ref[i].isalpha():
        i += 1
    return cell_ref[:i]


def _row_num(cell_ref: str) -> int:
    i = 0
    while i < len(cell_ref) and cell_ref[i].isalpha():
        i += 1
    return int(cell_ref[i:])


def _read_shared_strings(z: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
    shared: List[str] = []
    for si in sst.findall("main:si", NS):
        # 支持富文本：多个 <r><t>
        ts = [t.text or "" for t in si.findall(".//main:t", NS)]
        shared.append("".join(ts))
    return shared


def _workbook_sheet_path(z: zipfile.ZipFile, sheet_name: str) -> str:
    """
    从 workbook.xml + workbook.xml.rels 找到指定 sheet 的 worksheets/sheetN.xml 路径
    """
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rid: Optional[str] = None
    for sh in wb.findall("main:sheets/main:sheet", NS):
        if sh.attrib.get("name") == sheet_name:
            rid = sh.attrib.get(f"{{{NS['rel']}}}id")
            break
    if not rid:
        names = [sh.attrib.get("name", "") for sh in wb.findall("main:sheets/main:sheet", NS)]
        raise ValueError(f"未找到sheet：{sheet_name}；当前sheet列表：{names}")

    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid_to_target: Dict[str, str] = {}
    for r in rels.findall("pr:Relationship", NS):
        rid_to_target[r.attrib["Id"]] = r.attrib["Target"]

    target = rid_to_target.get(rid)
    if not target:
        raise ValueError(f"未找到sheet关系映射：{rid}")
    return str(PurePosixPath("xl") / target)


def _cell_value(cell: ET.Element, shared_strings: List[str]) -> Any:
    t = cell.attrib.get("t")
    v = cell.find("main:v", NS)
    if t == "s":
        if v is None or v.text is None:
            return None
        idx = int(v.text)
        return shared_strings[idx] if 0 <= idx < len(shared_strings) else None
    if t == "b":
        if v is None or v.text is None:
            return None
        return v.text == "1"
    if t == "inlineStr":
        ts = [t_el.text or "" for t_el in cell.findall(".//main:t", NS)]
        return "".join(ts)
    # default / number / cached result
    if v is None or v.text is None:
        return None
    return v.text


def _extract_topic_number(topic: str) -> Optional[str]:
    m = re.match(r"^(\d+(?:\.\d+)*)", topic.strip())
    return m.group(1) if m else None


def _extract_requirement_number(req: str) -> Optional[str]:
    m = re.match(r"^(\d+)", req.strip())
    return m.group(1) if m else None


def _domain_code(domain: str) -> Optional[str]:
    d = domain.strip()
    if not d:
        return None
    # 精确匹配优先
    if d in DOMAIN_CODE_MAP:
        return DOMAIN_CODE_MAP[d]
    # 容错：包含式
    if "物质" in d:
        return "PS"
    if "生命" in d:
        return "LS"
    if "地球" in d or "空间" in d:
        return "ESS"
    return None


@dataclass
class WarningItem:
    excelRow: int
    type: str
    message: str


def parse() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    xlsx_path = os.path.join(project_root, "01-documents", "国内外课标信息汇总.xlsx")

    items: List[Dict[str, Any]] = []
    warnings: List[WarningItem] = []
    multi_grade_rows: List[Dict[str, Any]] = []

    # 统计
    rows_scanned = 0
    requirement_rows = 0

    with zipfile.ZipFile(xlsx_path) as z:
        shared_strings = _read_shared_strings(z)
        sheet_path = _workbook_sheet_path(z, SHEET_NAME)
        sheet_xml = ET.fromstring(z.read(sheet_path))

        # 上一次非空值（用于处理合并单元格/空白下填）
        last_domain = ""
        last_core_concept = ""
        last_topic = ""

        # 仅关注 sheetData/row
        for row in sheet_xml.findall(".//main:sheetData/main:row", NS):
            r_attr = row.attrib.get("r")
            if not r_attr:
                continue
            r = int(r_attr)
            if r < ROW_START or r > ROW_END:
                continue

            rows_scanned += 1

            # 收集该行需要的列值
            row_cells: Dict[str, Any] = {}
            for c in row.findall("main:c", NS):
                ref = c.attrib.get("r")
                if not ref:
                    continue
                col = _col_letter(ref)
                if col in {"B", "C", "D", "E", "G", "H", "I", "J"}:
                    row_cells[col] = _cell_value(c, shared_strings)

            b = _as_str(row_cells.get("B"))
            c_val = _as_str(row_cells.get("C"))
            d = _as_str(row_cells.get("D"))
            e = _as_str(row_cells.get("E"))

            if b:
                last_domain = b
            if c_val:
                last_core_concept = c_val
            if d:
                last_topic = d

            # E列为空则不生成条目（每条要求一个条目）
            if not e:
                continue

            requirement_rows += 1

            domain = last_domain
            core_concept = last_core_concept
            topic = last_topic
            domain_code = _domain_code(domain or "")

            if not domain:
                warnings.append(WarningItem(r, "missing_domain", "B列为空且无法从上方填充"))
            if not core_concept:
                warnings.append(WarningItem(r, "missing_core_concept", "C列为空且无法从上方填充"))
            if not topic:
                warnings.append(WarningItem(r, "missing_topic", "D列为空且无法从上方填充"))
            if not domain_code:
                warnings.append(WarningItem(r, "unknown_domain_code", f"无法映射学科领域编号：{domain!r}"))

            topic_number = _extract_topic_number(topic) if topic else None
            req_number = _extract_requirement_number(e)

            if not topic_number:
                warnings.append(WarningItem(r, "missing_topic_number", f"无法从D列提取具体内容序号：{topic!r}"))
            if not req_number:
                warnings.append(WarningItem(r, "missing_requirement_number", f"无法从E列提取内容要求序号：{e!r}"))

            # 年级段勾选：G-J
            checked_bands: List[Tuple[str, List[str]]] = []
            for col, (band, grades) in GRADE_BAND_COLUMNS.items():
                if _is_checked(row_cells.get(col)):
                    checked_bands.append((band, grades))

            if len(checked_bands) > 1:
                # 按“方案A”拆分，同时记录供人工确认
                # ids 在生成后补上
                pass

            if not checked_bands:
                warnings.append(WarningItem(r, "missing_grade_band", "G-J列未检测到任何勾选"))
                checked_bands = [("UNKNOWN", [])]

            generated_ids: List[str] = []

            for band, grades in checked_bands:
                dc = domain_code or "UNK"
                tn = topic_number or "UNK"
                rn = req_number or "UNK"
                item_id = f"{dc}-{tn}-{rn}-{band}"
                generated_ids.append(item_id)

                items.append(
                    {
                        "id": item_id,
                        "domain": domain,
                        "domainCode": dc,
                        "coreConcept": core_concept,
                        "topic": topic,
                        "topicNumber": tn,
                        "requirement": e,
                        "requirementNumber": rn,
                        "gradeBand": band,
                        "grades": grades,
                        "source": {"sheet": SHEET_NAME, "excelRow": r},
                    }
                )

            if len(checked_bands) > 1:
                multi_grade_rows.append(
                    {
                        "excelRow": r,
                        "checkedGradeBands": [b for b, _ in checked_bands],
                        "ids": generated_ids,
                    }
                )

    meta = {
        "generatedAt": _now_iso(),
        "sheet": SHEET_NAME,
        "rowRange": [ROW_START, ROW_END],
        "rowsScanned": rows_scanned,
        "requirementRows": requirement_rows,
        "itemsGenerated": len(items),
        "multiGradeRowsCount": len(multi_grade_rows),
        "multiGradeRows": multi_grade_rows,
        "warningsCount": len(warnings),
        "warnings": [w.__dict__ for w in warnings],
    }

    return items, meta


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    out_dir = os.path.join(project_root, "web", "data")
    os.makedirs(out_dir, exist_ok=True)

    out_json = os.path.join(out_dir, "cn_compulsory_science_knowledge.json")
    out_meta = os.path.join(out_dir, "cn_compulsory_science_knowledge_meta.json")

    print("开始解析：", SHEET_NAME)
    items, meta = parse()

    # 快速摘要
    print("解析完成：")
    print("  rowsScanned:", meta["rowsScanned"])
    print("  requirementRows:", meta["requirementRows"])
    print("  itemsGenerated:", meta["itemsGenerated"])
    print("  multiGradeRowsCount:", meta["multiGradeRowsCount"])
    print("  warningsCount:", meta["warningsCount"])

    # 抽样打印前3条
    for it in items[:3]:
        print("  sample:", it["id"], it["domainCode"], it["grades"], it["requirement"][:40])

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"cnCompulsoryScienceKnowledge": items}, f, ensure_ascii=False, indent=2)
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("已输出：")
    print(" ", out_json)
    print(" ", out_meta)


if __name__ == "__main__":
    main()

