#!/usr/bin/env python3
"""Build a standard Hubei AI ecosystem lead template from a raw enterprise list."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


HEADERS = [
    "企业名称",
    "所在城市",
    "行业",
    "核心产品/业务",
    "企业规模",
    "技术/研发情况",
    "近期动态",
    "AI需求判断",
    "潜在应用场景",
    "线索来源",
    "分类结果",
    "跟进建议",
    "当前状态",
    "更新时间",
]

COMPANY_KEYS = [
    "企业名称",
    "公司名称",
    "名称",
    "company",
    "company_name",
    "name",
]

COMPANY_KEYS_LOWER = {key.lower() for key in COMPANY_KEYS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a raw enterprise list into standard CSV/XLSX lead templates."
    )
    parser.add_argument("--input", required=True, help="Path to txt/csv/tsv/json input.")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for generated files. Defaults to current directory.",
    )
    parser.add_argument(
        "--source-label",
        default="待补充",
        help="Default value for the 线索来源 column.",
    )
    parser.add_argument(
        "--status",
        default="新增",
        help="Default value for the 当前状态 column.",
    )
    return parser.parse_args()


def normalize_name(raw: str) -> str:
    return " ".join(raw.strip().split())


def dedupe_keep_order(names: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for name in names:
        normalized = normalize_name(name)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def detect_company_key(row: dict) -> str | None:
    lowered = {str(key).strip().lower(): key for key in row.keys()}
    for candidate in COMPANY_KEYS:
        if candidate in row:
            return candidate
        key = lowered.get(candidate.lower())
        if key is not None:
            return key
    return None


def row_looks_like_header(first_row: list[str], sample_text: str) -> bool:
    normalized = [cell.strip().lower() for cell in first_row if cell.strip()]
    if any(cell in COMPANY_KEYS_LOWER for cell in normalized):
        return True
    try:
        return csv.Sniffer().has_header(sample_text)
    except csv.Error:
        return False


def load_names(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return dedupe_keep_order(path.read_text(encoding="utf-8").splitlines())
    if suffix in {".csv", ".tsv"}:
        delimiter = "," if suffix == ".csv" else "\t"
        raw_text = path.read_text(encoding="utf-8-sig")
        rows = list(csv.reader(io.StringIO(raw_text), delimiter=delimiter))
        non_empty_rows = [row for row in rows if row]
        if not non_empty_rows:
            return []

        if row_looks_like_header(non_empty_rows[0], raw_text):
            reader = csv.DictReader(io.StringIO(raw_text), delimiter=delimiter)
            names = []
            for row in reader:
                key = detect_company_key(row)
                if key is None and reader.fieldnames:
                    first_key = reader.fieldnames[0]
                    value = row.get(first_key, "")
                else:
                    value = row.get(key or "", "")
                names.append(value)
            return dedupe_keep_order(names)

        return dedupe_keep_order(row[0] for row in non_empty_rows if row)
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list.")
        names = []
        for item in data:
            if isinstance(item, str):
                names.append(item)
                continue
            if isinstance(item, dict):
                key = detect_company_key(item)
                if key is not None:
                    names.append(str(item.get(key, "")))
                    continue
            raise ValueError("JSON list items must be strings or objects with a company-name field.")
        return dedupe_keep_order(names)
    raise ValueError(f"Unsupported input format: {suffix}")


def build_rows(names: list[str], source_label: str, status: str) -> list[list[str]]:
    rows = []
    for name in names:
        row = [""] * len(HEADERS)
        row[0] = name
        row[9] = source_label
        row[12] = status
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerows(rows)


def col_name(index: int) -> str:
    name = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def worksheet_xml(rows: list[list[str]]) -> str:
    header_cells = []
    for idx, value in enumerate(HEADERS, start=1):
        cell_ref = f"{col_name(idx)}1"
        header_cells.append(inline_str_cell(cell_ref, value))

    body_rows = []
    for row_idx, row in enumerate(rows, start=2):
        cells = []
        for col_idx, value in enumerate(row, start=1):
            if value == "":
                continue
            cells.append(inline_str_cell(f"{col_name(col_idx)}{row_idx}", value))
        body_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')

    dimension = f"A1:{col_name(len(HEADERS))}{max(1, len(rows) + 1)}"
    cols_xml = (
        "<cols>"
        '<col min="1" max="1" width="28" customWidth="1"/>'
        '<col min="2" max="4" width="18" customWidth="1"/>'
        '<col min="5" max="6" width="16" customWidth="1"/>'
        '<col min="7" max="14" width="24" customWidth="1"/>'
        "</cols>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<dimension ref=\"{dimension}\"/>"
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        "<sheetFormatPr defaultRowHeight=\"15\"/>"
        f"{cols_xml}"
        "<sheetData>"
        f'<row r="1">{"".join(header_cells)}</row>'
        f'{"".join(body_rows)}'
        "</sheetData>"
        "</worksheet>"
    )


def inline_str_cell(ref: str, value: str) -> str:
    return (
        f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    )


def write_xlsx(path: Path, rows: list[list[str]]) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="企业线索模板" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""
    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
</Properties>
"""
    core_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
</cp:coreProperties>
"""

    with ZipFile(path, "w", compression=ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", worksheet_xml(rows))
        zf.writestr("docProps/app.xml", app_xml)
        zf.writestr("docProps/core.xml", core_xml)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        names = load_names(input_path)
    except Exception as exc:
        print(f"Failed to read input: {exc}", file=sys.stderr)
        return 1

    if not names:
        print("No enterprise names found in input.", file=sys.stderr)
        return 1

    rows = build_rows(names, args.source_label, args.status)
    csv_path = output_dir / "hubei_ai_leads_template.csv"
    xlsx_path = output_dir / "hubei_ai_leads_template.xlsx"
    write_csv(csv_path, rows)
    write_xlsx(xlsx_path, rows)

    print(f"Generated {len(rows)} rows.")
    print(f"CSV: {csv_path}")
    print(f"XLSX: {xlsx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
