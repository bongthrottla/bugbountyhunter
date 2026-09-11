## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2026-09-11 - [Improve keyboard accessibility for primary actions]
**Learning:** In Tkinter, primary action inputs (like main entry text boxes) do not automatically trigger their corresponding actions on `<Return>` key press, nor do they auto-focus on startup, hindering keyboard-only users.
**Action:** Always bind the `<Return>` key (`widget.bind('<Return>', method)`) to the primary action (e.g., submitting a form/scan) for the main text entry (`tk.Entry`) widget, update the target method to accept an `event=None` argument, and call `widget.focus()` to set initial keyboard focus to the most critical input upon opening the app.