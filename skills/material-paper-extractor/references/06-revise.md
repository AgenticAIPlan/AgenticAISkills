# Revision Prompt

## Output Path
**Must save to:** `{output_base}/06_revise/{id}_revised.json` (strictly valid JSON — no markdown fences, no comments)

## Purpose

Revise the extraction results based on the critical review. Produce the final validated JSON.

## Input

You will receive:
1. Original combined text (from Step 2)
2. Extraction prompts (system + user prompts from Step 3)
3. Validated extraction results JSON (from Step 4, after script validation)
4. Critical review report (from Step 5)

## Revision Process

### 1. Address Critical Issues
For each 🔴 Critical and 🟠 High severity issue:
- Go back to the source text to find the correct value
- Correct the extraction
- Document what was changed

### 2. Incorporate Medium Issues
For 🟡 Medium issues:
- Evaluate if correction is warranted
- If yes, make the correction
- If no (false positive), explain why and keep original

### 3. Review Low Issues
For 🟢 Low suggestions:
- Apply if they improve clarity without changing meaning
- Reject if they alter data fidelity

### 4. Re-check Integrity
After revisions:
- Verify JSON syntax remains valid
- Ensure all required fields are present
- Check physical constraints (YS ≤ UTS, Elongation ≤ 100%)
- Verify composition sums to ~100% (±1 tolerance)
- Verify Main_Phase does not contain Laves/Carbides (prohibited)
- Verify Relative_Density_pct is not hallucinated
- Verify temperature isolation (test temps only in Test_Temperature_K)
- Verify heat treatment ranges are NOT averaged
- Verify compressive properties have `_Compressive` suffix
- Verify three-way elongation distinction is correct

## Output

**IMPORTANT: Output MUST be written to exactly this path:**
`{output_base}/06_revise/{id}_revised.json`

The file must be **strictly valid JSON**:
- No markdown fences (no ` ```json ` / ` ``` ` wrappers)
- No conversational text before or after
- **No JSON comments** — standard JSON does not permit `/* ... */` or `//` comments
- Start from `{` and end cleanly at the closing `}`

Use the Write tool to save the file. Do NOT use bash heredocs for JSON with non-ASCII content.

## Schema Reference

See `references/03-extract-system-prompt.md` Section VII for the authoritative schema. The revised JSON must match that schema exactly — same field names, same nesting, same nullability rules.

## Revision Notes (Separate Sidecar File)

**Do NOT embed comments inside the JSON file.** Standard JSON does not allow `/* ... */` or `//` comments, and the pipeline's downstream tools require strictly valid JSON.

Instead, write a brief change log to this separate sidecar file:

**Path:** `{output_base}/06_revise/{id}_revision_notes.md`

**Format:**

```markdown
# Revision Notes for {id}

## Summary
- Total issues addressed: N
- Errors corrected: N
- Warnings reviewed: N

## Item-by-Item Changes
- Item 1 ({Sample_ID}): [what was corrected and why]
- Item 2 ({Sample_ID}): [what was corrected and why]

## Unchanged (False Positives)
- [Any review findings you deliberately did not act on, with justification]
```

The sidecar file is optional documentation; the `{id}_revised.json` file is the authoritative artifact and is what Step 7 / Step 8 will consume.
