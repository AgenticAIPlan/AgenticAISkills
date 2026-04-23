# Version Maintenance

Last reviewed: April 21, 2026.

Use this file when:

- the user asks for the latest PaddleOCR or PaddleX usage,
- the answer depends on exact commands or package extras,
- model naming may have changed,
- or you are maintaining this skill after review feedback.

## High-Risk Drift Areas

Check these first because they change fastest:

1. package install groups such as `paddleocr`, `paddleocr[doc-parser]`, `paddleocr[ie]`, and `paddleocr[all]`
2. CLI entry points such as `paddlex --serve`, `paddlex --get_pipeline_config`, and `paddleocr doc_parser`
3. PaddleX pipeline registration names such as `OCR`, `table_recognition_v2`, `PP-StructureV3`, `PP-ChatOCRv4-doc`, and `PaddleOCR-VL(-1.5)`
4. flagship model naming on docs home pages and model cards
5. hardware and backend caveats for Windows, WSL, CUDA, `vLLM`, and high-performance serving

## Maintenance Checklist

For each review pass:

1. confirm the "Last reviewed" date in each reference file
2. verify install commands against the current official docs
3. verify model and pipeline names against the current official docs
4. verify any hardware caveats that could have changed with new releases
5. update wording where the old answer sounds more certain than the docs support

## Minimum Files To Recheck

- `references/deployment.md`
- `references/selection.md`
- `references/troubleshooting.md`

These files contain the most version-sensitive commands and names.

## Answering Rule

When the user asks a time-sensitive question, do not answer from memory alone.
Re-check the official source first, then answer with clear wording such as:

- "As of April 21, 2026, the docs show ..."
- "This is version-sensitive; the current docs list ..."
- "I did not find an official retention guarantee, so treat it as temporary."
