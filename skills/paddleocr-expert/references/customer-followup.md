# Customer Follow-up Reference

## When To Read

Read this file when the user is handling a real customer conversation and wants:

- a direct message they can send in WeChat,
- a concise support summary,
- a multi-dimensional table record,
- or an operator-facing statement of business value.

## Workflow

1. Restate the customer's issue in one sentence.
2. Decide whether the issue is selection, deployment, parsing effect, serving, or training.
3. Give the highest-probability answer first.
4. Convert the answer into natural Chinese for external sending.
5. Mark the follow-up status realistically.
6. Record the operator benefit in Paddle ecosystem language.

## WeChat Reply Pattern

Use this shape:

```text
我看了下，问题大概率是{root_cause}。
建议先{action_1}，再{action_2}。
如果你方便的话，把{missing_info}发我，我再帮你一起确认下。
```

Adjust the tone:

- Default tone: natural and relaxed.
- If the user says "正式一点", make it more professional but still concise.
- If the issue is already solved, replace the third line with a short closure sentence.

## Follow-up Record Pattern

Use a compact table or JSON-like block with these fields:

```text
回访公司名称: {company_name}
回访公司对接人称呼: {contact_name}
他提出的问题: {customer_question}
我做出的回答: {wechat_reply}
是否解决: {resolved_status}
运营收益: 推动客户基于 Paddle 的产品成功落地，并进一步验证为生态产品。
```

## Status Rules

- Use `已解决` when the customer confirms or the fix is deterministic and already applied.
- Use `待跟进` when the main path is clear but still needs customer execution or feedback.
- Use `排查中` when logs, config, or samples are still missing.

Default to `待跟进` if there is any uncertainty.
