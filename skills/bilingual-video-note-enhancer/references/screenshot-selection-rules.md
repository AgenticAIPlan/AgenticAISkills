# Screenshot Selection Rules

## Preferred Frame Order

Choose the most informative frame in this order:

1. Full slide with legible title and bullets
2. Diagram, workflow, chart, or code frame
3. Title page or section separator page
4. Partially obstructed content page
5. Speaker plus clearly legible projected content
6. Speaker-only frame

For talk videos, lectures, webinars, and conference recordings, assume the slide deck, worksheet, code demo, or whiteboard is the information-bearing target unless the note is explicitly about the speaker's delivery, body language, or physical demonstration.

## Capture Strategy

- Default to `yt-dlp + local clip + local frame selection`.
- Prefer 8-second high-resolution clips for normal timestamp work.
- For short videos with many timestamps, downloading the whole video first can be simpler and more stable than repeated segment fetches.
- Treat browser capture as fallback only when local video extraction is not workable.

## Window Strategy

- Start with an 8-second window around the target timestamp.
- If that window contains only speaker shots, widen to 20-30 seconds.
- Prefer the nearest content page that matches the section topic over an exact but low-information shot.
- If the default timestamp lands on a talking-head shot but the nearby window contains a legible PPT, handout, benchmark table, or diagram, choose the content frame instead of preserving the speaker shot.

## Fast-Switching Sections

- If a long transcript block spans several slides or demos, do not collapse it to one image by default.
- Insert multiple screenshots when the visuals carry distinct meaning.
- Use additional screenshots for page turns that introduce a new chart, pipeline, demo state, or conclusion.
- Keep each screenshot near the sentence it best supports.
- In the final note, anchor each screenshot to the nearest timestamp block or subtopic it explains. Avoid putting all screenshots at the top of the section before the reader reaches the relevant text.
- Do not let a speaker-only frame become the primary image for a section when the section is really about the changing slides.

## Review Process

- Build contact sheets from local clips before choosing final frames.
- For screenshot validation, start subagents in parallel to review timestamp windows or candidate sheets, then merge their picks in the main thread.
- Ask each subagent to optimize for semantic fit and readability, not just timestamp proximity.

## Export Rule

- Select on a local clip.
- Export from that same local clip.
- Do not re-seek the original remote stream after selection.

## Bookkeeping

- Back up replaced screenshots when there are original local assets worth preserving.
- Keep output filenames stable when possible so note embeds do not need edits.
- Record the chosen window, frame number, and extract time in a JSON map.
