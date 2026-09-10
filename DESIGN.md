---
version: alpha
name: CDM AI Assistant
description: A focused, trustworthy chat workspace for technical and operational consultation.
colors:
  brand-wine: "#71211A"
  brand-wine-soft: "#9C3D3B"
  brand-navy: "#1A2C52"
  brand-blue: "#1A4E85"
  brand-gold: "#EBAA35"
  brand-charcoal: "#1D1D1B"
  text-secondary: "#526071"
  surface: "#FFFFFF"
  canvas: "#F4F6F9"
  border: "#DDE3EC"
  dark-canvas: "#171717"
  dark-surface: "#222222"
  dark-border: "#3A3A3A"
  dark-text: "#F5F5F5"
typography:
  display: {fontFamily: Outfit, fontSize: 30px, fontWeight: 650, lineHeight: 1.12}
  heading: {fontFamily: Outfit, fontSize: 21px, fontWeight: 650, lineHeight: 1.25}
  body: {fontFamily: Outfit, fontSize: 15px, fontWeight: 400, lineHeight: 1.6}
  label: {fontFamily: Outfit, fontSize: 13px, fontWeight: 500, lineHeight: 1.35}
  caption: {fontFamily: Outfit, fontSize: 12px, fontWeight: 400, lineHeight: 1.4}
rounded:
  control: 10px
  container: 14px
  pill: 999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 20px
  xl: 28px
  xxl: 40px
components:
  sidebar: {backgroundColor: "{colors.brand-navy}", textColor: "{colors.surface}", width: 272px}
  message: {backgroundColor: "{colors.surface}", rounded: "{rounded.container}", padding: 20px}
  control: {rounded: "{rounded.control}", height: 44px}
  primary-button: {backgroundColor: "{colors.brand-blue}", textColor: "{colors.surface}", rounded: "{rounded.control}"}
---

# CDM AI Assistant

## Overview
A calm, precise workspace for CDM users who need answers without losing context. The interface balances a dark navigational rail with a clear reading surface. It should feel dependable before it feels clever.

## Colors
Wine is the CDM brand signal. Navy anchors navigation and identity. Blue is reserved for the primary action and focus states. Gold marks attention without becoming a competing action color. The canvas is cool and quiet so long responses remain readable.
## Dark Mode
Dark mode keeps the navy navigation rail and shifts the reading surface to dark navy-blue layers. Text remains cool white, borders become blue-gray, and the same wine, blue, and gold accents remain reserved for their existing actions. The selected theme persists locally and respects the system preference on first visit.

## Typography
Outfit is used throughout with weights 400, 500, and 650. Body copy stays open and readable. Numeric metadata uses tabular numerals so timestamps and counts align.

## Layout
The desktop shell uses a 272px sidebar and a centered reading column capped near 768px. The sidebar becomes a drawer below 768px. Core spacing follows the 4px base scale.

## Elevation & Depth
Prefer borders and tonal separation over heavy shadows. Containers use a subtle border and a restrained shadow only where a layer must separate from the canvas.

## Shapes
Controls use 10px radii. Main containers and message surfaces use 14px. Pills are reserved for compact status labels and never for primary content blocks.

## Components
- Sidebar: dark navy, compact navigation, visible active state, keyboard accessible.
- Primary action: blue fill with white text and a clear focus ring.
- Input: white surface, border, generous vertical padding, visible disabled state.
- Message: user messages use a pale wine tint; assistant messages use white and a narrow wine accent.

## Do's and Don'ts
- Do keep one clear primary action per view.
- Do preserve focus visibility and WCAG AA contrast.
- Do use Lucide icons consistently and pair icons with accessible labels.
- Don't use gradients, decorative emojis, or dense dashboard ornament.
- Don't put secrets, access tokens, or image bytes in persistent browser storage.
