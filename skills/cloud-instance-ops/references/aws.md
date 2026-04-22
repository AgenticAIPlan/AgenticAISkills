# AWS EC2 operations

Use this reference when the request targets AWS EC2 or related instance diagnostics.

## Prerequisites
- Local `aws` CLI is installed.
- Credentials come from an existing profile, environment variables, or the local AWS config/credentials files.
- Do not create or persist credentials in the repo.

## Preferred read-only commands
```bash
aws ec2 describe-instances --instance-ids <instance-id> --region <region> [--profile <profile>]
aws ec2 describe-instance-status --instance-ids <instance-id> --region <region> [--profile <profile>]
```

## Common lifecycle commands
```bash
aws ec2 start-instances --instance-ids <instance-id> --region <region> [--profile <profile>]
aws ec2 stop-instances --instance-ids <instance-id> --region <region> [--profile <profile>]
aws ec2 reboot-instances --instance-ids <instance-id> --region <region> [--profile <profile>]
```

## Guidance
- Prefer EC2 CLI/API for start/stop/reboot when cloud-level instance state matters.
- If the command fails with SSO, MFA, or expired credentials, return `needs_user` and tell the user to refresh the session.
- If the command fails with `UnauthorizedOperation` or `AccessDenied`, return `denied`.
- Avoid terminate, security group mutation, EBS replacement, or AMI/image changes unless explicitly requested and confirmed.

## Source notes
These command names align with the official AWS CLI EC2 references for `describe-instances`, `describe-instance-status`, `start-instances`, `stop-instances`, and `reboot-instances`.
