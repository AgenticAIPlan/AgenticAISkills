# Installation and usage examples

Use this reference when you need a compact checklist for setting up or invoking `cloud-instance-ops`.

## 1. Installation / placement checklist

### Codex
Place the skill directory where Codex can access local skills, or keep it in a workspace and invoke it explicitly if your setup supports local skill loading.

Expected directory shape:

```text
cloud-instance-ops/
├── SKILL.md
├── agents/openai.yaml
├── references/
└── scripts/
```

### OpenClaw / Claude Code
Reuse the same `cloud-instance-ops/` directory as the shared core skill. If your local setup expects a dedicated skills path, copy or symlink the whole folder there rather than splitting files.

## 2. Local prerequisites checklist
- Python 3 available locally
- `ssh` installed for Linux instance operations
- `scp` installed for file transfer / deploy flows
- `aws` CLI installed for AWS EC2 operations
- `aliyun` CLI installed for Aliyun ECS operations
- Existing credential source already configured locally:
  - SSH key / ssh-agent / SSH config
  - AWS profile or environment credentials
  - Aliyun profile or environment credentials
- Optional but common:
  - VPN connectivity
  - bastion / jump host
  - approved IP allowlist

## 3. Recommended invocation sequence
For any new target, prefer this order:

1. Run `preflight.py`
2. If SSH-based, run `ssh_probe.py`
3. Run the smallest real command
4. If the command fails, normalize it with `normalize_result.py`

## 4. Generic Linux examples

### 4.1 Check whether a host is reachable
```bash
python3 scripts/preflight.py \
  --cloud generic \
  --action inspect \
  --host 10.0.0.8 \
  --check-port
```

### 4.2 Probe SSH auth without making changes
```bash
python3 scripts/ssh_probe.py \
  --host 10.0.0.8 \
  --user ubuntu \
  --identity-file ~/.ssh/prod.pem
```

### 4.3 Probe through a bastion
```bash
python3 scripts/preflight.py \
  --cloud generic \
  --action inspect \
  --host 10.0.1.15 \
  --jump-host bastion.example.com \
  --check-port

python3 scripts/ssh_probe.py \
  --host 10.0.1.15 \
  --user ec2-user \
  --identity-file ~/.ssh/prod.pem \
  --jump-host bastion.example.com
```

### 4.4 Normalize a failed SSH result
```bash
python3 scripts/normalize_result.py \
  --exit-code 255 \
  --stderr 'Permission denied (publickey)' \
  --command 'ssh -i ~/.ssh/prod.pem ec2-user@10.0.0.8'
```

## 5. AWS examples

### 5.1 Check local AWS readiness
```bash
python3 scripts/preflight.py \
  --cloud aws \
  --action instance-check \
  --profile prod \
  --region ap-southeast-1
```

### 5.2 Describe an EC2 instance
```bash
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --region ap-southeast-1 \
  --profile prod
```

### 5.3 Reboot an EC2 instance
```bash
aws ec2 reboot-instances \
  --instance-ids i-0123456789abcdef0 \
  --region ap-southeast-1 \
  --profile prod
```

### 5.4 Normalize an AWS auth/session failure
```bash
python3 scripts/normalize_result.py \
  --exit-code 254 \
  --stderr 'SSO login required or session token has expired' \
  --command 'aws ec2 describe-instances --instance-ids i-0123456789abcdef0 --region ap-southeast-1 --profile prod'
```

## 6. Aliyun examples

### 6.1 Check local Aliyun readiness
```bash
python3 scripts/preflight.py \
  --cloud aliyun \
  --action instance-check \
  --profile default \
  --region cn-hangzhou
```

### 6.2 Describe an ECS instance
```bash
aliyun ecs DescribeInstances \
  --RegionId cn-hangzhou \
  --InstanceIds '["i-bp1example123456789"]' \
  --profile default
```

### 6.3 Reboot an ECS instance
```bash
aliyun ecs RebootInstance \
  --RegionId cn-hangzhou \
  --InstanceId i-bp1example123456789 \
  --profile default
```

### 6.4 Normalize an Aliyun permission failure
```bash
python3 scripts/normalize_result.py \
  --exit-code 1 \
  --stderr 'AccessDenied: You are not authorized to perform this action.' \
  --command 'aliyun ecs RebootInstance --RegionId cn-hangzhou --InstanceId i-bp1example123456789 --profile default'
```

## 7. Restricted-access examples

### MFA / SSO / approval known in advance
```bash
python3 scripts/preflight.py \
  --cloud aws \
  --action cloud-op \
  --profile prod \
  --region ap-southeast-1 \
  --restrictions mfa,sso,approval
```

### Read-only access trying a mutating action
```bash
python3 scripts/preflight.py \
  --cloud generic \
  --action restart \
  --host 10.0.0.8 \
  --restrictions read-only
```

### Allowlist or VPN restriction without bastion
```bash
python3 scripts/preflight.py \
  --cloud generic \
  --action inspect \
  --host 10.0.1.15 \
  --restrictions allowlist,vpn \
  --check-port
```

## 8. What not to do
- Do not put secrets into the skill directory.
- Do not treat browser-only console workflows as the default path.
- Do not skip preflight when access constraints are unclear.
- Do not claim success on the basis of assumptions.


## 9. Password SSH examples

### 9.1 Keep the password out of the repo
Preferred sources:
- environment variable for the current shell only
- local secret temp file outside the repo
- secure prompt or desktop secret storage

### 9.2 Minimal `expect` probe pattern
```bash
expect <<'EOF'
log_user 0
set timeout 20
set password $env(CLOUD_INSTANCE_PASSWORD)
spawn ssh -o StrictHostKeyChecking=accept-new ubuntu@122.51.187.199 true
expect {
  -re ".*assword:.*" { send -- "$password\r"; exp_continue }
  eof { catch wait result; exit [lindex $result 3] }
}
EOF
```

## 10. Model deployment examples

### 10.1 Single-run before serving
```bash
python3 scripts/remote_port_owner.py --port 8080
curl -fsS http://127.0.0.1:8080/docs
```

### 10.2 Artifact check
```bash
python3 scripts/artifact_check.py --path /data/exam/output.wav --kind audio --min-size 1024
python3 scripts/artifact_check.py --path /data/exam/result.txt --kind text --min-size 20
```

### 10.3 Final acceptance check
```bash
python3 scripts/deployment_final_check.py   --url http://127.0.0.1:8080/health   --repeat 2   --artifact /data/exam/output.wav   --artifact-kind audio
```
