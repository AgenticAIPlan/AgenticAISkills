# Interaction Patterns

Use this reference when building the page's behavior.

## Interaction philosophy

The site should reward curiosity without overwhelming the first pass.

That means:

- first glance gives structure
- second glance gives taxonomy
- click gives depth

## Navigation patterns

### Section rail

Desktop navigation works well as a fixed or sticky rail.

Good behavior:

- compact by default
- expands on hover or focus
- keeps section indices visible at all times
- highlights the active section while scrolling

This gives the page a strong spatial memory.

### Mobile section sheet

On small screens, replace the rail with:

- a floating button
- a compact pill
- a bottom sheet or slide-over list of sections

The mobile pattern should preserve the section model, not collapse into a generic hamburger.

## Card interaction patterns

### Preview then commit

Best default behavior:

- hover or focus gives a short preview cue
- click or tap selects the item
- selected item updates a stable detail area

This keeps the layout from jumping too much.

### Detail pane

For medium and large screens, show detail in:

- an adjacent panel
- a sticky side panel
- an inline panel below the active grid

For mobile, prefer:

- accordion expansion
- inline revealed block
- bottom sheet

### Taxonomy chips

Small chips are useful for:

- category labels
- technical domains
- command types
- status or role markers

Keep them small, crisp, and secondary. They should support the content, not dominate it.

## Deep linking

### Baseline

Always provide stable IDs for major sections.

Recommended:

- `#overview`
- `#architecture`
- `#features`
- `#commands`
- `#hidden-capabilities`

Use smooth scrolling and active-state updates.

### Extended state

Only encode local module state into the URL when sharing that state adds value.

Good candidates:

- selected architecture node
- selected feature category
- current tab in a multi-mode explorer

Bad candidates:

- transient hover state
- tiny accordion toggles
- every small UI detail

## Hover patterns

Keep hover subtle.

Good hover treatments:

- +5% to +12% brightness
- slight border emphasis
- faint label reveal
- icon opacity increase
- tiny upward translation only if it does not feel playful

Avoid dramatic scaling and exaggerated glow.

## Motion timings

Strong defaults:

- micro hover: `120ms-180ms`
- panel reveal: `180ms-260ms`
- section entry: `300ms-500ms`
- sheet/modal entry: `220ms-320ms`

Prefer `ease-out` or refined custom curves. Avoid springy motion unless the product already uses it.

## Recommended modules

### Architecture explorer

Overview:

- nodes or folders
- relationship cues
- short hover hint

Reveal:

- selected node detail
- breadcrumb or path context
- related items list

### Feature or tool atlas

Overview:

- categorized cards
- semantic colors
- short labels

Reveal:

- detail pane with explanation, examples, related links, caveats

### Command explorer

Overview:

- command families
- one-line descriptions
- mono labels

Reveal:

- syntax, use case, side effects, examples

### Hidden features block

Overview:

- mystery or low-visibility features
- restrained iconography

Reveal:

- why it matters
- when to use it
- example scenario

## Accessibility notes

Every hover interaction should also respond to:

- focus
- click
- tap

If an item looks interactive, it must be reachable by keyboard and communicate selection clearly.
