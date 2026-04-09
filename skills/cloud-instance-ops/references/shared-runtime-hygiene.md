# Shared runtime hygiene

Use this reference for reused machines, shared GPUs, repeated exam tasks, or mixed workloads.

## Port hygiene
Before binding a port:
- identify the current owner (`ss -tulpn`, `lsof`, or `fuser`)
- confirm the currently responding endpoint is the intended service
- avoid false success where an old service still answers new requests

## GPU / accelerator hygiene
Before launching a new model:
- check device occupancy and memory use
- identify stale inference servers
- free only the processes relevant to the current task
- do not assume "GPU present" means "GPU available"

## Dependency isolation
Prefer one `venv` or `conda` env per task. If not possible:
- snapshot key versions first
- avoid broad upgrades in shared environments
- expect packages like `transformers`, `diffusers`, `opencv`, `pydantic`, and inference runtimes to conflict

## Script / file layout
For remote task directories, prefer stable naming:
- `01_single_run.py`
- `02_api.py`
- `03_start.sh`
- `04_selftest.sh`
- `service.log`
- `service.pid`
- `outputs/`

## Cleanup rules
Clean only what you can attribute.
- stop the old service by PID or unit name
- remove stale PID files only after verifying the process is gone
- keep logs until acceptance is complete
