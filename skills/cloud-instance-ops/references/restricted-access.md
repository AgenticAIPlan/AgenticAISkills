# Restricted access diagnosis

Use this reference to map access symptoms to a stable response.

## Status mapping
- `ok`: the required local preconditions and command/probe succeeded
- `blocked`: a technical path exists in principle, but the current environment cannot reach or use it
- `denied`: the current identity lacks permission for the requested mutating action
- `needs_user`: a human must complete MFA, SSO, captcha, approval, or another interactive step
- `unsupported`: the requested environment or tooling is outside this skill's supported scope

## Symptom → status
- `Permission denied (publickey)` with no valid key path: `blocked`
- `Connection timed out`, `No route to host`, allowlist miss, private endpoint only: `blocked`
- `AccessDenied`, `UnauthorizedOperation`, RAM deny: `denied`
- `SSO login required`, `MFA required`, approval/captcha prompt: `needs_user`
- Missing `aws`, `aliyun`, or `ssh` binary when the task depends on it: `unsupported`

## Handoff language patterns
- **blocked**: explain the missing path or dependency, then name the smallest next step
- **denied**: name the permission boundary and the exact action that needs approval
- **needs_user**: say which interactive step is required and stop
- **unsupported**: say what this skill supports and what is out of scope

## Example next steps
- "Run the approved SSO login flow for the `prod` profile, then retry the command."
- "Provide the bastion hostname or connect this machine to the required VPN."
- "Ask for `ec2:RebootInstances` or `ecs:RebootInstance` on the target instance before retrying."
- "Install the required CLI locally, then rerun preflight."
