# New Genre — Style Reference
> Cinematic horizon at golden hour — a single gradient arc from charred umber through steel twilight to warm parchment, against which condensed serif headlines carve like editorial mastheads.

**Applies to:** every project frontend from Turnstile onwards (owner's decision, 15 September 2026). Sentinel, Sitewatch, Trackside and Kaunter stay on Column; the portfolio site stays on Apple (España).

**Theme:** light

New Genre operates in a cinematic dawn-to-dusk register: near-white surfaces, a near-black text color, and one monumental gradient that arcs from charred brown through steel blue to warm cream — that gradient IS the brand. Typography is a two-voice conversation between a condensed display serif (Serrif Condensed) that fills the top of every page with editorial gravity, and a low-weight geometric sans (Saans Variable) that handles everything else with quiet precision. The system is deliberately monochromatic at the interface level — no accent buttons, no chromatic badges — letting photographic work, gradient washes, and typographic contrast carry all the emotion. Components are architectural: pill-shaped controls at 50-90px radius, 16px-radius cards, hairline dividers, and barely-there elevation. Space is compact and functional, never decorative.

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Parchment Canvas | `#ffffff` | `--color-parchment-canvas` | Page backgrounds, card surfaces, inverse text on dark fills |
| Onyx | `#0c1018` | `--color-onyx` | Primary body text, headings, input text, icon fills — blue-shifted near-black replaces pure #000 across the interface |
| Pure Black | `#000000` | `--color-pure-black` | Footer text, heavy display accents, icon strokes — reserved for maximum weight moments |
| Charred Umber | `#1e1310` | `--color-charred-umber` | Footer surface, dark contrast bands, gradient origin stop — warm dark anchors the bottom of the spectrum |
| Slate Veil | `#6d7074` | `--color-slate-veil` | Secondary headings, subdued labels, inactive nav — desaturated mid-gray for quiet hierarchy |
| Ash Mist | `#9e9fa3` | `--color-ash-mist` | Supporting neutral for secondary UI, dividers, and muted labels. |
| Dawn Arc | `linear-gradient(rgb(40, 14, 1) 0%, rgb(24, 38, 68) 15.2608%, rgb(90, 118, 159) 30.284%, rgb(135, 161, 196) 43.3787%, rgb(193, 211, 230) 58.8313%, rgb(254, 249, 225) 79.7139%, rgb(247, 243, 240) 100%)` | `--color-dawn-arc` | Brand signature — the iconic hero gradient (charred umber → steel twilight → warm parchment); used in gradient washes, atmospheric overlays, and the gradient-text reveal effect on display headlines |
| Ember Radiance | `radial-gradient(75% 300% at 109.6% 147.1%, rgb(255, 230, 0) 0%, rgb(237, 148, 84) 29.5837%, rgba(153, 161, 175, 0.06) 100%)` | `--color-ember-radiance` | Accent warmth for radial gradient highlights and hover-state glows — the golden-hour counterpoint to the cool steel-blue arc |

## Tokens — Typography

### Serrif Condensed · `--font-serrif-condensed`
- **Substitute:** Fraunces (condensed variant) or Playfair Display SC. *In practice (Turnstile): Instrument Serif via next/font — a condensed editorial serif on Google Fonts at weight 400.*
- **Weights:** 400 · **Sizes:** 64px, 72px · **Line height:** 1.05 · **Letter spacing:** -0.02em
- **Role:** Display headlines — only used at 64-72px for hero and section-opening statements. Condensed letterforms with negative tracking create editorial masthead weight without boldness; the 1.05 line-height lets lines stack tightly into monumental blocks. This font carries the brand's voice at maximum volume.

### Saans Variable · `--font-saans-variable`
- **Substitute:** Söhne or General Sans. *In practice (Turnstile): DM Sans (variable) via next/font — weights 300, 380, 400, 500, 570 all reachable on the wght axis.*
- **Weights:** 300, 380, 400, 500, 570 · **Sizes:** 12–32px · **Line height:** 1.00–1.40 · **Letter spacing:** -0.01em
- **Role:** Body, navigation, buttons, inputs, subheadings — the workhorse. Weight 300 whispers, 400 speaks, 500-570 emphasizes. Tight -0.01em tracking across all sizes; line-height tightens to 1.0 for UI labels and opens to 1.4 for paragraph body.

### Type Scale

| Role | Size | Line Height | Letter Spacing | Token |
|------|------|-------------|----------------|-------|
| caption | 12px | 1.2 | -0.12px | `--text-caption` |
| body-sm | 14px | 1.4 | -0.14px | `--text-body-sm` |
| body | 16px | 1.3 | -0.16px | `--text-body` |
| subheading | 20px | 1.2 | -0.2px | `--text-subheading` |
| heading-sm | 24px | 1.15 | -0.24px | `--text-heading-sm` |
| heading | 32px | 1.1 | -0.32px | `--text-heading` |
| display | 64px | 1.05 | -1.28px | `--text-display` |
| display-lg | 72px | 1.05 | -1.44px | `--text-display-lg` |

## Tokens — Spacing & Shapes

**Density:** compact. Spacing scale 4, 6, 8, 10, 12, 16, 20, 24, 26, 32, 48, 52, 56, 64.

| Element | Radius |
|---------|-------|
| cards | 16px |
| inputs | 50px |
| buttons | 50px |
| nav-links | 8px |
| buttons-pill | 90px |

**Layout:** page max-width 1400px · section gap 64–96px · card padding 32px · element gap 10–16px.

## Components

- **Hero Gradient Banner** — full-bleed section on the dawn arc (charred umber at 0% through steel twilight at 30–58% to warm cream at 80–100%). Serrif Condensed display headline at 64–72px in Onyx, left-aligned with generous left margin. Gradient-text effect on the final phrase so it fades into the background.
- **Gradient-Text Reveal** — a trailing phrase of the display headline dissolves from #0c1018 into the gradient (CSS mask or colour fade): a horizon line where text becomes atmosphere.
- **Pill Action Button** — 50–90px radius, transparent or near-white, Saans 16px weight 400–500, Onyx text, 12–16px horizontal / 6–10px vertical padding. Ghost style — no fill, no border.
- **Top Navigation Bar** — logo in Saans 14–16px weight 500 uppercase; items in Saans 14–16px weight 400; a thin hairline can separate two groups. No background, no border-bottom — floats on the gradient.
- **Process Card** — 16px radius, #f5f5f5, 32px padding; heading Saans 24px weight 500 Onyx; body Saans 16px weight 400 Slate Veil; lower portion a full-bleed photograph.
- **Text Input** — 50px radius pill, Saans 16px, 1px border in Ash Mist, placeholder-driven.
- **Footer Dark Band** — Charred Umber background, white text, Saans 12–16px. The footer inherits the darkest stop of the hero gradient, bookending the page.

## Do's and Don'ts

### Do
- Use the dawn arc gradient as a full-bleed atmospheric wash for hero and transition sections — never as a small element background.
- Set all display headlines in Serrif Condensed at 64-72px weight 400, line-height 1.05, letter-spacing -0.02em.
- Use Onyx (#0c1018) for all primary text rather than pure #000000.
- Apply the gradient-text dissolve on the final 20-40% of display headlines.
- Use 50-90px radius for interactive elements; 16px for cards; 8px for small UI.
- Maintain -0.01em letter-spacing on all Saans text.
- Keep the interface monochromatic; let the gradient and typographic contrast carry the emotion.

### Don't
- Never introduce chromatic accent colors (no red, green, blue, or purple for buttons, badges, or tags).
- Never use Serrif Condensed below 48px.
- Never use bold weights (600-700) in Saans — authority comes from size and spacing, not weight.
- Never apply drop shadows or box-shadows — elevation is surface lightness, not shadow.
- Never use pure black for body text.
- Never use border-radius below 8px.
- Never use line-height above 1.4 or below 1.0 in Saans.

## Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 0 | Canvas | `#ffffff` | Default page background for content sections |
| 1 | Gradient Atmosphere | dawn arc | Full-bleed hero and transition sections |
| 2 | Card Surface | `#f5f5f5` | Content cards — whisper-light off-white that recedes against the canvas |
| 3 | Dark Ground | `#1e1310` | Footer and dark contrast bands |

## Layout

Full-bleed hero and transition sections (gradient edge to edge); content sections max-width ~1400px centred. Hero: full-viewport gradient with a left-aligned monumental serif headline and vast negative space. Section rhythm: dark gradient hero → light gradient continuation → white content, a dawn-to-daytime arc. 3-column equal-height card grids for process blocks. Navigation floats on the gradient with no background. Generous vertical spacing between major sections (64-96px), compact within components (10-16px). Asymmetric, left-aligned content rather than centred stacks.

## Gradient System

1. **Dawn Arc** (linear, vertical): #1e1310 → #182644 → #5a769f → #87a1c4 → #c1d3e6 → #fef9e1 → #f7f3f0. Full-bleed heroes and transition bands; also a mask on images or a text fill on the last words of a display headline.
2. **Ember Radiance** (radial, off-centre at 109.6% 147.1%): #ffe600 → #ed9454 → transparent grey. Hover-state atmosphere and accent warmth. Never a primary background.
3. **Fire Line** (secondary, linear): #1e1310 → #903c27 → #e46c44 → #ed9454 — warm complement for hover states on dark sections.

## Elevation Philosophy

No box-shadows. Elevation is the gradient plus near-white surface lightness: cards on a white canvas are #f5f5f5. Hierarchy = gradient atmosphere (1) → white canvas (0) → card surface (2). A drop shadow would feel foreign.

## Adapting it to data dashboards (Turnstile's reading of the rules)

- Status (passed / warning / failed) is carried by **weight and words, not colour**: FAILED as an Onyx-filled pill with parchment text, WARNING as an Onyx-outlined pill, PASSED in Slate Veil, NOTED in Ash Mist.
- Chart marks are Onyx and Slate Veil; the dawn arc's steel blue may sit under a line as a low-opacity wash (the gradient "as atmosphere"), never as a categorical colour.
- Negative and positive changes are distinguished by sign and weight, not hue.

## Quick Start — CSS custom properties

```css
:root {
  --color-parchment-canvas: #ffffff;
  --color-onyx: #0c1018;
  --color-pure-black: #000000;
  --color-charred-umber: #1e1310;
  --color-slate-veil: #6d7074;
  --color-ash-mist: #9e9fa3;
  --color-dawn-arc: #5a769f;
  --gradient-dawn-arc: linear-gradient(rgb(40, 14, 1) 0%, rgb(24, 38, 68) 15.2608%, rgb(90, 118, 159) 30.284%, rgb(135, 161, 196) 43.3787%, rgb(193, 211, 230) 58.8313%, rgb(254, 249, 225) 79.7139%, rgb(247, 243, 240) 100%);
  --color-ember-radiance: #ed9454;
  --gradient-ember-radiance: radial-gradient(75% 300% at 109.6% 147.1%, rgb(255, 230, 0) 0%, rgb(237, 148, 84) 29.5837%, rgba(153, 161, 175, 0.06) 100%);

  --text-caption: 12px;      --leading-caption: 1.2;     --tracking-caption: -0.12px;
  --text-body-sm: 14px;      --leading-body-sm: 1.4;     --tracking-body-sm: -0.14px;
  --text-body: 16px;         --leading-body: 1.3;        --tracking-body: -0.16px;
  --text-subheading: 20px;   --leading-subheading: 1.2;  --tracking-subheading: -0.2px;
  --text-heading-sm: 24px;   --leading-heading-sm: 1.15; --tracking-heading-sm: -0.24px;
  --text-heading: 32px;      --leading-heading: 1.1;     --tracking-heading: -0.32px;
  --text-display: 64px;      --leading-display: 1.05;    --tracking-display: -1.28px;
  --text-display-lg: 72px;   --leading-display-lg: 1.05; --tracking-display-lg: -1.44px;

  --font-weight-light: 300; --font-weight-w380: 380; --font-weight-regular: 400; --font-weight-medium: 500; --font-weight-w570: 570;

  --page-max-width: 1400px; --card-padding: 32px;
  --radius-cards: 16px; --radius-inputs: 50px; --radius-buttons: 50px; --radius-nav-links: 8px; --radius-buttons-pill: 90px;
  --surface-canvas: #ffffff; --surface-card-surface: #f5f5f5; --surface-dark-ground: #1e1310;
}
```

Source: Refero extraction of newgenre.studio (2026-06-03, extended variant).
