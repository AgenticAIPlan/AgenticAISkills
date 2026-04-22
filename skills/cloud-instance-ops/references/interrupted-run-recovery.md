# Interrupted run recovery

Use this reference when the user switched threads, interrupted commands, or the desktop session was closed.

## Recovery checklist
1. check residual processes
2. check listening ports
3. check output file timestamps and sizes
4. check service logs and last error
5. decide whether to resume or rebuild

## Prefer resume when
- downloads are still in progress or already complete
- artifacts exist and look current
- the service is still running and healthy
- the environment is otherwise clean

## Prefer rebuild when
- the port is occupied by an unknown process
- the environment is clearly contaminated
- output files are stale or mismatched
- logs show repeated crash loops from corrupted state

## Minimal commands to inspect first
```bash
ps -ef | grep -E 'service_name|python|node' | grep -v grep
ss -tulpn | grep ':8080 '
ls -lh <artifact>
tail -n 200 <service.log>
```

## Recovery claim rules
Never say "we can resume" without evidence. Never say "clean restart required" without identifying the stale state.
