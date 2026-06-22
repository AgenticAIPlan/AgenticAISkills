---
name: material-paper-extractor
description: >-
  Extract structured Composition-Processing-Microstructure-Properties data from
  alloy research papers (PDFs). Use this skill whenever the user asks to extract
  materials science data, parse alloy papers, run the extraction pipeline, or
  process metallurgy/metallography research PDFs. Triggers on: "extract materials",
  "parse alloy paper", "materials data extraction", "composition processing properties",
  "材料数据提取", "合金论文解析". Even if the user just provides a PDF of a materials
  science paper and asks to extract structured data from it, use this skill.
---

# Material Paper Extractor

Extract structured Composition-Processing-Microstructure-Properties data from alloy research papers.

## Pipeline Overview

```
PDF
 │
 ▼
Step 1  OCR          →  01_ocr/{id}.json
 │
 ▼
Step 2  Combine      →  02_combine/{id}.txt  ← ground truth for Steps 3–7
 │
 ▼
Step 3  Extract      →  03_extract/{id}.json
 │
 ▼
Step 4  Validate     →  04_validate/{id}.json  [+ _issues.md if errors/warnings]
 │
 ▼
Step 5  Review       →  05_review/{id}_review.md
 │
 ▼
Step 6  Revise       →  06_revise/{id}_revised.json  [+ _revision_notes.md]
 │
 ├──▶ Step 7  Evaluate (conditional on {comparison_path})
 │              →  07_evaluate/{id}_evaluation.md
 │
 ▼
Step 8  Summary
 ├── 8A (script) →  08_summary/06_revise_summary.json / .csv / _stats.md
 └── 8B (LLM, conditional on Step 7) →  08_summary/evaluation_summary.md
```

**Ground Truth Principle**: `02_combine/{id}.txt` is the canonical paper text. Every step from 3 onward derives from and is evaluated against it.

## Template Variables

This skill uses the following runtime variables resolved at execution time:

- `{output_base}` — Root directory for all pipeline outputs. When starting a new extraction,
  create this directory including a timestamp (e.g., `/path/to/output/20260408/`).
  If reusing existing results, point to the existing directory.
- `{id}` — Unique identifier for each paper. Use the filename stem or author-year format
  (e.g., `Kumar_2018`, or a short form of the paper title).
- `{pdf_path}` — Absolute path to the input PDF file.
- `{comparison_path}` — (Step 7 only, optional) Absolute path to an alternative extraction
  result to compare against. Step 7 is skipped when this variable is not set.
  Example: `/path/to/other_tool/{id}.json`

**Variable substitution**: These placeholders appear throughout this SKILL.md and in the
`references/` prompt files. When assembling prompts for sub-agents, replace every
`{variable}` with its resolved value before injecting the text. The LLM should see the
actual path, not the literal placeholder.

## Skill Base Directory

This skill is located at: `~/.claude/skills/material-paper-extractor/`

All reference files and scripts are relative to this directory.

## Directory Structure

```
{output_base}/
├── 01_ocr/            Step1 — PaddleOCR output
├── 02_combine/        Step2 — Combined original text (ground truth)
├── 03_extract/        Step3 — Extraction results
├── 04_validate/       Step4 — After script validation
├── 05_review/         Step5 — Review report
├── 06_revise/         Step6 — Revised results
├── 07_evaluate/       Step7 — Comparison evaluation (conditional)
└── 08_summary/        Step8 — Aggregated summary
```

## File Path Quick Reference

| Step | Resource | Path |
|------|----------|------|
| Step3 | Extraction rules + schema | `references/03-extract-system-prompt.md` |
| Step3 | Extraction workflow | `references/03-extract-user-prompt.md` |
| Step4 | Validation script | `scripts/04-validate.py` |
| Step5 | Review prompt | `references/05-review.md` |
| Step6 | Revision prompt | `references/06-revise.md` |
| Step7 | Evaluation prompt | `references/07-evaluate.md` |
| Step8 | Summary script | `scripts/08-summarize.py` |
| Step8 | Summary prompt | `references/08-summary.md` |

## Output Path Rules (MANDATORY)

**Sub-agents must strictly follow these paths. Do not create any sub-directories not listed below:**

| Step | Output | Required Path |
|------|--------|---------------|
| Step1 | OCR JSON | `{output_base}/01_ocr/{id}.json` |
| Step2 | Combined text | `{output_base}/02_combine/{id}.txt` |
| Step3 | Extraction JSON | `{output_base}/03_extract/{id}.json` |
| Step4 | Validated JSON | `{output_base}/04_validate/{id}.json` |
| Step4 | Issue log (when errors/warnings) | `{output_base}/04_validate/{id}_issues.md` |
| Step5 | Review report | `{output_base}/05_review/{id}_review.md` |
| Step6 | Revised JSON | `{output_base}/06_revise/{id}_revised.json` |
| Step6 | Revision notes sidecar | `{output_base}/06_revise/{id}_revision_notes.md` |
| Step7 | Evaluation report | `{output_base}/07_evaluate/{id}_evaluation.md` |
| Step8A | Data summary JSON | `{output_base}/08_summary/06_revise_summary.json` |
| Step8A | Data summary CSV | `{output_base}/08_summary/06_revise_summary.csv` |
| Step8A | Stats report | `{output_base}/08_summary/06_revise_stats.md` |
| Step8B | Narrative summary (LLM, conditional) | `{output_base}/08_summary/evaluation_summary.md` |

**Do not create unlisted directories. All files must be written to the paths specified above.**

---

## Step 1 — OCR (PaddleOCR)

**Prerequisites — set credentials in your shell environment before running (never paste tokens here):**

```bash
export PADDLEOCR_DOC_PARSING_API_URL="<your-paddleocr-endpoint>"
export PADDLEOCR_ACCESS_TOKEN="<your-paddleocr-token>"
```

Add these to `~/.bashrc` or a local `.env` file that is sourced before invoking the pipeline. **Do not commit tokens to any file tracked by git or stored in skill directories.**

**Run:**

```bash
cd ~/.claude/skills/paddleocr-doc-parsing
conda activate thl
python scripts/vl_caller.py \
  --file-path "{pdf_path}" \
  --output "{output_base}/01_ocr/{id}.json" \
  --pretty
```

Output: `{output_base}/01_ocr/{id}.json`

---

## Step 2 — Combine Text

Read the Step 1 OCR JSON, extract:
1. `text` field (full markdown)
2. Per-page `<table>` markdown from `result.result.layoutParsingResults[n].markdown.text`

Combine into a single text block. Use the **Write tool** to save the output file (OCR text may contain Chinese characters — avoid bash heredocs for non-ASCII content).

Output: `{output_base}/02_combine/{id}.txt`

**This combined text is the ground truth for all downstream steps.**

---

## Step 3 — Extract

Read these two reference files from the skill directory:
1. `references/03-extract-system-prompt.md` — your extraction rules and JSON schema
2. `references/03-extract-user-prompt.md` — your extraction workflow

Follow them as your own instructions. In the user prompt, replace the `{paper_text}` placeholder with the Step 2 combined text. Then perform the extraction directly, producing the JSON output.

**Critical**: Output must be **strictly valid JSON — no markdown fences, no comments, no conversational text**. Use the **Write tool** to save the file directly; do not use bash heredocs for JSON with non-ASCII content.

Output: `{output_base}/03_extract/{id}.json`

---

## Step 4 — Validate (Script)

```bash
conda activate thl
python ~/.claude/skills/material-paper-extractor/scripts/04-validate.py \
  {output_base}/03_extract/{id}.json \
  {output_base}/04_validate/{id}.json
```

Schema validation: role values, composition sums, numeric ranges, Main_Phase prohibition, Elongation bounds, YS ≤ UTS check.

**The validated file is always written**, even when issues are found, so the review step can still run. When errors or warnings exist, a sidecar report is also written to `{output_base}/04_validate/{id}_issues.md`.

- Exit 0: passed (may include warnings)
- Exit 1: hard errors found — the review step **must** address them
- Exit 2: I/O failure

Output: `{output_base}/04_validate/{id}.json`

**From Step 5 onwards, all downstream steps read from `04_validate/` as input data.**

---

## Step 5 — Review

Read `references/05-review.md` and follow it as your own instructions.

Your inputs:
- **`{output_base}/02_combine/{id}.txt`** — ground truth
- `references/03-extract-system-prompt.md` and `references/03-extract-user-prompt.md` — extraction rules (context for judging correctness)
- **`{output_base}/04_validate/{id}.json`** — validated extraction data
- **`{output_base}/04_validate/{id}_issues.md`** (if it exists) — pre-identified schema errors from the script; these must be addressed in the review

Play devil's advocate. Apply maximum scrutiny to catch errors.

**Report must be written in Chinese.**

Output: `{output_base}/05_review/{id}_review.md`

---

## Step 6 — Revise

Read `references/06-revise.md` and follow it as your own instructions.

Your inputs:
- **`{output_base}/02_combine/{id}.txt`** — ground truth
- `references/03-extract-system-prompt.md` and `references/03-extract-user-prompt.md` — extraction rules
- **`{output_base}/04_validate/{id}.json`** — validated extraction data
- **`{output_base}/05_review/{id}_review.md`** — review report

Fix issues identified in the review, producing the final corrected JSON.

**Critical**: Output must be **strictly valid JSON — no markdown fences, no `/* */` comments, no conversational text**. Use the **Write tool** to save.

Outputs:
- `{output_base}/06_revise/{id}_revised.json` — corrected extraction (primary artifact)
- `{output_base}/06_revise/{id}_revision_notes.md` — change log sidecar (see `references/06-revise.md`)

---

## Step 7 — Evaluate (Conditional)

**Only execute when `{comparison_path}` is defined.** Skip this step if no comparison path is provided.

Read `references/07-evaluate.md` and follow it as your own instructions.

Your inputs:
- **`{output_base}/02_combine/{id}.txt`** — ground truth
- **`{output_base}/06_revise/{id}_revised.json`** — this pipeline's output (Result A)
- **`{comparison_path}`** — alternative extraction to compare against (Result B)

Evaluate both results equally against the original paper text as the sole fact base.

**Report must be written in Chinese.**

Output: `{output_base}/07_evaluate/{id}_evaluation.md`

---

## Step 8 — Summary (Always Execute)

**Always execute this step.**

### 8A — Data aggregation (script)

Aggregates all revised extraction JSONs into a flat cross-paper dataset.

```bash
conda activate thl
python ~/.claude/skills/material-paper-extractor/scripts/08-summarize.py \
  {output_base}/06_revise \
  {output_base}/08_summary
```

Output (prefixed with the source directory name `06_revise`):
- `{output_base}/08_summary/06_revise_summary.json` — merged papers + items
- `{output_base}/08_summary/06_revise_summary.csv` — flat property table
- `{output_base}/08_summary/06_revise_stats.md` — per-paper counts + property distribution

### 8B — Narrative evaluation summary (LLM task, conditional on Step 7 having run)

**The script does not process `.md` files.** If Step 7 produced evaluation reports,
generate the cross-paper narrative summary using the LLM by following
`references/08-summary.md` as your instructions.

Inputs: all `{output_base}/07_evaluate/*_evaluation.md` files
Output: `{output_base}/08_summary/evaluation_summary.md` (LLM-written, not script-generated)

---

## How to Execute This Skill

When the user provides a PDF (or multiple PDFs) and asks to extract materials data:

1. Determine `{output_base}` (ask user or use reasonable default based on PDF location, include timestamp)
2. Determine `{id}` for each paper (use filename stem or author-year format)
3. Execute Steps 1-6 for each paper sequentially
4. Execute Step 7 only if comparison data exists
5. Execute Step 8 after all papers are processed

**Reusing existing results**: If `{output_base}/01_ocr/{id}.json` already exists, skip Step 1 and reuse the existing OCR result. Similarly, if any intermediate step's output already exists and the user confirms it's valid, you can skip that step and proceed from the next.

