---
name: cloud-instance-ops
description: Use for cloud instance access diagnosis and SSH/CLI-first operations in Codex, OpenClaw, or Claude Code when the task centers on Linux server access, password or key based SSH, file transfer, service or process checks, log inspection, AWS EC2 or Aliyun ECS inspection, or diagnosing blockers such as bastions, MFA, SSO, IP allowlists, approvals, and read-only permissions. Only extend into deployment, API serving, or cloud-side mutating actions when the user explicitly asks for them.
---

# Cloud Instance Ops

## Overview
Use this skill to manage cloud servers and instances like a careful human operator **within the current authorization boundary**. Prefer SSH and official cloud CLIs. Do **not** try to bypass MFA, SSO, approval workflows, captchas, IP allowlists, bastions, or least-privilege controls.

This skill is optimized for a shared core workflow that can be reused in Codex, OpenClaw, and Claude Code. Codex-specific UI metadata lives in `agents/openai.yaml`; the operational logic stays in this `SKILL.md` plus the bundled references and scripts.

## Use this skill when
- You need to connect to a Linux instance through SSH, password SSH, `ProxyJump`, or a bastion.
- You need file transfer, service/process checks, log inspection, restart operations, or access troubleshooting on an existing instance.
- You need AWS EC2 or Aliyun ECS instance inspection or other cloud-side checks through the official CLI.
- You need to deploy a model, stand up an API, validate output artifacts, or run cloud-side mutating actions **and the user has explicitly asked for that path**.

## Required inputs
Normalize each request into these five inputs before acting:
1. **Target object**: host/IP, instance ID, region, environment, bastion
2. **Cloud environment**: generic Linux, AWS, or Aliyun
3. **Authentication method**: SSH key, password SSH, agent, AWS profile, Aliyun profile, short-lived token, SSO
4. **Restrictions**: MFA, approval, allowlist, no public route, read-only, captcha, missing CLI, shared GPU/port use
5. **Requested action**: connect, transfer, inspect, logs, restart, deploy, single-run, serve, accept, instance-check, cloud-op

Treat `deploy`, `single-run`, `serve`, `accept`, and `cloud-op` as explicit-action modes. Do not enter them from a vague “帮我看看机器” style request without confirming intent from the user prompt or environment.

If an input is missing, infer it from the environment first. Ask the user only for the minimum missing detail.

## Core operating model

### 1. Preflight
Run a lightweight local check before attempting privileged or remote work.

Typical commands:

```bash
python3 scripts/preflight.py --cloud generic --action inspect --host 10.0.0.8 --check-port
python3 scripts/preflight.py --cloud aws --action instance-check --profile prod --region ap-southeast-1
python3 scripts/preflight.py --cloud aliyun --action cloud-op --profile default --region cn-hangzhou
```

Preflight should verify only what is safe to verify locally:
- required binaries exist
- obvious credential sources exist
- referenced files exist
- target port is reachable when requested
- explicit restrictions imply `blocked`, `denied`, or `needs_user`

### 2. Execution
Use the narrowest command that answers the request.
- Prefer read-only checks before mutating actions.
- Prefer official cloud CLI for cloud-level state changes.
- For instance lifecycle operations on EC2/ECS, prefer provider CLI/API over in-guest reboot when cloud state matters.

Useful wrappers:

```bash
python3 scripts/ssh_probe.py --host 10.0.0.8 --user ec2-user --identity-file ~/.ssh/prod.pem
python3 scripts/remote_port_owner.py --port 8080
```

### 3. Restriction handling
If the environment requires human involvement, stop and return a structured handoff instead of guessing.

Common stop conditions:
- MFA / SSO / captcha required
- explicit approval required
- IP allowlist or private-network-only path not yet satisfied
- read-only permission for a mutating action
- missing cloud CLI or profile
- SSH key or bastion path unavailable
- shared port/GPU is still occupied by another workload

### 4. Handoff
Return a stable contract for both success and blocked cases so the result can be reused in later handoff, approval, or postmortem steps.

Minimum success shape:

```json
{
  "status": "ok",
  "action": "inspect",
  "target": "10.0.0.8",
  "evidence": {
    "network": {"10.0.0.8:22": "open"}
  },
  "next_step": "Proceed with the requested read-only inspection."
}
```

When blocked, return a concrete next step instead of guessing.

Expected shape:

```json
{
  "status": "blocked",
  "reason": "Target port 22 is unreachable from the current machine.",
  "next_step": "Connect through the approved bastion or ask for the current IP to be allowlisted.",
  "evidence": {
    "network": {"10.0.0.8:22": "closed"}
  }
}
```

Allowed `status` values:
- `ok`
- `blocked`
- `denied`
- `needs_user`
- `unsupported`

## Model deployment workflow
Use this workflow whenever the task is “部署模型 / 起 API / 做题面验收 / 输出文件检查” instead of plain server ops.

### Principle: single-run before serving
Always verify the underlying model or command **once** before wrapping it in an API. Do not start with service orchestration unless the user explicitly asks for service-first diagnosis.

### Recommended sequence
1. **Read-only preflight**: model path, input path, GPU/CPU, memory, ports, dependency versions, existing services
2. **Single-run check**: run one minimal inference locally or remotely and verify the base pipeline works
3. **Service deployment**: only after single-run succeeds, expose HTTP/API/worker entrypoint
4. **Example-request acceptance**: rerun the exact original `curl` or request shape from the task prompt
5. **Output artifact check**: confirm files exist, size is reasonable, type matches expectation, contents are not obviously broken
6. **Repeated-request stability**: repeat at least once to catch cold-start-only success or stale previous services

### Final acceptance checklist
Do not claim “deployed successfully” until all applicable checks pass:
- health check or docs endpoint check
- original example request check
- output artifact check
- repeated request stability check
- service log sanity check

Use the bundled scripts when helpful:

```bash
python3 scripts/remote_service_check.py --url http://127.0.0.1:8080/docs
python3 scripts/artifact_check.py --path /data/exam/output.wav --kind audio
python3 scripts/deployment_final_check.py --url http://127.0.0.1:8080/health --repeat 2
```

## Shared runtime hygiene
In exam, benchmark, and shared-machine environments, assume the host may already have leftovers.

Before reusing a port, GPU, or task directory:
- identify the current port owner
- identify old model/server processes
- verify the endpoint is serving the intended workload, not a stale process
- verify the current environment has enough free memory/disk/GPU for the next task

Never assume “service started” means “new service is handling requests”. Always verify the response path.

## Environment isolation
Prefer one environment per task (`venv` or `conda`). If isolation is impossible:
- record key dependency versions before installation
- assess whether new packages may break existing services
- avoid in-place upgrades of shared production environments unless the user explicitly accepts the risk

## Password SSH guidance
Password SSH is common in exam or public-IP environments. Use it carefully:
- prefer secrets from environment variables, local temp files, or secure prompts
- never write passwords into the repo, shell history, or final logs
- distinguish network failure, host key issues, wrong password, and server-side auth restrictions
- when automation is needed, use the smallest possible `expect` or similar wrapper and keep logs password-free

## Interrupted run recovery
When the task was interrupted, never restart blindly. First check:
1. residual processes
2. listening ports
3. output file timestamps and sizes
4. last service logs
5. whether to resume or rebuild

If artifacts and downloads are already present, prefer resume. If state is ambiguous or contaminated, clean and restart only the affected slice.

## Remote script layout
For longer remote tasks, prefer a predictable work layout such as:
- `01_single_run.py`
- `02_api.py`
- `03_start.sh`
- `04_selftest.sh`
- `*.log`
- `*.pid`

Keep logs, PID files, and outputs in one task directory so interrupted runs are easy to inspect.

## Guardrails
- Never store secrets, tokens, or private keys in the repo.
- Never claim success unless a command or probe actually succeeded.
- Never attempt to bypass MFA, SSO, approval, captcha, or network policy.
- Never execute destructive or high-blast-radius actions without explicit confirmation.
- For deployment tasks, never claim success based only on “command exited 0”; validate the artifact or endpoint.

### Confirmation required
Treat these as confirmation-required even if technically possible:
- terminating or releasing an instance
- resetting or recreating disks, snapshots, images, or security groups
- firewall/public exposure changes
- forced restart/stop that may cause downtime
- any action outside the user’s stated target environment

## References
Load only the reference relevant to the current task:
- Generic Linux and SSH patterns: `references/generic-linux.md`
- AWS EC2 patterns: `references/aws.md`
- Aliyun ECS patterns: `references/aliyun.md`
- Restriction diagnosis and handoff language: `references/restricted-access.md`
- Installation and invocation checklist: `references/install-and-examples.md`
- Model deployment workflow and acceptance: `references/model-deployment.md`
- Shared runtime hygiene and environment isolation: `references/shared-runtime-hygiene.md`
- Interrupted-run recovery patterns: `references/interrupted-run-recovery.md`

## Scripts
- `scripts/preflight.py`: local preflight checks and initial status classification
- `scripts/ssh_probe.py`: non-destructive SSH connectivity/auth probe with optional bastion
- `scripts/normalize_result.py`: normalize command outcomes into the shared status contract
- `scripts/remote_port_owner.py`: inspect which local process is listening on a port
- `scripts/artifact_check.py`: verify output artifacts exist and look reasonable
- `scripts/deployment_final_check.py`: verify health/example endpoints and optional artifacts with repeat checks
