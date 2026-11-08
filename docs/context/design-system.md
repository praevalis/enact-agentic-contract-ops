# Enact Design System

**Related:** `docs/reference/enact-project-brief.md`, `docs/context/prd.md`, `docs/context/execution-plan.md`

## Brand positioning

Enact turns signed agreements into verified operational change. The product should feel precise, consequential, and visibly active. Its primary audience is the deal desk team carrying signed intent into operations. Operations reviewers and auditors also need to understand what changed, why it changed, and who authorized it.

The visual identity should support source-grounded review and governed execution. Amber is Enact's recognizable signal for primary action. A related Umber supports provenance details without competing for attention. Neutral surfaces carry contract text, operational data, and decisions. Status colors communicate state independently from the brand signal.

## Fixed color palette

The hex values below form one palette for both light and dark modes. Brand, neutral, and status colors do not receive mode-specific replacements. Modes assign these same colors to different surface and text roles.

### Brand colors

| Color | Hex | Role |
|---|---|---|
| Amber | `#C9A75D` | Signature color for the Enact mark and primary actions |
| Umber | `#7B6851` | Subordinate, related tone for provenance marks and restrained emphasis |

### Neutrals

| Color | Hex | Role |
|---|---|---|
| Night | `#171D20` | Dark canvas, light-mode primary text, fixed logo backing |
| Deep | `#1C2427` | Dark-mode surface |
| Raised | `#222C2F` | Dark-mode inset or raised surface |
| Edge | `#334044` | Low-emphasis dark-mode control boundary when needed |
| Graphite | `#48565A` | Light-mode secondary text |
| Steel | `#AEB9B5` | Dark-mode secondary text |
| Line | `#E8EBE8` | Low-emphasis light-mode control boundary when needed |
| Soft | `#F8F9F7` | Light-mode inset surface |
| Off-white | `#FBFBFA` | Light-mode surface |
| White | `#FFFFFF` | Light canvas and dark-mode primary text |

Light surfaces remain close to white. Dark surfaces remain close to Night. Surface depth comes from these small tonal steps and restrained elevation. Use spacing and headings to separate sections rather than dividing lines or large gray panels.

### Operational states

| State | Color | Hex |
|---|---|---|
| Ready or reconciled | Green | `#4F8065` |
| Needs review | Muted violet | `#866B8E` |
| Processing | Steel blue | `#587A96` |
| Blocked or failed | Muted red | `#B15460` |

These colors indicate operational meaning, not brand identity. Always pair status color with a visible text label. Do not use Amber as the Needs review or Processing status color.

## Mode assignments

| Role | Light mode | Dark mode |
|---|---|---|
| Canvas | White | Night |
| Main surface | Off-white | Deep |
| Inset surface | Soft | Raised |
| Control boundary, when needed | Line | Edge |
| Primary text | Night | White |
| Secondary text | Graphite | Steel |
| Brand signal | Amber | Amber |
| Related support | Umber | Umber |
| Status colors | Fixed values above | Fixed values above |

The Enact mark should use the same color values in both modes. Its backing or placement must preserve legibility without changing its brand colors.

## Logo

The Enact mark is a compact E made from aligned strokes. Its Amber middle stroke reaches a separate endpoint, reflecting a deliberate change carried from an agreement into an operational system. The mark uses Amber and Off-white on a fixed Night backing in both modes. The full lockup pairs the mark with the Enact wordmark on the same backing, with about 6 px between the visible mark and first letter. Use the scalable mark alone at navigation and favicon sizes.

The approved vector assets are `apps/web/src/assets/brand/logo-mark.svg` and `apps/web/src/assets/brand/logo.svg`. Keep the mark's geometry and colors consistent at every size and in both themes.

### Theme preference

Follow the user's system appearance setting by default and respond when that setting changes. Offer an explicit choice of System, Light, or Dark. Light and Dark override the system setting until the user chooses another option; System restores automatic behavior. Remember the user's explicit choice across visits and apply it when the interface first appears, without showing the wrong mode first.

## Typography

Use IBM Plex Sans for interface headings, body text, controls, tables, and source excerpts displayed by Enact. Use IBM Plex Mono sparingly for technical identifiers and source references, such as case IDs and document clause labels. Long contract passages and ordinary explanatory text stay in IBM Plex Sans.

Use tabular numerals in IBM Plex Sans where amounts, dates, quantities, or before-and-after values must align. Monospace is reserved for identifier-like content rather than used to align whole tables. Establish hierarchy through size, weight, and spacing within the two selected families instead of adding a decorative display face.

### Type hierarchy

| Role | Size / line height | Weight | Typical use |
|---|---|---|---|
| Page title | 30 / 36 px | 600 | The main heading of a workspace view |
| Section heading | 20 / 28 px | 600 | Major areas within a view |
| Panel heading | 16 / 24 px | 600 | A card or subsection title |
| Reading text | 16 / 24 px | 400 | Contract excerpts, decision rationale, and guidance |
| Interface text | 14 / 20 px | 400 or 500 | Queue rows, fields, navigation, and buttons |
| Supporting text | 12 / 16 px | 400 or 500 | Dates, captions, and secondary metadata |
| Prominent value | 24 / 32 px | 600 | Counts and summary figures when they help comprehension |

Use the 14 px tier for compact operational controls and the 16 px tier for sustained reading. Keep supporting text at least 12 px. Use IBM Plex Mono only for short technical references, at the size of the surrounding interface or supporting text. Apply this hierarchy consistently across screen sizes; change a type size at a breakpoint only when the layout requires it. Allow text to wrap and containers to grow when users increase text size or spacing.

Manage both families through Fontsource and serve the font files with the web application. Load IBM Plex Sans at weights 400, 500, and 600 and only the IBM Plex Mono weights the interface uses, with system sans-serif and monospace fallbacks for unavailable font files.

## Spacing

Use Tailwind's 4 px spacing unit as the foundation. The 6 and 10 px half steps are reserved for labels and control interiors. Keep related information compact and create more space between distinct sections of work. Prefer values from the shared scale over one-off pixel measurements.

| Relationship | Default | Adjustment |
|---|---|---|
| Label to field | 6 px (`gap-1.5`) | 8 px (`gap-2`) when supporting text needs clearer separation |
| Button content padding | 8 px vertical, 16 px horizontal (`py-2 px-4`) | Small: 6/12 px (`py-1.5 px-3`); large: 10/20 px (`py-2.5 px-5`) |
| Items within a record or form group | 16 px (`gap-4`) | 12 px (`gap-3`) in dense rows or compact forms |
| Panel padding | 24 px (`p-6`) | 20 px (`p-5`) for compact panels; 28 px (`p-7`) for spacious summaries |
| Related panels | 24 px (`gap-6`) | 32 px (`gap-8`) when panels carry separate topics |
| Major workspace sections | 48 px (`gap-12`) | 40 px (`gap-10`) for a continuous workflow; 56 px (`gap-14`) at a major stage boundary |

Page gutters grow from 16 px on narrow screens to 32 px on medium screens and 48 px on wide screens (`px-4 sm:px-8 lg:px-12`). Use matching top and bottom padding of 40 px through medium screens and 48 px on wide screens (`py-10 lg:py-12`). The medium breakpoint increases horizontal space while preserving the vertical rhythm.

Use the smaller steps within a single idea, such as a label and its field or a value and its source. Use the larger steps when attention moves to another section or stage. Apply each boundary's spacing once, through a parent gap or a sibling margin, so nested layouts do not add both. Avoid section-sized gaps inside tables, case records, or dense evidence views.

## Section composition

Let sections and components flow together without decorative dividers. Establish grouping through the spacing scale, clear section headings, and the distinct form or surface of each component. Keep related content close and give separate topics enough space to read as separate groups. Use Line and Edge only where a control needs a visible boundary for its affordance, not as separators between sections, panels, or repeated items.

## Component shape

Choose border radius according to each component's role and size. Use slight rounding (`rounded-md`, 6 px) through moderate rounding (`rounded-lg`, 8 px) as the normal range. Keep the choice consistent for repeated instances of a component and use the same shape in light and dark modes. Do not impose one radius on every control and surface.

## Interaction states

Use small changes in surface tone and elevation for pointer feedback. Keep component borders stable across hover, press, and selection. In dark mode, surface tone carries more of the distinction where a shadow would be difficult to see.

| State | Treatment |
|---|---|
| Default | Clear label and affordance on the component's normal surface |
| Hover | Slight surface color change, with a soft shadow on components that appear raised |
| Pressed | Slightly deeper surface tone and reduced shadow while pressed |
| Selected | Persistent surface tone plus a checkmark, selected label, or other visible cue that remains after hover ends |
| Keyboard focus | Immediate outer focus ring using a contrasting shadow, visible for as long as the control has keyboard focus |
| Disabled | Muted appearance and disabled behavior while keeping the label legible |
| Invalid | Explanatory text beside the affected field, reinforced by an error icon or marker |
| Submitting | Keep entered values visible, prevent duplicate submission, and identify the pending action |

Use Graphite for the focus ring against light surfaces and Steel against dark surfaces. Check the ring against each component's actual surroundings, including Amber-filled controls. Do not rely on color or shadow alone to communicate selection, errors, or pending work. A local submitting state is distinct from the case status Processing reported by the API.

## Motion

Use restrained motion to confirm interactions, preserve context as local content changes, and draw attention to confirmed state changes. Evidence, decisions, and status labels must remain readable without animation.

| Moment | Treatment | Duration |
|---|---|---|
| Hover, press, and selection | Subtle surface tone or shadow transition | About 120 ms |
| Open or close a detail panel or disclosure | Short fade with a small positional shift | About 200 ms |
| Confirmed status change | Brief highlight that settles into the persistent labeled state | About 200–300 ms |

Use the case status terminology supplied by the API for prominent labels: Draft, Processing, Blocked, Ready, Completed, Failed, and Cancelled. Show a changed status only when the server reports it. A successful request must not be presented as completed execution or reconciliation before the server confirms the resulting state. More specific workflow stages belong in a detail view when the API exposes them.

For ongoing work, pair a restrained activity indicator with the current status label. Do not show a percentage unless the system measures actual progress. Keep timelines and contract text stable as updates arrive; avoid repeated pulsing, bouncing badges, and large page transitions. Focus indicators appear immediately.

Respect reduced-motion preferences by removing positional movement and other nonessential animation. Preserve the same status information through text and static styling.

## Usage and accessibility

- Use Amber sparingly for the Enact mark and the main action in a view. Use Night text and a Night border on Amber-filled controls so the label and control boundary remain clear in both modes.
- Do not use Amber for small text on White or Off-white. Amber and White have only 2.29:1 contrast.
- Use Umber as a small provenance mark or restrained supporting element. Keep adjacent explanatory text in the mode's neutral text color.
- Use the operational state colors for state markers alongside visible text labels, never as the sole carrier of meaning.
- Keep document evidence, comparison values, and decision text on neutral surfaces. Color should direct attention to a meaningful action or state rather than fill large reading areas.

Checked contrast pairs for this palette include Night on Amber at 7.44:1, Night on White at 17.03:1, Graphite on White at 7.62:1, White on Deep at 15.78:1, and Steel on Deep at 7.82:1. Component implementations must verify contrast in their actual states and backgrounds.
