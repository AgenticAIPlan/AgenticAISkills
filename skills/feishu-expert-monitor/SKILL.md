---
name: feishu-expert-monitor
description: Use when building or maintaining a Feishu Bitable workflow that monitors public statements from government, ministries, think tanks, universities, and authoritative media, then writes clean expert and statement records with clickable links, source tags, priority labels, and expert aggregation.
---

# Feishu Expert Monitor

Use this skill when the task is to operate or extend a Feishu expert-monitoring base.

## Scope

- Rebuild a Feishu Bitable so there are no blank columns, numbering starts from `NO.001`, and links are clickable.
- Normalize imported statement data, including fixing mojibake text before writing records.
- Keep three tables aligned: source registry, public statements, and candidate experts.
- Ensure every statement and expert has a source tag and a priority label.
- Aggregate statements by expert and keep the latest unit, title, contact entry, homepage, recent statement, and recommended activity.
- Support a daily 09:00 update flow that only writes when there is new data.

## Workflow

1. Read the workspace schema and current Feishu base token.
2. Repair garbled Chinese text in source data before any scoring or writes.
3. Filter out data older than two years.
4. Score AI/data relevance and map each record to a simple priority.
5. Rebuild or update the Bitable schema with URL fields for all jump links and select fields for source and priority labels.
6. Write statement records and aggregate expert records.
7. Keep the default view ordered from `NO.001` and put the most important columns first.
8. Skip Feishu writes when the run produces no updates.

## Required Outputs

- `来源注册表`
- `公开言论池`
- `候选专家池`

## Field Rules

- Use URL fields for `链接`, `来源链接`, `最新言论链接`, `机构主页`, and `公开联系入口`.
- Use select fields with color for `来源类型标签` and `优先级标签`.
- Keep `ID` as the first visible field in every table.
- Do not leave placeholder blank columns in the final layout.

## References

- Read [references/schema.md](./references/schema.md) when you need the target table layout.
