# Implementation Playbook

Use this reference when turning the style into real code.

## Recommended project shape

For a React or similar frontend project, a clean structure is:

```text
src/
  app/
  components/
    AmbientGrid.*
    HeroSection.*
    SectionRail.*
    SectionBlock.*
    ExplorerGrid.*
    ExplorerCard.*
    DetailPane.*
    MobileSectionSheet.*
  data/
    sections.*
    taxonomy.*
  styles/
    tokens.css
    base.css
    motion.css
```

The point is to keep:

- data separate from presentation
- tokens centralized
- interaction primitives reusable

## Build order

### 1. Tokens first

Implement:

- color variables
- type scale
- spacing scale
- radius scale
- blur and shadow tokens
- motion durations

Do not hardcode ad hoc values throughout components.

### 2. Shell second

Build:

- page background
- hero
- section wrappers
- nav rail or section navigator
- responsive max-width system

### 3. One flagship module

Get one interactive section right before multiplying patterns.

Best starting options:

- explorer grid with detail pane
- architecture tree with selected state
- categorized feature atlas

### 4. Responsive redesign pass

Do not wait until the end to check mobile.

Specifically test:

- section navigation
- detail reveal pattern
- dense card grids
- sticky elements

### 5. Motion and polish pass

Add:

- hero stagger
- section entry transitions
- subtle hover brightness
- detail reveal transitions

Then stop before it becomes too ornamental.

## Practical coding rules

### Use stable section data

Represent sections as structured data:

- `id`
- `index`
- `title`
- `summary`
- `component`

This makes side rails, mobile navigators, and active states easier to keep in sync.

### Keep module state local

Examples:

- active architecture node
- selected feature card
- current explorer tab

Section navigation should stay global. Explorer selection should stay local unless shareability really matters.

### Use semantic classes and tokens

Favor classes like:

- `.section-frame`
- `.section-kicker`
- `.explorer-card`
- `.detail-pane`
- `.taxonomy-chip`

This makes later theming and polish much easier than one-off utility soup alone.

### Animate opacity and transform, not layout chaos

Good:

- opacity
- translateY
- scale within tight bounds
- width expansion for a nav label

Use layout reflow sparingly and intentionally.

### Design for pre-hydration safety

If using SSR or partial hydration:

- avoid hiding large content blocks with inline `opacity: 0` until JS runs
- provide a readable static fallback
- make the no-JS state respectable

## Suggested CSS token starter

```css
:root {
  --bg: #0d0d0d;
  --bg-elevated: rgba(255, 255, 255, 0.03);
  --surface: rgba(255, 255, 255, 0.05);
  --surface-strong: rgba(255, 255, 255, 0.08);
  --border: rgba(255, 255, 255, 0.12);
  --text: rgba(245, 242, 235, 0.94);
  --text-muted: rgba(245, 242, 235, 0.62);
  --accent: #d4a853;
  --category-slate: #7b9eb8;
  --category-rust: #c17b5e;
  --category-moss: #6ba368;
  --category-teal: #9bbec7;
  --category-lavender: #b8a9c9;
  --category-stone: #8a8580;
}
```

Treat this as a starting skeleton, not a fixed brand system.

## Review checklist

Before finishing, verify:

- the page has a clear section narrative
- one glance reveals hierarchy
- hover never carries the full meaning alone
- click states are obvious
- the detail layer adds real substance
- fonts are doing distinct jobs
- the palette is restrained and semantic
- mobile keeps the concept intact
- motion improves focus rather than stealing it

If the result feels like a normal startup landing page with darker colors, the system is not strong enough yet.
