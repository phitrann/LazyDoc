# Design System

## Overview
DeepWiki's visual system is a high-density, dark-themed utility interface designed for technical users and developers. It is heavily influenced by the "shadcn/ui" aesthetic, featuring a monochromatic foundation punctuated by vibrant accent colors like Pacific Blue (#6096FF) and Ray Orange (#FFAA47). The layout is compact and grid-heavy, utilizing a split-pane structure typical of developer tools. Subtle motion cues like pulsed gradients ("powered-by-devin-gradient") and transition-on-hover effects for repository cards create a sense of active, AI-driven responsiveness.

## Colors
### Core Palette
- **Background**: `#000000` (Main background through Tailwind `bg-background`)
- **Surface**: `#181818` (Secondary surface for cards and components)
- **Secondary Surface**: `#202020` (Hover states and tertiary layers)
- **Component BG**: `#252525` (Internal component fills)
- **Border**: `#2a2a2a` (Default dashed and solid border color)
- **Border Hover**: `#454545` (Increased contrast on interaction)

### Text
- **Primary**: `#CBCBCB` (High-readability light gray)
- **Secondary**: `#8F8F8F` (Metadata and descriptions)
- **Muted**: `oklch(70.7% .022 261.325)` (Tertiary text labels)

### Accents
- **Pacific Blue**: `#6096FF` (Link primary, highlights)
- **Ray Orange**: `#FFAA47` (Link hover, status indicators)
- **Devin Green**: `#21C19A` (Active AI/agent branding)
- **Deep Blue**: `#3969CA` (Branding and gradient segments)

## Typography
- **Primary Font**: `Geist`, `sans-serif` (Variable weight 100-900). Used for all body copy and primary UI labels.
- **Mono Font**: `Geist Mono`, `monospace`. Used for repository names, code snippets, and specific technical metadata.
- **Sizing Hierarchy**:
  - **Small (xs)**: `0.75rem` (Used for repository descriptions and star counts)
  - **Base**: `1.0rem` (Default UI text)
  - **Large (lg)**: `1.125rem` (Section headers)
  - **Heading (2xl-4xl)**: `1.5rem` to `2.25rem` (Primary titles)
- **Weights**: Medium (500) for standard labels, Semibold (600) for active items.

## Elevation
- **Border Reliance**: High. The system uses borders rather than deep shadows to define space. `border-dashed` is frequently used on persistent structural lines (navigation/sidebar).
- **Layering**: Flat-to-slightly-raised. Components use `bg-surface` contrast against `bg-background` to imply depth.
- **Shadows**: Minimal usage of `shadow-sm` or `shadow-none` for repository cards, relying instead on background color shifts (`bg-surface-hover`) to indicate state.
- **Glass/Blur**: Occasional use of `backdrop-blur-md` for sticky headers and popover overlays.

## Components
- **Repository Card**: A compact block with a 1px border (`border-border`), `bg-surface` fill, and rounded corners (`rounded-md`). Contains a header (org/repo), a `line-clamp-2` description, and a footer with star counts and a circular arrow icon button.
- **Navigation Sidebar**: A vertical container with a fixed or sticky layout, utilizing dashed borders for structural separation.
- **AI Status Bar**: A specialized horizontal element at the top using the `powered-by-devin-gradient` and animated SVG paths for pulse effects.
- **Prose Blocks**: Rich text content utilizing the Tailwind Typography plugin style, specifically optimized for dark mode with Pacific Blue link colors.

## Do's and Don'ts
### Do's
- Use Geist Mono for any text representing file paths, repository handles, or code strings.
- Use dashed borders for primary layout structural lines (sidebars, persistent headers).
- Implement `transition-colors` with a duration of `150ms` for all interactive card components.
- Maintain a strictly dark background to ensure accent colors pop.

### Don'ts
- Do not use large, soft drop shadows; the aesthetic is "modern flat."
- Do not use sharp white for text; use the primary light gray (`#CBCBCB`) to reduce eye strain.
- Avoid rounded corners greater than `rounded-lg` (approx. 8px) for standard cards.

## Assets
- **Webpack Script**: https://deepwiki.com/_next/static/chunks/webpack-6c4d7b978beb885b.js?dpl=dpl_8ToKKCUmAcd5v6bzkY2d8GP64sAJ
- **Font Geist Latin**: https://deepwiki.com/_next/static/media/4cf2300e9c8272f7-s.p.woff2
- **Font Geist Greek/Cyrillic**: https://deepwiki.com/_next/static/media/747892c23ea88013-s.woff2
- **Font Geist Ext**: https://deepwiki.com/_next/static/media/8d697b304b401681-s.woff2
- **Font Geist Mono Latin**: https://deepwiki.com/_next/static/media/93f479601ee12b01-s.p.woff2
- **Font Geist Mono Greek**: https://deepwiki.com/_next/static/media/9610d9e46709d722-s.woff2
- **Font Geist Secondary**: https://deepwiki.com/_next/static/media/ba015fad6dcf6784-s.woff2
- **Meta Image Width**: https://deepwiki.com/1200
- **Meta Image Height**: https://deepwiki.com/630
- **Apple Touch Icon**: https://deepwiki.com/apple-icon.png?a4f658907db0ab87
- **Twitter OG Image**: https://deepwiki.com/deepwiki_og_image.png
- **Favicon**: https://deepwiki.com/favicon.ico
- **Rel Icon PNG**: https://deepwiki.com/icon.png?1ee4c6a68a73a205
- **OG Image Type/PNG**: https://deepwiki.com/image/png
- **Main OG Image**: https://deepwiki.com/opengraph-image.png?8391a278ea71bf13