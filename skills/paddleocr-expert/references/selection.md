# Pipeline Selection

Last reviewed: April 16, 2026.

Use this file when the user asks which PaddleOCR or PaddleX pipeline to choose, how two pipelines differ, or what output format a pipeline is good at.

## Quick Decision Matrix

| Need | Best first choice | Why |
| --- | --- | --- |
| Fast OCR from image/screenshot | `PP-OCRv5` / PaddleX `OCR` | Best default for plain text spotting and mixed-language scene OCR |
| Parse tables from images or PDFs | `table_recognition_v2` | Purpose-built table pipeline; supports HTML and XLSX result saving |
| Convert complex PDF/image to Markdown or JSON while preserving layout | `PP-StructureV3` | Structure-aware parsing with reading order, formulas, charts, and table sub-pipeline |
| Extract named fields or answer questions over docs | `PP-ChatOCRv4-doc` | KIE and document QA focus |
| Strong multilingual VLM parsing, irregular layouts, or more difficult real-world docs | `PaddleOCR-VL` / `PaddleOCR-VL-1.5` | SOTA VLM-style document parsing with strong multilingual support |

## Choose Between The Big Four

### `PP-OCRv5`

Pick this when the user mainly wants text boxes and recognized text. It is the default for `/ocr` style APIs and is usually the lowest-friction choice.

### `table_recognition_v2`

Pick this when the success criterion is the table itself rather than all page elements. Official docs note that the result object supports:

- `save_to_xlsx()`
- `save_to_html()`
- `save_to_json()`

Use this when the user says "table", "Excel", "HTML table", "PDF table extraction", or "表格识别".

### `PP-StructureV3`

Pick this when the user wants full document structure, especially:

- Markdown or JSON output
- table + formula + chart + reading order
- coordinate-rich structured parsing
- a pipeline approach rather than a VLM approach

Prefer `PP-StructureV3` over `PaddleOCR-VL` when downstream systems need fine-grained coordinates or stable structured sub-results.

### `PaddleOCR-VL` / `PaddleOCR-VL-1.5`

Pick this when the user needs:

- multilingual parsing
- hard real-world documents
- irregular or distorted layouts
- cross-page table merging
- a VLM-like document parser

The Hugging Face model card for `PaddleOCR-VL` describes the 0.9B model as supporting 109 languages and handling text, tables, formulas, and charts. The latest PaddleOCR home page highlights `PaddleOCR-VL-1.5` as the newer flagship line.

## PaddleOCR And PaddleX Name Mapping

PaddleOCR 3.x docs state that PaddleOCR uses PaddleX underneath for inference and deployment, and that pipeline names stay aligned. Use these mappings when moving from user-facing PaddleOCR docs to `paddlex --serve` commands:

| PaddleOCR pipeline | PaddleX registration name |
| --- | --- |
| General OCR | `OCR` |
| PP-StructureV3 | `PP-StructureV3` |
| PP-ChatOCRv4 | `PP-ChatOCRv4-doc` |
| General Table Recognition V2 | `table_recognition_v2` |
| Formula Recognition | `formula_recognition` |
| Seal Text Recognition | `seal_recognition` |
| Document Image Preprocessing | `doc_preprocessor` |
| Document Understanding | `doc_understanding` |
| PP-DocTranslation | `PP-DocTranslation` |
| PaddleOCR-VL | `PaddleOCR-VL` |
| PaddleOCR-VL-1.5 | `PaddleOCR-VL-1.5` |

## Version-Sensitive Names To Recheck

Re-verify these during maintenance because naming can shift with new releases:

- flagship VLM names such as `PaddleOCR-VL` and `PaddleOCR-VL-1.5`
- PaddleX registration names used by `paddlex --serve`
- whether a capability is positioned as a pipeline, model family, or package extra in the latest docs

## Common Recommendation Patterns

- Existing `/ocr` API, wants table parsing too:
  keep `/ocr` on `OCR`; add a second service for `table_recognition_v2` or `PP-StructureV3`.
- Wants `PDF -> Excel`:
  use `table_recognition_v2` first; if the PDF also needs broader structure understanding, compare with `PP-StructureV3` or `PaddleOCR-VL` and then wrap XLSX generation in your own backend flow.
- Wants `PDF -> Markdown`:
  start with `PP-StructureV3`; escalate to `PaddleOCR-VL(-1.5)` for harder multilingual or distorted documents.
- Wants fields like name, date, amount, address:
  use `PP-ChatOCRv4-doc`, not plain OCR.
