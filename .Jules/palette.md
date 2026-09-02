## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2026-09-02 - [Keyboard Accessibility & Interaction feedback for Tkinter widgets]
**Learning:** Tkinter `tk.Entry` forms don't inherently bind the Enter key to the primary logical action of that form, leading to a friction point for keyboard-oriented users. Additionally, similar to buttons, `tk.Radiobutton` elements lack hover cursor feedback by default.
**Action:** When adding main input fields (`tk.Entry`), auto-focus them via `.focus_set()` and bind `<Return>` to the primary submit action to enhance keyboard accessibility. Also, expand the `cursor="hand2"` rule to apply to `tk.Radiobutton` elements as well for consistent interactive affordance.
