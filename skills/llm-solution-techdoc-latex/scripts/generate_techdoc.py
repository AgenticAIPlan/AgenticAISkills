#!/usr/bin/env python3
"""从 JSON 生成企业大模型技术方案 LaTeX，并可选用 tectonic/xelatex/pdflatex 编译为 PDF。"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def latex_escape(text: str) -> str:
    if text is None:
        return ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in str(text))


def join_list(items):
    return "、".join(latex_escape(x) for x in items) if items else "待确认"


def render_rows_current_products(current_products):
    rows = []
    for item in current_products or []:
        name = latex_escape(item.get("name", ""))
        owner = latex_escape(item.get("owner", ""))
        notes = latex_escape(item.get("notes", ""))
        rows.append(f"{name} & {owner} & {notes} \\\\")
    return "\n".join(rows) if rows else r"\multicolumn{3}{l}{待补充} \\"


def render_rows_capabilities(caps):
    rows = []
    for item in caps or []:
        cap = latex_escape(item.get("capability", ""))
        notes = latex_escape(item.get("notes", ""))
        rows.append(f"{cap} & {notes} \\\\")
    return "\n".join(rows) if rows else r"\multicolumn{2}{l}{待补充} \\"


def render_mapping_rows(scenarios):
    rows = []
    for sc in scenarios or []:
        name = latex_escape(sc.get("name", ""))
        caps = "（示例）见能力清单"
        integration = join_list(sc.get("integration", []))
        kpis = join_list(sc.get("kpis", []))
        benefits = join_list(sc.get("expected_benefits", []))
        cell = f"{benefits}；KPI：{kpis}"
        rows.append(f"{name} & {caps} & {integration} & {latex_escape(cell)} \\\\")
    return "\n".join(rows) if rows else r"\multicolumn{4}{l}{待补充} \\"


def render_scenario_sections(scenarios):
    blocks = []
    for i, sc in enumerate(scenarios or [], start=1):
        name = latex_escape(sc.get("name", f"场景{i}"))
        pain_points = sc.get("pain_points", [])
        solution = latex_escape(sc.get("solution", ""))
        integration = sc.get("integration", [])
        benefits = sc.get("expected_benefits", [])
        kpis = sc.get("kpis", [])

        pain_items = "\n".join([f"  \\item {latex_escape(p)}" for p in pain_points]) or r"  \item 待补充"
        blocks.append(
            "\n".join(
                [
                    f"\\subsection{{{name}}}",
                    "\\begin{infobox}{痛点}",
                    "\\begin{itemize}[leftmargin=2.2em]",
                    pain_items,
                    "\\end{itemize}",
                    "\\end{infobox}",
                    "\\begin{infobox}{方案要点}",
                    solution if solution else "待补充",
                    "\\end{infobox}",
                    "\\begin{infobox}{集成与指标}",
                    "\\begin{itemize}[leftmargin=2.2em]",
                    f"  \\item 集成点：{join_list(integration)}",
                    f"  \\item 预期收益：{join_list(benefits)}",
                    f"  \\item KPI：{join_list(kpis)}",
                    "\\end{itemize}",
                    "\\end{infobox}",
                    "",
                ]
            )
        )
    return "\n".join(blocks) if blocks else "\\subsection{待补充}\n待补充\n"


def load_template(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8")


def _llm_capabilities(data: dict):
    """读取大模型能力列表；字段名为 llm_capabilities。"""
    return data.get("llm_capabilities") or []


def compile_pdf(tex_path: Path, engine_preference=None) -> None:
    candidates = []
    if engine_preference:
        candidates.append(engine_preference)

    base_dir = Path(__file__).resolve().parent.parent
    candidates.append(str(base_dir / "tools" / "tectonic" / "tectonic"))

    candidates.extend(
        [
            os.path.expanduser("~/.local/tectonic/tectonic"),
            "tectonic",
            "xelatex",
            "pdflatex",
        ]
    )

    tex_dir = tex_path.parent
    tex_name = tex_path.name

    for cmd in candidates:
        exe = shutil.which(cmd) if not cmd.startswith("/") else (cmd if os.path.exists(cmd) else None)
        if not exe:
            continue

        if os.path.basename(exe) in ("tectonic",):
            args = [exe, tex_name, "--outdir", str(tex_dir)]
        else:
            args = [exe, "-interaction=nonstopmode", "-halt-on-error", tex_name]

        try:
            if os.path.basename(exe) in ("xelatex", "pdflatex"):
                for _ in range(2):
                    p = subprocess.run(args, cwd=str(tex_dir), capture_output=True, text=True, timeout=180)
                    if p.returncode != 0:
                        raise RuntimeError(p.stderr or p.stdout)
            else:
                p = subprocess.run(args, cwd=str(tex_dir), capture_output=True, text=True, timeout=180)
                if p.returncode != 0:
                    raise RuntimeError(p.stderr or p.stdout)
            return
        except Exception as e:
            last_err = str(e)
            continue

    raise RuntimeError(
        "No LaTeX engine available (tried tectonic/xelatex/pdflatex). "
        "Install one (e.g. MacTeX) or provide a working tectonic binary. "
        f"Last error: {locals().get('last_err','(none)')}"
    )


def main():
    ap = argparse.ArgumentParser(description="从 JSON 生成企业大模型技术方案 LaTeX/PDF。")
    ap.add_argument("--input", required=True, help="输入 JSON 路径。")
    ap.add_argument("--outdir", required=True, help="输出目录。")
    ap.add_argument("--compile", action="store_true", help="生成 .tex 后编译 PDF。")
    ap.add_argument(
        "--preview",
        action="store_true",
        help="生成纯文本预览；若系统有 cupsfilter，可额外生成简易 preview PDF。",
    )
    ap.add_argument("--engine", default=None, help="指定引擎（tectonic/xelatex/pdflatex 或可执行文件路径）。")
    args = ap.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / "assets" / "techdoc-template.tex"

    data = json.loads(input_path.read_text(encoding="utf-8"))
    doc = data.get("doc", {})
    llm_caps = _llm_capabilities(data)

    tokens = {
        "DOC_TITLE": latex_escape(doc.get("title", "大模型技术方案")),
        "DOC_SUBTITLE": latex_escape(doc.get("subtitle", "")),
        "DOC_CUSTOMER": latex_escape(doc.get("customer_name", "待确认")),
        "DOC_INDUSTRY": latex_escape(doc.get("industry", "待确认")),
        "DOC_VERSION": latex_escape(doc.get("version", "V0.1")),
        "DOC_DATE": latex_escape(doc.get("date", "")),
        "DOC_AUTHOR": latex_escape(doc.get("author", "")),
        "DOC_REVIEWER": latex_escape(doc.get("reviewer", "")),
        "DOC_CONF": latex_escape(doc.get("confidentiality", "内部/客户专用")),
        "CURRENT_PRODUCTS_TABLE": render_rows_current_products(data.get("current_products", [])),
        "LLM_CAP_TABLE": render_rows_capabilities(llm_caps),
        "MAPPING_TABLE": render_mapping_rows(data.get("scenarios", [])),
        "SCENARIO_SECTIONS": render_scenario_sections(data.get("scenarios", [])),
        "DEPLOY_MODE": latex_escape(data.get("deployment", {}).get("mode", "待确认")),
        "DEPLOY_DATA_SOURCES": join_list(data.get("deployment", {}).get("data_sources", [])),
        "DEPLOY_SECURITY": join_list(data.get("deployment", {}).get("security_compliance", [])),
        "OPS_SLA": latex_escape(data.get("ops", {}).get("sla", "待确认")),
        "OPS_MONITORING": join_list(data.get("ops", {}).get("monitoring", [])),
        "OPS_COST": latex_escape(data.get("ops", {}).get("cost_model", "待确认")),
    }

    tex = load_template(template_path)
    for k, v in tokens.items():
        tex = tex.replace(f"<<{k}>>", v)

    out_stem = "llm-solution-techdoc"
    out_tex = outdir / f"{out_stem}.tex"
    out_tex.write_text(tex, encoding="utf-8")
    print(f"Wrote: {out_tex}")

    if args.preview:
        preview_txt = outdir / f"{out_stem}.preview.txt"
        preview_pdf = outdir / f"{out_stem}.preview.pdf"

        scenarios = data.get("scenarios", [])
        lines = []
        lines.append(doc.get("title", "大模型技术方案"))
        subtitle = doc.get("subtitle", "")
        if subtitle:
            lines.append(subtitle)
        lines.append("")
        lines.append(f"客户：{doc.get('customer_name','待确认')}    行业：{doc.get('industry','待确认')}")
        lines.append(f"版本：{doc.get('version','V0.1')}    日期：{doc.get('date','')}")
        lines.append("")
        lines.append("1 概述")
        lines.append("  - 目标：能力与系统结合，按场景/KPI可追溯")
        lines.append("")
        lines.append("2 现有产品清单")
        for item in data.get("current_products", []):
            lines.append(f"  - {item.get('name','')}（{item.get('owner','')}）：{item.get('notes','')}")
        lines.append("")
        lines.append("3 大模型能力清单（示例）")
        for item in llm_caps:
            lines.append(f"  - {item.get('capability','')}：{item.get('notes','')}")
        lines.append("")
        lines.append("4 场景方案（示例）")
        for sc in scenarios:
            lines.append(f"  - {sc.get('name','')}")
            for p in sc.get("pain_points", []):
                lines.append(f"      痛点：{p}")
            lines.append(f"      方案：{sc.get('solution','')}")
            if sc.get("integration"):
                lines.append(f"      集成：{'、'.join(sc.get('integration', []))}")
            if sc.get("expected_benefits"):
                lines.append(f"      收益：{'、'.join(sc.get('expected_benefits', []))}")
            if sc.get("kpis"):
                lines.append(f"      KPI：{'、'.join(sc.get('kpis', []))}")
        lines.append("")
        lines.append("5 部署/安全/运维（模板）")
        dep = data.get("deployment", {})
        ops = data.get("ops", {})
        lines.append(f"  - 部署模式：{dep.get('mode','待确认')}")
        if dep.get("data_sources"):
            lines.append(f"  - 数据源：{'、'.join(dep.get('data_sources', []))}")
        if dep.get("security_compliance"):
            lines.append(f"  - 合规：{'、'.join(dep.get('security_compliance', []))}")
        lines.append(f"  - SLA：{ops.get('sla','待确认')}")
        if ops.get("monitoring"):
            lines.append(f"  - 监控：{'、'.join(ops.get('monitoring', []))}")
        lines.append(f"  - 成本：{ops.get('cost_model','待确认')}")

        preview_txt.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        print(f"Wrote: {preview_txt}")

        cups = shutil.which("cupsfilter")
        if cups:
            p = subprocess.run(
                [cups, "-m", "application/pdf", str(preview_txt)],
                capture_output=True,
                timeout=60,
            )
            if p.returncode == 0 and p.stdout:
                preview_pdf.write_bytes(p.stdout)
                print(f"Built: {preview_pdf} ({preview_pdf.stat().st_size} bytes)")
            else:
                print("Preview PDF generation failed; cupsfilter returned non-zero.", file=sys.stderr)
        else:
            print("cupsfilter not found; skipped preview PDF.", file=sys.stderr)

    if args.compile:
        compile_pdf(out_tex, engine_preference=args.engine)
        out_pdf = out_tex.with_suffix(".pdf")
        if out_pdf.exists():
            print(f"Built: {out_pdf} ({out_pdf.stat().st_size} bytes)")
        else:
            print("Compilation finished but PDF not found; check LaTeX logs.", file=sys.stderr)


if __name__ == "__main__":
    main()
