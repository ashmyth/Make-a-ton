# Monad — Style Reference
> editorial tech journal on warm parchment

**Theme:** light

Source measurements are normalized; roles and recommendations are interpreted. Font summary lists are independent, not paired by position. HTML examples are reconstructions, not source components.

Monad renders its entire interface on a warm parchment canvas (#f6f3f1) that immediately separates it from the typical pure-white SaaS template. Headlines carry editorial weight in Untitled Serif at weight 400 — never bold — while every body, nav, and UI string runs in ABC Diatype Mono, giving the site the texture of a technical manual typeset for a literary magazine. A single vivid Lake Blue (#2b59d1) is the only chromatic accent for primary actions; everything else lives in a warm grayscale, so a periwinkle card surface (#cfdaf5) and soft pastel gradient washes (coral, sky, mint, gold) read as deliberate punctuation rather than noise. Components lean on hairline borders and 100px pill containers rather than shadows, and the rhythm stays calm and spacious with 40px card padding and generous vertical breathing room between sections.

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Parchment | `#f6f3f1` | `--color-parchment` | Page canvas and the majority of surface fills — this warm off-white IS the brand's signature surface, immediately distinguishing the site from pure-white SaaS templates |
| Lake Blue | `#2b59d1` | `--color-lake-blue` | Violet wash for highlight backgrounds, decorative bands, and soft emphasis behind content. Do not promote it to the primary CTA color |
| Periwinkle Mist | `#cfdaf5` | `--color-periwinkle-mist` | Muted UI surface for disabled controls, low-emphasis panels, and placeholder blocks. |
| Sky Blue | `#a0b5eb` | `--color-sky-blue` | Decorative gradient stop — appears in atmospheric washes and the pipeline diagram's flow lines, never as a UI fill |
| Mint | `#a7fccd` | `--color-mint` | Supporting palette color for small decorative accents when the core palette needs contrast. |
| Coral | `#ff9473` | `--color-coral` | Supporting palette color for small decorative accents when the core palette needs contrast. |
| Gold | `#ecda98` | `--color-gold` | Decorative gradient stop — warm accent in gradient washes, never used in functional UI |
| Crimson | `#f37a0a` | `--color-crimson` | Decorative gradient stop — deep warm tone in gradient washes alongside gold and coral |
| Off-Black | `#242424` | `--color-off-black` | High-contrast neutral action fill for primary buttons on light surfaces. |
| Ink | `#000000` | `--color-ink` | Announcement bar surface and certain heading fills — the black band at the top of the page and select heading contexts |
| Graphite | `#4e4d4d` | `--color-graphite` | Secondary text — body copy and sub-headings that need less weight than primary headlines |
| Smoke | `#797776` | `--color-smoke` | Muted helper text and tertiary links |
| Ash | `#cecac8` | `--color-ash` | Hairline borders — 1px solid lines separating sections, outlining pipeline diagram nodes, and defining card edges |

## Tokens — Typography

### ABC Diatype Mono — Body text, navigation, buttons, badges, tags, and ALL UI strings. The monospace choice across every functional element gives the interface its technical-manual character — body copy at 16-20px reads as data, not marketing. Nav labels and badges use 18px uppercase with tighter tracking; small print and meta text use 12px uppercase. Weight 500 is reserved for emphasized UI labels. · `--font-abc-diatype-mono`
- **Substitute:** JetBrains Mono, IBM Plex Mono, or Space Mono
- **Weights:** 400, 500
- **Sizes:** 12px, 14px, 16px, 18px, 20px, 28px
- **Line height:** 1.0–1.35 (varies by size)
- **Letter spacing:** -0.033em at 12px, -0.025em at 16px, -0.022em at 18px, -0.02em at 14px and 20px, -0.014em at 28px
- **Role:** Body text, navigation, buttons, badges, tags, and ALL UI strings. The monospace choice across every functional element gives the interface its technical-manual character — body copy at 16-20px reads as data, not marketing. Nav labels and badges use 18px uppercase with tighter tracking; small print and meta text use 12px uppercase. Weight 500 is reserved for emphasized UI labels.

### Untitled Serif — Display and heading type only — used at 80px (hero), 48px (section), 40px and 32px (sub-section), 24px (feature card titles). Weight is locked at 400 across all sizes; the serif's natural contrast and the -0.02em letter-spacing do the heavy lifting instead of bold weight. This is the editorial confidence signature: headlines whisper through typographic refinement rather than shout through weight. · `--font-untitled-serif`
- **Substitute:** Times New Roman, Georgia, or any editorial serif with similar stroke contrast
- **Weights:** 400
- **Sizes:** 24px, 32px, 40px, 48px, 80px
- **Line height:** 1.2
- **Letter spacing:** -0.02em at all sizes (-1.6px at 80px, -0.96px at 48px, -0.8px at 40px, -0.64px at 32px, -0.48px at 24px)
- **Role:** Display and heading type only — used at 80px (hero), 48px (section), 40px and 32px (sub-section), 24px (feature card titles). Weight is locked at 400 across all sizes; the serif's natural contrast and the -0.02em letter-spacing do the heavy lifting instead of bold weight. This is the editorial confidence signature: headlines whisper through typographic refinement rather than shout through weight.

### Untitled Sans — Detected in extracted data but not described by AI · `--font-untitled-sans`
- **Weights:** 400
- **Sizes:** 16px
- **Line height:** 1.35
- **Letter spacing:** -0.02
- **Role:** Fallback neutral text

### Type Scale

| Role | Family | Weight | Size | Line Height | Letter Spacing | Token |
|------|--------|--------|------|-------------|----------------|-------|
| caption | — | — | 12px | 1.2 | -0.4px | `--text-caption` |
| body-sm | — | — | 14px | 1.35 | -0.28px | `--text-body-sm` |
| body | — | — | 16px | 1.35 | -0.4px | `--text-body` |
| label | — | — | 18px | 1.2 | -0.4px | `--text-label` |
| body-lg | — | — | 20px | 1.35 | -0.4px | `--text-body-lg` |
| subheading | — | — | 24px | 1.2 | -0.48px | `--text-subheading` |
| heading-sm | — | — | 32px | 1.2 | -0.64px | `--text-heading-sm` |
| heading | — | — | 40px | 1.2 | -0.8px | `--text-heading` |
| heading-lg | — | — | 48px | 1.2 | -0.96px | `--text-heading-lg` |
| display | — | — | 80px | 1.2 | -1.6px | `--text-display` |

## Tokens — Spacing & Shapes

**Base unit:** 8px

**Density:** comfortable

### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| 8 | 8px | `--spacing-8` |
| 16 | 16px | `--spacing-16` |
| 24 | 24px | `--spacing-24` |
| 32 | 32px | `--spacing-32` |
| 40 | 40px | `--spacing-40` |
| 64 | 64px | `--spacing-64` |
| 72 | 72px | `--spacing-72` |
| 80 | 80px | `--spacing-80` |
| 200 | 200px | `--spacing-200` |
| 216 | 216px | `--spacing-216` |

### Border Radius

| Element | Value |
|---------|-------|
| tags | 9999px |
| cards | 40px |
| pills | 9999px |
| buttons | 100px |

### Shadows

| Name | Value | Token |
|------|-------|-------|
| md | `rgba(0, 0, 0, 0.1) 0px 0px 10px 0px` | `--shadow-md` |

### Layout

- **Page max-width:** 1432px
- **Section gap:** 64px
- **Card padding:** 40px
- **Element gap:** 16px

## Components

### Announcement Bar
**Role:** Top-of-page notification strip
Full-width black (#000000) bar, ~40px tall, containing mono text in white (#f6f3f1) at 14px and a small white pill button (9999px radius, white border, 12px uppercase text) anchored right. Close icon (×) in white at far right.

### Primary Pill Button (Blue)
**Role:** Primary conversion action
Lake Blue (#2b59d1) fill, white text in ABC Diatype Mono at 14px uppercase, 100px border-radius, 16px 32px padding, with a trailing arrow (▸) glyph in white. Height ~48px. This is the only saturated fill in the system.

### Primary Pill Button (Black)
**Role:** Secondary conversion action
Off-Black (#242424) fill, white text in ABC Diatype Mono at 14px uppercase, 100px border-radius, 16px 32px padding, no arrow. Height ~48px.

### Ghost Pill Button
**Role:** Tertiary navigation action
Transparent fill, 1px Off-Black (#242424) border, Off-Black text in ABC Diatype Mono at 14px uppercase, 100px border-radius, 16px 32px padding. Height ~48px.

### Text Link with Arrow
**Role:** Navigation link with directional indicator
Transparent fill, Off-Black (#242424) text in ABC Diatype Mono at 14px, trailing rightward arrow (→) in Off-Black. No background or border. Uppercase tracking.

### Feature Card
**Role:** Product capability card with icon, title, description
Transparent or Parchment fill, 1px Ash (#cecac8) border, 40px border-radius, 40px padding. Small mono icon (20px) in top-left at 16px padding offset. Title in Untitled Serif at 24px weight 400, Off-Black. Body in ABC Diatype Mono at 16px weight 400, Graphite (#4e4d4d). No shadow.

### Elevated Feature Card (Periwinkle)
**Role:** Hero feature card with gradient illustration
Periwinkle Mist (#cfdaf5) fill, 40px border-radius, 40px padding. Contains a large gradient illustration on the right side using Coral → Sky Blue → Mint washes. Title in Untitled Serif 24px, body in mono 16px. This is the one card that uses a colored surface to draw the eye.

## Do's and Don'ts

### Do
- Use Untitled Serif at weight 400 for all headings — never go bold; the serif's stroke contrast and -0.02em tracking carry the weight visually
- Use ABC Diatype Mono for all body copy, buttons, nav labels, badges, and functional UI text — the monospace IS the brand voice
- Set all button and tag border-radius to 100px or 9999px — pill shapes are the container language of this system
- Use Parchment (#f6f3f1) as the page canvas — never substitute pure white (#ffffff); the warm tint is signature
- Reserve Lake Blue (#2b59d1) exclusively for the single primary action per screen; all other buttons use Off-Black or ghost variants
- Use 1px solid Ash (#cecac8) for all borders and dividers — avoid thicker weights or darker border colors
- Apply uppercase + tight tracking to all nav labels, buttons, and tag text via the monospace family

### Don't
- Never set headings in bold or 600+ weight — Untitled Serif headlines stay at 400 across all sizes
- Never use pure white (#ffffff) as a page background — always use Parchment (#f6f3f1) to preserve the warm surface
- Never use Lake Blue (#2b59d1) for anything other than the single primary action fill — it loses meaning if scattered
- Never substitute a sans-serif for the monospace body font — the mono/serif pairing is the defining typographic gesture
- Never apply drop shadows to cards — use 1px Ash borders and surface color contrast (Parchment → Periwinkle) for elevation instead
- Never use corner radii below 16px on cards or below 100px on buttons — the system is pill-and-soft-rect, never sharp
- Never introduce additional accent colors for UI elements — the pastel palette (Sky, Mint, Coral, Gold) is decorative-only and belongs in illustrations and gradient washes
