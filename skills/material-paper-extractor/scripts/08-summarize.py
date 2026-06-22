#!/usr/bin/env python3
"""Summary generator — merges per-paper extraction JSON into a cross-paper summary.

Given a directory of extraction JSON files (typically ``06_revise/``), writes:

- ``{prefix}_summary.json`` — merged papers + items
- ``{prefix}_summary.csv`` — flat one-row-per-property table
- ``{prefix}_stats.md`` — per-paper + property-type statistics

The output filenames are prefixed with the input directory's basename so that
running the script on different source directories produces independent files
in the same summary directory (e.g. ``06_revise_summary.json`` vs.
``eval_summary.json``) and never clobbers each other.

Note: this script only processes JSON files. The narrative cross-paper evaluation
summary described in ``references/08-summary.md`` is an LLM task that reads
``07_evaluate/*.md``, not something this script produces.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from typing import Any

logger = logging.getLogger("summarize")

FIXED_COLS: list[str] = [
    "source_file",
    "role",
    "alloy_name",
    "process_category",
    "property_name",
    "test_condition",
    "value_numeric",
    "value_range",
    "value_stddev",
    "unit",
    "test_temperature_K",
    "data_source",
    "test_specimen",
    "strain_rate_s1",
    "tensile_speed_mm_min",
    "hardness_load",
    "hardness_dwell_time_s",
]


def _load_json_files(results_dir: str) -> list[tuple[str, dict[str, Any]]]:
    loaded: list[tuple[str, dict[str, Any]]] = []
    for fname in sorted(os.listdir(results_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(results_dir, fname)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("invalid JSON in %s: %s", fname, e)
            continue
        except OSError as e:
            logger.error("cannot read %s: %s", fname, e)
            continue
        loaded.append((fname, data))
    return loaded


def _row_for_property(
    source_file: str,
    ci: dict[str, Any],
    pi: dict[str, Any],
    prop: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_file": source_file,
        "role": ci.get("Role") or "",
        "alloy_name": ci.get("Alloy_Name_Raw") or "",
        "process_category": pi.get("Process_Category") or "",
        "property_name": prop.get("Property_Name") or "",
        "test_condition": prop.get("Test_Condition"),
        "value_numeric": prop.get("Value_Numeric"),
        "value_range": prop.get("Value_Range"),
        "value_stddev": prop.get("Value_StdDev"),
        "unit": prop.get("Unit"),
        "test_temperature_K": prop.get("Test_Temperature_K"),
        "data_source": prop.get("Data_Source"),
        "test_specimen": prop.get("Test_Specimen"),
        "strain_rate_s1": prop.get("Strain_Rate_s1"),
        "tensile_speed_mm_min": prop.get("Tensile_Speed_mm_min"),
        "hardness_load": prop.get("Hardness_Load"),
        "hardness_dwell_time_s": prop.get("Hardness_Dwell_Time_s"),
    }


def _write_summary_json(
    summary_dir: str,
    prefix: str,
    papers: list[dict[str, Any]],
    items: list[dict[str, Any]],
) -> None:
    path = os.path.join(summary_dir, f"{prefix}_summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"papers": papers, "items": items}, f, indent=2, ensure_ascii=False)


def _write_summary_csv(
    summary_dir: str, prefix: str, items: list[dict[str, Any]]
) -> None:
    rows: list[dict[str, Any]] = []
    for it in items:
        ci = it.get("Composition_Info") or {}
        pi = it.get("Process_Info") or {}
        for prop in it.get("Properties_Info") or []:
            rows.append(
                _row_for_property(it.get("_source_file", ""), ci, pi, prop)
            )

    path = os.path.join(summary_dir, f"{prefix}_summary.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIXED_COLS)
        writer.writeheader()
        writer.writerows(rows)


def _write_stats_md(
    summary_dir: str,
    prefix: str,
    papers: list[dict[str, Any]],
    items: list[dict[str, Any]],
) -> None:
    prop_types: dict[str, int] = {}
    for it in items:
        for prop in it.get("Properties_Info") or []:
            name = prop.get("Property_Name") or "unknown"
            prop_types[name] = prop_types.get(name, 0) + 1

    total_properties = sum(
        len(it.get("Properties_Info") or []) for it in items
    )

    lines: list[str] = [
        f"# Extraction Summary ({prefix})",
        "",
        f"- **Total papers:** {len(papers)}",
        f"- **Total materials (items):** {len(items)}",
        f"- **Total property measurements:** {total_properties}",
        f"- **Unique property types:** {len(prop_types)}",
        "",
        "## Per-Paper Breakdown",
        "",
        "| File | Materials | Properties | DOI |",
        "|------|-----------|------------|-----|",
    ]
    for p in papers:
        lines.append(
            f"| {p['source_file']} | {p['n_materials']} | "
            f"{p['n_properties']} | {p['doi']} |"
        )

    lines.append("")
    lines.append("## Property Type Distribution")
    lines.append("")
    for name, count in sorted(prop_types.items(), key=lambda x: -x[1]):
        lines.append(f"- **{name}**: {count}")

    path = os.path.join(summary_dir, f"{prefix}_stats.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def summarize(results_dir: str, summary_dir: str, prefix: str) -> int:
    if not os.path.isdir(results_dir):
        logger.error("results_dir not found: %s", results_dir)
        return 2

    os.makedirs(summary_dir, exist_ok=True)
    loaded = _load_json_files(results_dir)
    if not loaded:
        logger.warning("no JSON files found in %s", results_dir)

    all_items: list[dict[str, Any]] = []
    all_papers: list[dict[str, Any]] = []

    for fname, data in loaded:
        paper_meta = data.get("Paper_Metadata") or {}
        items = data.get("items") or []

        for item in items:
            tagged = dict(item)
            tagged["_source_file"] = fname
            all_items.append(tagged)

        all_papers.append(
            {
                "source_file": fname,
                "doi": paper_meta.get("DOI") or "N/A",
                "paper_title": paper_meta.get("Paper_Title") or "N/A",
                "n_materials": len(items),
                "n_properties": sum(
                    len(it.get("Properties_Info") or []) for it in items
                ),
            }
        )

    _write_summary_json(summary_dir, prefix, all_papers, all_items)
    _write_summary_csv(summary_dir, prefix, all_items)
    _write_stats_md(summary_dir, prefix, all_papers, all_items)

    logger.info(
        "summary generated: %d papers, %d materials -> %s",
        len(all_papers),
        len(all_items),
        summary_dir,
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate cross-paper summary.")
    parser.add_argument("results_dir", help="directory of extraction JSON files")
    parser.add_argument(
        "summary_dir",
        nargs="?",
        help="output directory (default: <results_dir>/../08_summary)",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="filename prefix (default: basename of results_dir)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    summary_dir = args.summary_dir or os.path.join(
        args.results_dir, "..", "08_summary"
    )
    prefix = args.prefix or (
        os.path.basename(os.path.normpath(args.results_dir)) or "summary"
    )

    return summarize(args.results_dir, summary_dir, prefix)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
