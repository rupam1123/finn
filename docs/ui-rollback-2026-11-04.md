# UI rollback · 4 November 2026

At the user’s request, restore the pre-redesign app presentation from commit d1ae33d. Retain the new FINN welcome page and the rolling company picker. Remove installation of press-and-slide navigation: the bottom bar uses taps only. Financial data, backend logic, evidence, explicit AI generation rules and read-only mode are preserved. Existing Ask FINN functionality stays accessible from the company header.

The old styles and routed page structures are restored; welcome, picker and assistant styles are scoped to their respective components. The recent shared disclosure/control redesign is no longer loaded. Historical design notes describe superseded checkpoints. Deployment remains paused.
