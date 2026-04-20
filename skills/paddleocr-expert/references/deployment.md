# Deployment Guide

Last reviewed: April 16, 2026.

Use this file for installation, CLI/Python entry points, service deployment, Docker patterns, and PaddleX YAML customization.

## Install By Capability

PaddleOCR 3.x separates core and optional dependencies.

### Minimal OCR

```bash
python -m pip install paddleocr
```

Use this for:

- PP-OCRv5
- basic OCR pipeline
- document image preprocessing

### Document Parsing

```bash
python -m pip install "paddleocr[doc-parser]"
```

Use this for:

- `PP-StructureV3`
- `table_recognition_v2`
- `PaddleOCR-VL`

### Information Extraction

```bash
python -m pip install "paddleocr[ie]"
```

Use this for:

- `PP-ChatOCRv4`

### Everything

```bash
python -m pip install "paddleocr[all]"
```

## PaddlePaddle Version Notes

- The repo `pyproject.toml` currently pins `paddlex[ocr-core]>=3.4.0,<3.5.0` for the base `paddleocr` package.
- PaddleOCR docs describe the current 3.4.x line as matching PaddleX `>=3.4.0,<3.5.0`.
- Do not mix arbitrary PaddleOCR, PaddleX, and PaddlePaddle versions when debugging. Check the version trio first.

## First Local Validation

Before serving, validate on representative files:

1. single image
2. single PDF page
3. multi-page PDF
4. full service call
5. frontend or downstream integration

This isolates model problems from serving problems.

## CLI And Python Entry Points

### General OCR

PaddleX basic serving:

```bash
paddlex --install serving
paddlex --serve --pipeline OCR
```

### Export Or Inspect Pipeline Config

```bash
paddlex --get_pipeline_config OCR
```

Or from Python:

```python
from paddleocr import PaddleOCR

pipeline = PaddleOCR()
pipeline.export_paddlex_config_to_yaml("ocr_config.yaml")
```

Use YAML configs whenever the user needs:

- custom model paths
- batch size changes
- device changes
- serving config edits
- swapping module models inside a pipeline

### Table Recognition

The table recognition v2 result object supports saving to XLSX, HTML, and JSON. The docs explicitly mention `save_to_xlsx()` and state the Excel representation is written to the target `.xlsx` file.

### PaddleOCR-VL

Official package path:

```bash
python -m pip install "paddleocr[doc-parser]"
```

CLI:

```bash
paddleocr doc_parser -i your_file.png
```

Python:

```python
from paddleocr import PaddleOCRVL

pipeline = PaddleOCRVL(pipeline_version="v1")
output = pipeline.predict("your_file.png")
for res in output:
    res.save_to_json("output")
    res.save_to_markdown("output")
```

## Basic Serving

PaddleOCR docs recommend starting with PaddleX basic serving for quick validation.

### Install Serving Plugin

```bash
paddlex --install serving
```

### Run Server

```bash
paddlex --serve --pipeline {pipeline-name-or-yaml}
```

Useful flags:

- `--device`
- `--host`
- `--port`
- `--use_hpip`
- `--hpi_config`

## High-Stability Serving

If the user needs stronger production serving, scaling, or Triton-backed deployment, route them to PaddleX high-stability serving. Keep the expectation clear: PaddleOCR docs note that the current high-stability serving path may not yet outperform the old 2.x PaddleServing setup in every case, though it fully supports PaddlePaddle 3.x.

## Docker Patterns

If the user already has a Docker command like:

```bash
docker run ... paddleocr:latest paddlex --serve --pipeline OCR ...
```

Explain that:

- the container is fine
- the chosen capability is defined by `--pipeline`
- expanding from plain OCR to tables or document parsing usually means changing the pipeline name or loading a different YAML, not patching the same `/ocr` interface forever

Typical next steps:

- OCR only: `OCR`
- tables: `table_recognition_v2`
- structure-heavy docs: `PP-StructureV3`
- KIE/doc QA: `PP-ChatOCRv4-doc`
- VLM parsing: `PaddleOCR-VL` or `PaddleOCR-VL-1.5`

## PaddleOCR-VL Accelerated Serving

The Hugging Face model card and repo docs describe an optimized server path using `paddleocr genai_server`, including `vLLM` support for the VLM component. Use this only when the user actually needs PaddleOCR-VL acceleration and their hardware matches the documented constraints.

The model card also notes:

- official inference path is preferred for full page-level parsing
- `transformers` support is currently positioned for element-level recognition rather than full document parsing
