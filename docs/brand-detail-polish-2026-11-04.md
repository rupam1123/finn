# Targeted brand and control edits · 4 November 2026

Keep the restored workspace UI and tap-only navigation. This update is limited to the user's four marked areas:

- Replace the in-app F mark with the supplied letter artwork on transparent alpha, without a square/round background tile. The shared BrandMark is used in desktop/mobile headers and the welcome header; favicon metadata points to it too.
- Remove the rolling assessment picker's visible previous/next arrow buttons. Native swiping, mouse dragging, keyboard selection and the Research link remain.
- Add small local company logos to the saved-price ribbon. All 18 assessment symbols have saved logo assets. TMPV uses the shared Tata identity artwork from the provider's historical filename; no ticker mapping or financial history changes. Jyothy Labs artwork is from its official site. Asset URLs are retained in the logo manifest.
- Group Radar values with their labels, add clear filled range tracks, retain native keyboard/touch inputs and original thresholds/debounce, and stack only this control group on narrow screens.
- Place Ask FINN at the opposite end of the company header's back-link row, with a decorative Lucide Sparkles icon. It retains the existing evidence assistant and modal behaviour.

No backend financial calculations, source data, model execution flags, global navigation gestures or page structure are changed. Deployment remains paused.

## Logo asset and edit prompt

Saved app asset: `frontend/public/brand/finn-mark.png`. Built-in image_gen editing tool used with transparent_background enabled. Alpha inspected using the installed image library: hasAlpha=true, isOpaque=false, alpha range 0–255. No API key was added or saved.

Final prompt:

> Clean up the transparent F-logo cutout in image 1, with image 2 as the original artwork reference. Keep the identical stylized F silhouette, arrow, blue vertical bar and turquoise/teal ribbon facets and gradients. Remove ALL floating cyan/blue speckles, noise and fragments in the transparent negative spaces and outside the three solid logo shapes. Make boundaries clean, smooth, sharply antialiased, with fully transparent background and gaps. The result must be pristine finished brand artwork, not a rough extraction. No redesign, no glow, no shadows outside the letter, no text, no rectangular badge. Frame the F tightly with minimal transparent padding.

Validation uses the picker, welcome and existing workspace regressions, TypeScript and production builds. Any browser/device visual gate remains separate; no new physical-device or measured frame-rate claim is made.

## Typography and compact quarters

- Remove welcome pagination dots because this page has no slides.
- Apply the already verified SF Pro Display family, 400/500/600 roles, minus-one-percent tracking and explicit heading/body/control hierarchy across the actual app elements. Financial copy and source/period/status labels remain domain-specific; the reference app's trading/account or live-price copy is not substituted into FINN.
- SF Pro is not installed in the inspected Windows system font directory and no licensed distributable font asset exists in this repository. Local-only SF font faces and Apple system fonts are preferred; self-hosted DM Sans remains the fallback. Exact SF rendering on arbitrary Windows/Android machines is not claimed. Apple directs developers not to bundle its system fonts: https://developer.apple.com/documentation/technologyoverviews/fonts . No proprietary font is downloaded or redistributed.
- Each Say–Do quarter is now a compact native disclosure. Its period, existing evidence-gap/status and matched-comparison count stay visible when closed. The original reason, values, model assessments, management excerpts and delivered evidence remain inside. The two evidence sections have smaller separate native disclosures with direction icons and counts.
- Seven new regression checks cover nested disclosure expansion, preserved matched statuses, slider limits/outputs/debounced query updates, no writes during filtering, genuine logo alpha and all 18 ribbon logo mappings. Existing picker/welcome/workspace checks and production builds remain required.

## Completed verification

- 88 UI checks passed: 60 existing workspace checks, eight assistant checks, four welcome/asset checks, nine picker checks and seven final-detail checks. New checks use synthetic fixtures except actual local-logo alpha/file validation.
- Frontend TypeScript, Next production build, hosted TypeScript, Vinext production build and the hosted navigation namespace guard passed. No backend financial/parser/storage changes; no fresh provider/model run performed for this UI update.
- Browser control became available for this pass. Chromium review at the normal desktop viewport and 390×844 covered dark/light ETERNAL Say–Do quarter rows, quarter expansion and nested evidence, Ask FINN dialog open/close, Radar slider keyboard changes with restored values, native tap navigation, company logos, rolling picker drag (TCS to HDFCBANK), and welcome actions in both themes.
- Closed quarter rows measured 78px tall on both desktop and 390px layouts; no document horizontal overflow in checked views. After the fallback-font responsive correction, welcome actions fit inside the 844px viewport, with zero pagination-dot elements.
- Browser font inspection confirmed the intended family stack but `document.fonts.check('16px "FINN SF Display"')` returned false on this Windows machine. Exact SF glyph rendering is therefore still a platform/font-availability limitation, not a passed gate. No Apple font file is bundled.
- Browser console had no error entries in the inspected session. Screenshots are retained locally under ignored `.deployment-data/final-ui-20261104/`; these are browser emulation checks, not physical iPhone/Android/Safari certification.

Both source branches are prepared for GitHub upload. Site deployment and account/access changes remain paused under the user's prior instruction.
