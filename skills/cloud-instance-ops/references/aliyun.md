# Aliyun ECS operations

Use this reference when the request targets Alibaba Cloud ECS.

## Prerequisites
- Local `aliyun` CLI is installed.
- Credentials come from an existing Aliyun profile, environment variables, or local CLI config.
- Do not create or persist AccessKey material in the repo.

## Preferred read-only commands
```bash
aliyun ecs DescribeInstances --RegionId <region> --InstanceIds '["<instance-id>"]' [--profile <profile>]
aliyun ecs DescribeInstanceStatus --RegionId <region> --InstanceId.1 <instance-id> [--profile <profile>]
```

## Common lifecycle commands
```bash
aliyun ecs StartInstance --RegionId <region> --InstanceId <instance-id> [--profile <profile>]
aliyun ecs StopInstance --RegionId <region> --InstanceId <instance-id> [--profile <profile>]
aliyun ecs RebootInstance --RegionId <region> --InstanceId <instance-id> [--profile <profile>]
```

## Guidance
- Prefer ECS CLI/API for start/stop/reboot when instance lifecycle state matters.
- If the request is blocked by RAM policy, financial lock, or missing approval, stop and return a structured handoff.
- If the CLI reports authentication problems, MFA-like interactive login, or missing profile setup, return `needs_user`.
- Treat disk reset, image replacement, security group mutation, and public exposure changes as confirmation-required.

## Source notes
These command names align with the official Aliyun ECS CLI/API documentation for `DescribeInstances`, `DescribeInstanceStatus`, `StartInstance`, `StopInstance`, and `RebootInstance`.
