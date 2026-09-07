## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2025-02-15 - [Improve focus management and keyboard accessibility]
**Learning:** By default, Tkinter entry fields do not automatically gain focus, requiring a mouse click to start interacting. This interrupts user flow. Additionally, `<Return>` key presses inside entry fields are not natively bound to the form's primary action button, requiring users to switch back to the mouse to submit.
**Action:** When adding critical input fields (like the target domain entry) in Tkinter, use `.focus_set()` for immediate keyboard interactivity, and bind the `<Return>` key (`.bind('<Return>', callback)`) to trigger the main form action, remembering to update the target method to accept the `event` parameter.
