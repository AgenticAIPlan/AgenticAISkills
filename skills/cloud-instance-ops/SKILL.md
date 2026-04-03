---
name: cloud-instance-ops
description: Use for SSH/CLI-first cloud instance operations in Codex, OpenClaw, or Claude Code when the task involves Linux server access, file transfer, service or process management, deployment, log triage, AWS EC2 or Aliyun ECS inspection, or diagnosing access blockers such as bastions, MFA, SSO, IP allowlists, approvals, and read-only permissions.
---

# Cloud Instance Ops

## Overview
Use this skill to manage cloud servers and instances like a careful human operator **within the current authorization boundary**. Prefer SSH and official cloud CLIs. Do **not** try to bypass MFA, SSO, approval workflows, captchas, IP allowlists, bastions, or least-privilege controls.

This skill is optimized for a shared core workflow that can be reused in Codex, OpenClaw, and Claude Code. Codex-specific UI metadata lives in `agents/openai.yaml`; the operational logic stays in this `SKILL.md` plus the bundled references and scripts.

## Use this skill when
- You need to connect to a Linux instance through SSH, `ProxyJump`, or a bastion.
- You need file transfer, service/process checks, log inspection, deployment, or restart operations.
- You need AWS EC2 or Aliyun ECS instance inspection or routine lifecycle actions through the official CLI.
- You must explain why access is blocked and tell the user exactly what they need to do next.

## Required inputs
Normalize each request into these five inputs before acting:
1. **Target object**: host/IP, instance ID, region, environment, bastion
2. **Cloud environment**: generic Linux, AWS, or Aliyun
3. **Authentication method**: SSH key, agent, AWS profile, Aliyun profile, short-lived token, SSO
4. **Restrictions**: MFA, approval, allowlist, no public route, read-only, captcha, missing CLI
5. **Requested action**: connect, transfer, inspect, logs, restart, deploy, instance-check, cloud-op

If an input is missing, infer it from the environment first. Ask the user only for the minimum missing detail.

## Operating model

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

Useful wrapper:

```bash
python3 scripts/ssh_probe.py --host 10.0.0.8 --user ec2-user --identity-file ~/.ssh/prod.pem
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

### 4. Handoff
When blocked, return a stable contract and a concrete next step.

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

## Guardrails
- Never store secrets, tokens, or private keys in the repo.
- Never claim success unless a command or probe actually succeeded.
- Never attempt to bypass MFA, SSO, approval, captcha, or network policy.
- Never execute destructive or high-blast-radius actions without explicit confirmation.

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

## Scripts
- `scripts/preflight.py`: local preflight checks and initial status classification
- `scripts/ssh_probe.py`: non-destructive SSH connectivity/auth probe with optional bastion
- `scripts/normalize_result.py`: normalize command outcomes into the shared status contract
