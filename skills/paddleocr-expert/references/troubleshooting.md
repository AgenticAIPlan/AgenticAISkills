# Troubleshooting

Last reviewed: April 16, 2026.

Use this file when the user reports install failures, version mismatch, vLLM trouble, ONNX errors, memory issues, bad-case parsing, or serving instability.

## First Checks

Always verify these before deeper debugging:

1. exact PaddleOCR version
2. exact PaddleX version
3. exact PaddlePaddle version
4. OS and whether it is native Windows, Linux, Docker, or WSL
5. GPU model and CUDA version
6. exact command used
7. whether the pipeline requires `doc-parser`, `ie`, or `trans`

## Recurring Issue Themes

As of April 16, 2026, the open PaddleOCR issues page shows recurring problem categories around:

- dependency conflicts or installation issues
- deployment and ONNX/serving problems
- memory growth and OOM
- PaddleOCR-VL bad cases on specific tables or layouts
- reading-order or parsing-order problems
- C++ layout/deployment questions

Representative open issues visible on the public issues page include:

- `#17186` dependency conflict while importing PaddleOCR
- `#17888` intermittent memory growth during continuous runs
- `#17060` ONNX conversion error
- `#17839` PaddleOCR-VL-1.5 high-performance serving error
- `#17437` PaddleOCR-VL bad-case cell omission
- `#16847` parsing result text order issue

Treat these as signals for where the ecosystem is most fragile today.

## Version And Dependency Mismatch

Likely symptoms:

- import errors
- missing modules
- CLI commands present but pipelines unavailable
- serving starts but a requested pipeline crashes later

Likely fixes:

- install the right optional extra
- align PaddleOCR and PaddleX versions
- confirm PaddlePaddle version is within the documented range

## Windows, WSL, And 50-Series Caveats

- PaddleOCR docs provide a special Windows wheel flow for NVIDIA 50-series GPUs.
- The same docs also note known issues with text recognition training on that Windows 50-series path.
- For PaddleOCR-VL, docs explicitly warn that `vLLM`, `SGLang`, and `FastDeploy` do not run natively on Windows; use the official Docker path instead.

## vLLM Caveats For PaddleOCR-VL

The latest PaddleOCR-VL usage docs say:

- `vLLM` expects CUDA 12.6 or newer
- compute capability should be at least 8.0
- although `vLLM` may launch on CC 7.x GPUs like T4 or V100, timeout or OOM can occur and that setup is not recommended

If the user mentions `T4`, `V100`, timeout, or unexplained OOM with PaddleOCR-VL, surface this early.

## Serving Expectations

PaddleOCR docs for `PP-StructureV3` explicitly say the basic serving solution processes one request at a time and is intended for quick validation, integration, or low-concurrency use.

That means:

- poor concurrency is not automatically a bug
- first prove correctness in basic serving
- move to high-stability serving and configuration tuning only when throughput actually matters

## Debugging Output Mismatches

If the user says:

- text is out of order
- Markdown does not match JSON
- table cells are missing
- repeated numbers hallucinate
- one class of region is consistently omitted

Then check in this order:

1. wrong pipeline for the task
2. bad-case limitation in the chosen model
3. PDF page preprocessing/orientation issue
4. layout mode or structure merge setting
5. post-processing expectations not matching the pipeline output contract

## Good Escalation Advice

When the user is blocked, prefer this escalation path:

1. reproduce on one minimal input
2. swap to the closest alternative pipeline
3. export the PaddleX YAML and inspect model settings
4. retry with documented hardware/backend path
5. consult the latest relevant GitHub issues before claiming it is user error
