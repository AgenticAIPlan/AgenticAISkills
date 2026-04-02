---
name: frontend-diagram-system
description: Build premium frontend-based technical diagram systems for proposals, whitepapers, presales demos, interactive architecture explainers, and exportable presentation assets. Always use this skill when the user wants to turn technical content into polished diagrams or a live demo page, especially if they mention solution diagrams, 架构图, 技术方案图, 白皮书配图, interactive explanation pages, hover/click reveal details, style tabs, exportable PNG/SVG assets, or wants the same content expressed across multiple visual styles such as Apple, Palantir, or Mission Control. Prefer this skill over generic frontend work whenever the output is fundamentally a diagram system rather than a normal website page.
---

# Frontend Diagram System

This skill turns a static technical document into a frontend-based diagram system that is:

- visually polished enough for formal proposal decks and client demos
- structured enough to explain complex technical ideas clearly
- interactive enough for live walkthroughs
- exportable enough for Word, PPT, and PDF deliverables

## What this skill is for

Use this skill when the user needs a diagram workflow that combines:

1. technical accuracy
2. presentation-grade visual design
3. frontend interaction
4. export-friendly output

This is not generic infographic generation.

This skill is specifically for cases where diagrams need to live in a frontend page first, then be refined, reviewed, and exported.

Typical requests that should trigger this skill:

- "把方案内容做成一个可演示页面"
- "做一套可导出的技术方案图"
- "除了 Word，我还想现场给客户演示页面版"
- "把架构图做得可以 hover / click 讲解"
- "同一套内容做成 Apple / Palantir / Mission Control 三种风格"
- "把技术方案图做成可导出 PNG 的前端系统"

## Core principle

Treat diagrams as a product system, not single images.

That means every diagram should have:

- a clear semantic job
- a reusable visual grammar
- a presentation mode
- an export mode
- optional detail expansion for live explanation

## Workflow

Follow this sequence.

### 1. Normalize the content

Before drawing anything, reduce the source material into diagram-ready units.

For each target diagram, define:

- title
- one sentence purpose
- diagram type: overview, layer stack, pipeline, topology, factor map, milestone, decision tree, ecosystem map
- 3-7 primary entities
- 1 dominant relationship type
- optional secondary detail lists for click/hover expansion

If a diagram tries to explain more than one central relationship, split it.

Bad:

- one figure mixing stakeholders, technical layers, timeline, and outputs

Good:

- one stakeholder coordination diagram
- one three-layer capability diagram
- one data-to-decision pipeline

### 2. Define the design system first

Do not start by drawing cards.

Define a visual system before implementing diagrams:

- color tokens
- typography hierarchy
- card density
- border radius scale
- connector style
- annotation style
- interaction style

The style system must be intentional and narrow.

One diagram family should feel like one authored system.

Always decide these before implementation:

- what the dominant mood is
- what the card density should be
- whether the page is whitepaper-first, operator-first, or mission-first
- how much copy belongs in the visible state vs expanded state

### 3. Separate viewing mode from export mode

Always create two modes:

- browse mode: dense, comfortable, interactive
- export mode: stable size, controlled spacing, screenshot-safe

Never force export-height constraints into default browse mode.

### 4. Make the interaction useful

Interaction is not decoration.

Only add hover/click behavior when it helps live explanation.

Good interactive targets:

- stakeholder roles
- model components
- factor definitions
- milestone details
- warning levels
- output descriptions

Good interactions:

- click to expand details
- hover to reveal short explanation
- tab to switch style families

Avoid gimmicks:

- floating tooltips for everything
- unnecessary animations
- decorative hover scaling with no information gain

### 5. Build one hero sample first

Before scaling to all diagrams, produce one flagship diagram that establishes the standard.

Recommended order:

1. coordination overview
2. capability layers
3. data-to-decision pipeline

Only after one of these feels strong should the rest be propagated.

### 6. Add real style variants

If multiple styles are requested, make them structurally different, not just recolored.

Examples:

- Apple Blueprint: calm, sparse, editorial, whitepaper-first
- Palantir Ops: analytical, operational, matrix-oriented, tighter grids
- Mission Control: command-center, field-oriented, stronger directional flow

Each style should differ in:

- layout rhythm
- density
- card geometry
- connector logic
- tone of labels

Not just accent color.

### 7. Export readiness

Every final diagram system should support:

- stable IDs for export targets
- single-diagram capture
- clean print/export mode
- screenshot-safe spacing

Recommended export pattern:

- every diagram card gets a stable `data-export-name`
- normal browsing mode stays compact
- export mode applies stable min-height and print-safe spacing
- exported assets are named after the export IDs, not human titles

## Design rules

### Diagram semantics

Each diagram gets one main job.

- overview: who relates to whom
- layers: what builds on what
- pipeline: what flows where
- ecosystem: what platform pieces exist
- factor map: what contributes to what
- timeline: when what happens

### Typography

Typography is one of the main quality signals.

Use:

- elegant display serif or refined display sans for major titles
- restrained sans for body text
- condensed or mono only for tags, codes, labels, APIs, stages

Avoid overly technical text everywhere. It makes the page feel mechanical.

### Layout

Use strong macro-layout.

Prefer:

- central spine
- three-column orchestration
- stacked capability rows
- grouped modules with clear parent-child relationships

Avoid:

- random floating cards
- evenly distributed visual weight with no focal point
- over-packed cards

When in doubt, make the macro-layout more obvious before styling details.

The most common failure mode is not ugly colors. It is unclear spatial logic.

### Connectors

Connectors should explain relationship, not add atmosphere.

Use:

- a small number of precise lines
- consistent curvature
- consistent arrow semantics

Avoid:

- too many crossing paths
- lines that terminate ambiguously
- decorative lines with no meaning

### Density

Tighten aggressively.

Most diagrams are improved by:

- shorter copy
- fewer labels
- more group logic
- stronger spacing hierarchy

If a diagram feels crowded, reduce content before adding space.

Good diagram density rule:

- visible layer explains
- expanded layer justifies

Do not let the visible layer become the appendix.

## Interaction patterns

### Recommended pattern: details cards

For live demos, use expandable regions for supporting detail.

Pattern:

- visible layer: concise, presentation-safe summary
- expanded layer: supporting explanation bullets

This lets the presenter answer questions without leaving the visual surface.

### Recommended pattern: style tabs

Use tabs only if each tab expresses a genuinely different authored style.

Bad:

- same diagram, different colors

Good:

- same content, different layout language and visual tone

Use tabs when:

- the user is deciding which visual tone fits the client best
- the same technical content needs different presentation attitudes
- the page is being used live in client conversations

Do not use tabs when the styles are not meaningfully different.

## Deliverables

When this skill is used successfully, the expected output is usually:

- a frontend page containing the full diagram system
- one or more style modes
- interaction for expanded explanation
- export-friendly structure
- optional PNG/SVG export pipeline

## Recommended implementation architecture

For medium to large projects, prefer this split:

```text
src/
  DiagramStudio.jsx            # page shell, tabs, mode switching
  diagram-studio.css           # visual system tokens and base layout
  diagrams/
    coordination.jsx
    layers.jsx
    pipeline.jsx
    ecosystem.jsx
    factors.jsx
    roadmap.jsx
  data/
    coordination.js
    layers.js
    pipeline.js
  export/
    capture.js
```

Rules:

- content data should not be buried in CSS
- style tokens should not be repeated per diagram
- export naming should be centralized
- the shell should manage mode switching, not individual diagrams

## Example content decomposition

### Example A: stakeholder overview

Input intent:

- explain who participates
- explain who owns what
- explain what the central algorithm hub produces

Correct decomposition:

- left/right/top/bottom roles or 3-column orchestration
- one central service hub
- one output zone

Visible copy should include only:

- role label
- organization name
- one-line responsibility

Expanded copy can include:

- detailed responsibilities
- boundary definitions
- acceptance or integration notes

### Example B: three-layer capability architecture

Input intent:

- explain layered capability progression

Correct decomposition:

- shared input foundation
- L1/L2/L3 or equivalent
- each layer gets one short description and 3-4 capability chips

Avoid:

- giant paragraph blocks in each layer
- mixing timeline semantics into layer structure
- decorative arrows that do not explain flow

### Example C: pipeline diagram

Input intent:

- explain data-to-decision transformation

Correct decomposition:

- 4 or 5 sequential stages
- short stage titles
- one sentence each
- expanded details for sub-steps

## Interaction rules

Use `details/summary` for lightweight interaction when you need:

- native disclosure behavior
- low-complexity implementation
- export compatibility

Use custom controlled state only when you need:

- synchronized expansion
- analytics
- cross-diagram interactions
- keyboard/state orchestration beyond the native pattern

For live demo pages, default to this hierarchy:

- click expands details
- hover only enhances, never hides critical content
- tabs switch styles
- export mode disables unnecessary motion

## Export rules

When the user wants exportable assets, always implement:

1. default compact browse mode
2. explicit export mode, e.g. `?export=1`
3. stable selectors for every diagram card
4. one card = one export target

Recommended export IDs:

- `diagram-overview-coordination`
- `diagram-system-layers`
- `diagram-pipeline-delivery`
- `diagram-paddle-ecosystem`
- `diagram-data-governance`
- `diagram-detection-model`
- `diagram-risk-fusion`
- `diagram-spread-simulation`
- `diagram-warning-decision`
- `diagram-roadmap`

## Review checklist

Before considering the system done, review each diagram against this list:

- Is the diagram understandable in 5 seconds?
- Is the title better than the body copy?
- Does the diagram have one dominant relationship?
- Can the visible layer stand alone without expansion?
- Does expansion actually add useful talking points?
- Are style tabs structurally different, not just recolored?
- Does export mode look deliberate rather than stretched?
- Would this still feel good inside a proposal PDF?

## Escalation rule

If a diagram keeps getting worse through iteration, stop tweaking and recompose it.

Do not endlessly refine a broken structure.

Replace the layout.

## File structure recommendation

Use a structure like:

```text
src/
  DiagramStudio.jsx
  diagram-studio.css
  diagrams/
    overview-data.js
    layer-data.js
    pipeline-data.js
  export/
    capture.js
```

If the implementation grows, split by diagram and shared primitives.

## Quality checklist

Before calling the work done, verify:

- each diagram has one dominant idea
- the page has a clear visual hierarchy
- cards are not overfilled
- labels are short and intentional
- tabs create real stylistic differences
- click/hover reveals useful detail
- default browse mode is not stretched for export
- export mode does not break layout
- no diagram feels like a dashboard template

## Anti-patterns

Do not do these:

- static diagrams disguised as interactive UI
- export-mode spacing in normal browsing mode
- tab switching that only changes colors
- every card expandable, regardless of usefulness
- overusing badges, pills, and labels until the page looks noisy
- turning system diagrams into marketing cards

## If the user wants the workflow turned into a reusable skill

Capture the workflow as:

1. input normalization
2. visual token setup
3. flagship diagram creation
4. style variant generation
5. interaction layering
6. export mode separation
7. final export packaging

If needed, move larger implementation standards into reference files.

Useful reference files for this skill:

- `references/diagram-content-template.md`
- `references/style-variants.md`
