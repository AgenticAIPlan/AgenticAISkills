---
name: editorial-tech-atlas
description: Design and build high-end editorial technology websites with a dark, modern, systems-explorer feel. Use this skill whenever the user wants a polished product site, interactive narrative page, architecture explainer, feature atlas, research-style microsite, proposal demo page, whitepaper-to-site conversion, long-scroll technology story, or any section-based web experience with premium typography, subdued dark surfaces, hover-reveal details, anchored deep-link sections, click-to-reveal panels, sticky section navigation, or an annotated systems-publication feel. Also trigger for phrasing like “很有科技感的网站”, “技术叙事页面”, “交互式白皮书”, “长滚动 microsite”, “可演示方案页”, or “像研究站点/系统地图一样”. Prefer this over generic frontend styling when the result should feel like a premium technical publication, not a standard marketing page or dashboard.
license: CC BY-NC-SA 4.0
---

# Editorial Tech Atlas

This skill is for building websites that feel like a premium interactive technology editorial: dark, restrained, information-dense, and carefully staged.

The goal is not to clone any specific site. The goal is to reproduce the design grammar: strong narrative sections, premium typography, subtle motion, progressive disclosure, semantic color coding, and a modern research-lab mood.

## What this skill should produce

Use this skill when the deliverable should feel like:

- a high-end interactive microsite
- a technical story page with deep sections
- a polished product or architecture explainer
- a feature atlas with click-to-reveal detail
- a dense but readable modern technology presentation site

This is not a generic SaaS landing page.

The output should feel authored, structural, and tactile.

## Core design thesis

Build the page like an annotated system map.

That means:

- content is organized into numbered narrative sections
- the layout favors scanability first, then deeper interaction
- hover gives hints, click reveals substance
- color is semantic, not decorative
- motion guides attention instead of showing off
- typography carries hierarchy as much as layout does

## Visual direction

Default aesthetic:

- near-black canvas
- soft glass or matte panels
- faint dividers and translucent layering
- one warm metallic accent for primary emphasis
- several muted category colors for semantic grouping
- low-noise, editorial spacing with technical precision

Avoid:

- loud gradients everywhere
- shiny cyberpunk neon overload
- generic startup hero blocks
- oversized pills and empty marketing fluff
- random card grids with no narrative structure

## Typography system

Use a three-tier type system whenever possible:

1. geometric or modern grotesk for headings and structural labels
2. serif for explanatory body copy and more reflective paragraphs
3. mono for commands, chips, counters, anchors, paths, metadata, and small labels

Why this matters:

- sans gives control and clarity
- serif adds authority and editorial depth
- mono signals system detail and technical specificity

If web fonts are allowed, a strong default combination is:

- heading: `Space Grotesk` or a similar sharp geometric grotesk
- body: `Source Serif 4` or another readable editorial serif
- mono: `JetBrains Mono` or a similarly crisp mono

If the existing product already has a font system, adapt this logic rather than forcing these exact families.

## Color system

Define tokens first. Always create named variables.

Recommended token groups:

- `--bg`
- `--bg-elevated`
- `--surface`
- `--surface-strong`
- `--border`
- `--text`
- `--text-muted`
- `--accent`
- `--accent-soft`
- `--category-*`

Preferred palette behavior:

- background sits near black, charcoal, graphite, or warm-black
- text is soft white, not pure white
- borders stay low-contrast but consistent
- accent is singular and memorable, often warm gold, brass, or muted amber
- category colors are desaturated and earthy, not toy-like

Good category colors:

- slate blue
- rust
- moss green
- pale teal
- dusty lavender
- warm gray

These should help classify content, not turn the page into a rainbow.

## Layout grammar

The page should feel like one composed document.

Use this macro structure:

1. immersive hero
2. section rail or section navigator
3. repeated numbered sections
4. one main interactive module per section
5. restrained footer that remains in-system

Each major section should usually contain:

- small section number
- thin divider or horizontal rule
- strong title
- brief subhead
- one primary interactive region

Keep widths controlled. Dense information reads better inside deliberate max widths than edge-to-edge layouts.

Prefer:

- `max-width` containers
- asymmetric internal composition
- generous vertical rhythm
- clear separation between overview and detail areas

Avoid:

- dashboard-wide stretch layouts for editorial content
- perfectly even card mosaics without focal hierarchy
- stacking too many unrelated modules into one section

## Interaction model

Follow this rule:

- hover previews
- click commits
- scroll advances narrative

Good uses of hover:

- reveal a label next to an icon or section index
- raise brightness slightly on a tile
- hint at a hidden affordance
- surface a one-line explanation

Good uses of click:

- open detail panels
- swap the active record in a grid
- drill into architecture nodes
- open modal or sheet content on mobile

Avoid hover-only critical information. The important state change should always be available through click or focus.

## Deep-linking and navigation

This design language works best with in-page deep links.

Implement:

- stable section IDs
- smooth scrolling between sections
- active section highlighting via scroll position or intersection observers
- desktop side rail and mobile sheet or compact navigator when appropriate

The usual pattern is:

- high-level navigation jumps to sections
- internal interactive modules manage detail state locally
- URL changes are reserved for meaningful sections, not every micro-interaction

If the project benefits from fully shareable states, add query params or hash fragments for active module state. Otherwise keep detail state local and lightweight.

## Progressive disclosure

This is the heart of the style.

Start with a readable surface, then reveal depth only when the user asks for it.

Preferred pattern:

- visible layer: concise labels, clear taxonomy, short descriptions
- revealed layer: supporting notes, bullets, technical details, references, or examples

Typical modules:

- architecture explorer
- tool or feature atlas
- command or API explorer
- hidden capabilities grid
- timeline or release lattice
- evidence cards or annotated reference blocks

When a user clicks an item, render the detail in one of these ways:

- adjacent sticky detail panel
- expanded inline region below the selected grid
- side sheet or bottom sheet on small screens
- modal when the content is self-contained

Do not reveal everything at once.

## Motion rules

Motion should be low-amplitude and purposeful.

Use:

- fade-ups on section entry
- staggered reveals in hero and list regions
- width expansion for navigation hints
- opacity transitions for detail states
- subtle scale or brightness shifts on active cards
- slide-up bottom sheets on mobile

Avoid:

- bouncy micro-interactions everywhere
- large parallax effects that distract from reading
- dramatic 3D transforms with no semantic meaning

If you animate, make sure the animation explains one of these:

- this entered
- this became active
- this is expandable
- this belongs to the current section

## Surface styling

Prefer surfaces that feel precise and physical:

- soft translucent panels
- matte dark blocks
- thin borders
- tiny highlight gradients
- subtle internal shadows
- faint background grids or line patterns

Useful atmosphere elements:

- animated grid background in the hero
- noise or grain at very low opacity
- soft radial glow behind focal regions
- restrained backdrop blur on overlays

Do not let atmosphere overpower legibility.

## Responsive behavior

Do not only resize. Re-compose.

Desktop patterns:

- fixed or sticky section rail
- multi-column interactive layouts
- adjacent detail panel next to a grid or map

Mobile patterns:

- bottom sheet section navigation
- stacked overview then detail
- reduced density in labels
- larger tap targets and simplified hover affordances

If a desktop pattern depends on hover, convert it into tap-select behavior on mobile.

## Implementation workflow

Follow this order.

### 1. Define the narrative structure

Break the page into 3-7 numbered sections.

For each section, define:

- section ID
- section number
- title
- one-sentence thesis
- primary interactive module
- what detail is hidden by default

### 2. Define tokens

Before building modules, create the theme tokens for color, spacing, radius, shadow, blur, and typography.

### 3. Build the shell

Implement:

- page background and atmosphere
- hero
- section wrappers
- global nav or section rail
- mobile navigation pattern

### 4. Build one flagship module first

Start with the section that best proves the visual system. Usually this is:

- an architecture explorer
- a categorized feature grid
- a technical command atlas

Only propagate the system once that section feels convincing.

### 5. Add disclosure behavior

Make the overview state elegant first. Then add selection, detail reveal, keyboard focus, and mobile sheet logic.

### 6. Add motion last

Do not use animation to rescue weak layout. The composition should work fully before motion.

## Recommended component set

This style often benefits from components like:

- `HeroSection`
- `SectionRail`
- `SectionBlock`
- `InfoPanel`
- `ExplorerGrid`
- `ExplorerCard`
- `DetailPane`
- `MobileSectionSheet`
- `StatStrip`
- `TaxonomyChip`
- `AmbientGrid`

Keep state ownership clean. Navigator state and selected-item state should not be mixed together unnecessarily.

## Content writing guidance

The copy should be concise, informed, and technical without reading like marketing sludge.

Use:

- short declarative section titles
- one or two sentence subheads
- restrained metadata labels
- concise bullet detail panels

Avoid:

- hype-heavy slogans
- long product-marketing paragraphs
- vague claims with no content structure

The right tone is closer to an annotated systems publication than a startup billboard.

## Accessibility and robustness

Always preserve:

- keyboard access for all interactive tiles and nav items
- visible focus states
- sufficient contrast for body text and metadata
- reduced-motion fallback
- touch-friendly interaction for mobile

If using server-rendered entry animations, avoid a blank pre-hydration state. Remove or neutralize hidden initial transforms when hydration is delayed.

## Output expectations

When this skill succeeds, the output should usually include:

- a complete page or section system
- reusable tokens and typography rules
- at least one strong progressive-disclosure module
- anchored sections with clear navigation
- responsive behavior tuned for both desktop and mobile
- restrained but premium motion

## Reference files

Read these references when useful:

- `references/design-principles.md` for the full style anatomy
- `references/interaction-patterns.md` for hover, click, detail, and deep-link behavior
- `references/implementation-playbook.md` for practical coding structure

## Final reminder

Do not imitate branding, copy, or unique illustrations from any one reference site.

Instead, capture the underlying design intelligence:

- editorial hierarchy
- dark precision
- semantic color
- progressive disclosure
- interactive systems thinking

That is what makes this style powerful.
