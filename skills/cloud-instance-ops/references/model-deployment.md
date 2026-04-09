# Model deployment workflow

Use this reference for model deployment, exam, benchmark, or API-serving tasks.

## Default principle
**Single-run before serving.**

Do not start with API orchestration unless the task is explicitly about service debugging. First prove that the base model, command, or script works once.

## Recommended sequence
1. Read-only preflight
2. Single-run validation
3. Service deployment
4. Original example request validation
5. Output artifact validation
6. Repeated-request stability validation

## Preflight checklist
- model files exist and paths are correct
- inputs exist and formats match the task
- CPU/GPU/memory/disk are sufficient
- target port is free or intentionally reused
- dependency versions are known
- old services/processes are identified

## Final acceptance checklist
Do not say "done" until you have all applicable evidence:
- health/docs endpoint works
- original `curl` or request from the task prompt works
- output file exists
- output file size/type/basic content are reasonable
- repeated request also works
- logs do not show obvious repeated crashes

## Output reasonableness rules
- **TTS**: non-empty output, plausible duration, sample rate/channel count if available, file size not tiny
- **ASR**: text is non-empty and not obviously truncated or garbled
- **Image generation**: file format, dimensions, and size are plausible
- **Text generation**: length meets expectations and does not leak hidden reasoning or placeholders
- **OCR / parsing**: result is non-empty, structure is plausible, and exported files exist if the task requires them

## Deployment claim rules
- `command succeeded` is not enough
- `service started` is not enough
- `port is listening` is not enough
- only claim success when **request + artifact + repeatability** all pass
