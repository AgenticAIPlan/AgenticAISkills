# Obsidian Note Shape

Use these rules when enhancing an existing note instead of drafting from scratch.

## Placement

- Keep the original title.
- Place the Chinese TL;DR immediately after the title.
- For video notes, default to only the TL;DR. Do not add extra `abstract`, `info`, `note`, or `Key Takeaways` blocks unless the user explicitly wants them.
- Do not move the main timestamp guide unless the user asks for restructuring.
- Keep embeds at the section they semantically belong to.
- If one section covers multiple visual ideas, multiple embeds in the same section are allowed.

## Frontmatter

- Preserve existing frontmatter fields.
- Update `updated` when the note content changes materially.
- Update `processed_at` when the note is reprocessed end to end.
- Do not invent new frontmatter fields unless the vault already uses them nearby.

## Markdown Style

- Preserve existing heading levels.
- Keep Obsidian embeds in place unless the filename changes.
- Prefer plain paragraphs over heavy callout nesting.
- Use wikilinks only for in-vault notes. Keep external URLs as Markdown links.

## Bilingual Layout

- English source first, Chinese immediately after.
- Keep the Chinese translation as plain text unless the note already wraps translation blocks in a special pattern.
- Do not insert `译文：`.
