# Export Playbook

Use this when the user wants diagrams exported to PNG, SVG, or embedded into Word/PPT.

## Rule 1

Browse mode and export mode must be separate.

Browse mode:

- compact
- conversational
- optimized for interaction

Export mode:

- stable card height
- screenshot-safe spacing
- controlled print styles
- no layout jumps

## Rule 2

Every export target must have a stable selector.

Preferred pattern:

```html
<section class="diagram-card" data-export-name="diagram-system-layers"></section>
```

## Rule 3

Export naming should be systematic.

Bad:

- `final-v2.png`
- `good-one.png`

Good:

- `diagram-system-layers.png`
- `diagram-overview-coordination.png`

## Rule 4

Use print/export mode for fixed-height layouts only.

Do not force giant card heights during normal browsing.

## Rule 5

Before export, verify:

- no card overflow
- no clipped shadows
- no hidden expanded state unless intended
- no tabs or controls that should be hidden in final asset
- no visible debug text
