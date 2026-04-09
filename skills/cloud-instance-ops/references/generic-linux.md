# Generic Linux / SSH operations

Use this reference for ordinary Linux instance work when SSH is the main control plane.

## Preferred sequence
1. Confirm target, user, network path, and auth source.
2. Probe connectivity before making assumptions.
3. Start with read-only commands.
4. Mutate only after the user has requested the action.
5. Summarize outcome with `status`, `reason`, `next_step`, and `evidence`.

## Common read-only commands
```bash
whoami
hostname
uname -a
id
pwd
ls -la
ps aux
ss -tulpn
systemctl status <service>
journalctl -u <service> -n 200 --no-pager
df -h
free -m
```

## Common safe operational patterns
- Service restart: `sudo systemctl restart <service>`
- Service logs: `journalctl -u <service> -n 200 --no-pager`
- File transfer in: `scp <local> <user>@<host>:<remote>`
- File transfer out: `scp <user>@<host>:<remote> <local>`
- Bastion path: prefer `ssh -J <jump_host> <user>@<host>`

## Stop instead of guessing when
- SSH fails due to `Permission denied`, key mismatch, host key mismatch, or missing bastion
- Port 22 is unreachable or routed only inside a VPC/VPN
- `sudo` prompts for an unavailable password
- The requested action is destructive or affects uptime without confirmation
