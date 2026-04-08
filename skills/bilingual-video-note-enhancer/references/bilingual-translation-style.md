# Bilingual Translation Style

## Goal

Produce Chinese that is faithful, readable, and useful for later study.

## Rules

- Preserve technical meaning over spoken filler.
- Keep product and model names in their common English forms when that is clearer.
- Translate process descriptions naturally instead of copying English syntax.
- Keep speaker intent visible when the source is evaluative or comparative.
- Avoid over-polishing into article prose if the original is obviously spoken.

## Terminology

- `TL;DR` may stay as `TL;DR` in headings or labels.
- `agent`, `workflow`, `sandbox`, `prompt`, `tool call`, `spec`, `TDD` may remain in English when they are the common term in context.
- Translate the explanation around these terms into natural Chinese.

## Segment Handling

- Short utterances can be translated with short Chinese lines.
- Long spoken paragraphs may be compressed lightly if repetition does not add meaning.
- Do not omit claims, comparisons, or caveats.

## Anti-Patterns

- Do not prefix translations with `译文：`.
- Do not produce literal word-by-word Chinese when it becomes awkward.
- Do not summarize when the user asked for translation.
