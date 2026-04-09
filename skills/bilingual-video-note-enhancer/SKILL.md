---
name: bilingual-video-note-enhancer
description: Enhance existing English Obsidian video notes, transcript notes, timestamped study notes, or article-like notes into compact bilingual study notes. Make sure to use this skill whenever the user wants an existing note enhanced with a Chinese TL;DR near the top, Chinese translations directly below English source blocks, or clearer timestamp screenshots and visual inserts. Trigger for requests such as “双语笔记”, “中英对照”, “中文 TL;DR”, “逐段翻译”, “英文笔记增强”, or “把截图换清晰”, even if the user does not explicitly mention YouTube or screenshots, as long as the task is to upgrade an existing note rather than draft a brand-new note from scratch.
---

# Bilingual Video Note Enhancer

Enhance an English video note into a bilingual Obsidian note that stays readable, compact, and visually useful. Keep the original English source, add a concise Chinese TL;DR near the top, insert Chinese translations directly under the corresponding English blocks, and replace weak screenshots with readable content frames.

Default to Obsidian-compatible Markdown and stable asset handling. Preserve the note's existing structure unless the user explicitly asks for a larger rewrite.

## Preserve Note Identity

Do not invent a new free-form title for the note unless the user explicitly asks for retitling.

Title rules:
- Preserve the existing note title by default.
- Do not append generic suffixes such as `- transcript note`, `- bilingual note`, or similar machineish labels.
- If the source title is obviously a temporary placeholder and the user wants cleanup, normalize it to the simplest stable topic title rather than a descriptive sentence.

## Workflow

1. Read the target note.
2. Detect frontmatter, section headings, timestamp guide, transcript layout, and image embeds.
3. Decide whether the note is:
- a video note with timestamps and screenshots
- a transcript note with timestamps but no screenshots
- an English article-like note that still needs bilingual enhancement

## Choose Enhancement Mode

Pick the lightest mode that fully satisfies the task. Do not automatically enter the screenshot workflow just because the note contains timestamps.

- **Translation-only mode**: Use when the user wants Chinese TL;DR plus paragraph-level translation, and the note either has no screenshots or does not need visual upgrades.
- **Screenshot-refresh mode**: Use only when the note already contains screenshot embeds, the screenshots are weak, or the user explicitly asks for better visual inserts.
- **Article-note mode**: Use when the note is article-like or transcript-lite and should gain bilingual enhancement without being forced into a video-note structure.
- **Fallback mode**: Use when screenshot work would normally be relevant but local video tooling, source clips, or parallel review support are unavailable. In that case, still complete the bilingual note enhancement and preserve existing embeds rather than inventing fake screenshot updates.

Mode rules:
- If the task can be completed well with TL;DR + translation only, stop there.
- Do not invent screenshot work for article-like notes.
- Do not convert an existing note into a brand-new layout unless the user explicitly asks for a larger rewrite.

## Minimum Inputs

Choose the lightest path that the available materials can actually support.

- **Translation-only mode** and **Article-note mode** require only the target note path or note content. Existing screenshots, video URLs, or local clips are optional and should not be requested just because timestamps are present.
- **Screenshot-refresh mode** requires the target note plus at least one reusable visual source that covers the needed timestamps: the original video URL, a local video file path, or an existing local clip or asset directory.
- If the note has timestamps but no accessible video URL, local video file, or reusable clip assets, do not start the screenshot workflow. Stay in Translation-only mode or Fallback mode and preserve the existing embeds.
- If the user explicitly wants screenshot upgrades but cannot provide a usable visual source, say the screenshot path is blocked and still complete the bilingual enhancement without fabricating new frames.

## Add Chinese TL;DR

Add a short Chinese summary near the top of the note after the title.

Default output for YouTube or video notes:
- Add only the Chinese TL;DR.
- Do not add extra `abstract`, `info`, `note`, or `Key Takeaways` blocks unless the user explicitly asks for them or the note already depends on that structure.
- Prefer 3 to 5 concise bullets or one short paragraph, whichever matches the note better.

TL;DR requirements:
- Summarize the whole piece, not only the opening.
- Prefer concrete takeaways over vague praise.
- Keep terminology consistent with the body translation.

Read [references/obsidian-note-shape.md](references/obsidian-note-shape.md) if you need note placement rules.

## Insert Chinese Translations

Insert each Chinese translation directly below the English source block it translates.

Translation rules:
- Do not prefix the Chinese block with `译文：`.
- Preserve timestamps, speaker cues, and section headings.
- Keep the English source intact unless the user asked for cleanup.
- Translate faithfully, but compress obvious filler words when the spoken English is repetitive.
- Keep product, model, and tool names in their conventional forms.

If the note already uses a pattern like:

```md
**12:30** · English source paragraph
```

then produce:

```md
**12:30** · English source paragraph

对应中文译文段落
```

Read [references/bilingual-translation-style.md](references/bilingual-translation-style.md) for style rules and consistency checks.

## Upgrade Screenshots

Use this section only when the note has timestamp screenshots or the user explicitly wants visual inserts.

Before starting screenshot work, check these preconditions:
- The note actually contains screenshot embeds or clearly needs visual inserts.
- A reusable visual source is available: `yt-dlp` against the source URL works, a local video file exists, or an existing local clip or asset directory can be reused for the target timestamps.
- There is enough support to review candidate frames well. Prefer parallel subagents when available, but do not block the whole task if they are unavailable.

Default screenshot workflow:
1. Build a timestamp list from the note.
2. Use `yt-dlp` to download a short high-resolution local clip for each timestamp, or download the full video first when the source is short and local re-seeking is simpler.
3. Generate a contact sheet from the local clip.
4. Prefer parallel subagents to review candidate contact sheets and identify the best content frames.
5. If subagents are unavailable, review the contact sheets in the main thread and explicitly treat that as a fallback path with lower confidence.
6. Review the returned picks locally and confirm the frame that best represents each section topic.
7. Export the final image from that same local clip.
8. Replace the existing image file in place or create a stable new asset path.
9. Write or update a frame map JSON in `output/<topic>-<date>/`.

Preferred scripts:
- `scripts/extract_video_segments.sh`
- `scripts/build_contact_sheet.sh`
- `scripts/export_selected_frame.sh`
- `scripts/update_frame_map.py`

Selection policy:
- Prefer slide, diagram, workflow, code, title page, or clearly legible UI over speaker-only frames.
- For YouTube talks, lectures, and recorded presentations, projected PPT or handout content is usually the primary target. Treat speaker-only shots as low-value unless the speaker's physical action is itself the thing being explained.
- If the narrow timestamp window contains only speaker shots, expand the search to the nearest content page.
- Optimize for semantic fit first and exact timestamp match second.
- If no clean content frame exists after widening the search, mark the section as a true boundary case and keep the nearest semantically relevant frame.
- Browser screenshots are a fallback only. They are more expensive, more fragile, and more likely to include player chrome.

Critical rules:
- Once a frame is chosen from a local clip, export the final PNG from that same clip.
- Do not re-seek the original stream by absolute time after selection, because that can drift to a different shot.
- Screenshot review is not optional for multi-section video notes, but parallel subagents are a preferred implementation detail rather than a hard requirement. If subagents are unavailable, do the review in the main thread and say that the selection used the fallback path.

## Fallback Rules

When the ideal workflow is blocked, degrade gracefully instead of fabricating work.

- If `yt-dlp`, `ffmpeg`, or a usable local video source is unavailable, skip screenshot replacement and continue with TL;DR + translation enhancement.
- If the note already has embeds and screenshot replacement cannot be done safely, preserve the existing embeds in place.
- Do not claim that screenshots were upgraded if you only preserved the originals.
- Do not create or update a frame map unless screenshot selection actually happened.
- If screenshot review had to be done without subagents, keep the best available local review path and note that this was a fallback rather than the preferred review method.

## Handle Fast-Switching Visual Sections

Some videos flip through many informative slides while the transcript stays in one long spoken block.

When that happens:
- Do not force one screenshot per heading or one screenshot per timestamp.
- If one transcript block covers several materially different visuals, insert multiple screenshots within that section.
- Place each screenshot immediately above or below the timestamp block, sentence, or subtopic it best supports. Do not dump all related screenshots at the top of the section and make the reader guess which text they belong to.
- Prefer 2 to 4 screenshots for a long, dense section instead of one blurry or semantically overloaded image.

Signals that a section needs multiple screenshots:
- the spoken block is long and spans multiple concepts
- the contact sheet shows several distinct content pages with real information
- one screenshot cannot represent the section without losing important visual context

Read [references/screenshot-selection-rules.md](references/screenshot-selection-rules.md) for the detailed heuristics.

## Update Note Metadata

If the vault or repository uses frontmatter timestamps such as `updated` or `processed_at`, refresh them when the note was materially changed.

Do not rewrite unrelated frontmatter fields.

## Validation Checklist

Before finishing, verify:
- The Chinese TL;DR is present near the top.
- No extra summary callout blocks were added for video notes unless the user asked for them.
- Every translated Chinese block sits directly under its English source block.
- No Chinese block starts with `译文：`.
- Image embeds still resolve.
- Replaced screenshots are readable at normal Obsidian note width.
- Fast-switching sections use multiple screenshots when one image is not enough.
- Inserted screenshots sit next to the timestamp block or subtopic they illustrate, rather than being grouped far away from the relevant text.
- The frame map was created or updated if screenshots were modified.
- If screenshots were not modified because tooling or review support was unavailable, the note still remains structurally valid and no fake frame map was created.
- Screenshot verification used parallel subagents when available, or an explicit fallback review path when they were not.

## Resources

Use the bundled scripts when they fit the task. Adjust them rather than retyping the workflow from scratch.

Read these references only when needed:
- [references/obsidian-note-shape.md](references/obsidian-note-shape.md)
- [references/bilingual-translation-style.md](references/bilingual-translation-style.md)
- [references/screenshot-selection-rules.md](references/screenshot-selection-rules.md)
