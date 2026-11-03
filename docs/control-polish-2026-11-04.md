# Disclosure and company picker polish · 4 November 2026

User feedback identified text-glyph arrows and a dense 18-company pill wall on Research.

- Shared DisclosureSummary renders a native summary with one aligned Lucide chevron, grouped text/metadata, visible keyboard focus and a 48px minimum target. It replaces 44 headings across current and retained legacy views. Text plus/minus/caret decorations are suppressed; the icon rotates with the native open state.
- Native select controls use a consistent vector chevron and spacing. The search close control uses the existing X icon.
- The compact saved-price ribbon has consistent spacing, borders, card widths and aligned metadata.
- Research uses one horizontal, centre-snapping company picker. The focused card is larger and highlighted; adjacent cards are faded. It starts on the second company when available so both neighbours can be seen. All exact 18 assessment companies are retained without repeating clones.
- Native touch scrolling, mouse dragging, previous/next controls and Left/Right/Home/End keys share the same selection. Browser scroll events coalesce into one animation frame. Selection does not fetch data or open a route; Research is an explicit action. Reduced motion uses immediate centring.
- Loading/missing research remain explicit. Company identity logos and fallback initials are preserved. No financial calculations, saved data, source jobs or AI generation behaviour changed.

Validation includes nine synthetic picker/disclosure regressions, existing workspace checks, TypeScript and production builds. Browser control reports disabled in Work settings. These checks do not establish pixel-level rendering, measured frame rate, native inertia or physical-device acceptance. Publication remains paused; source updates can go to GitHub.
