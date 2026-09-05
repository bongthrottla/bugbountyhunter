## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2024-06-25 - [Add auto-focus and Enter key binding]
**Learning:** For desktop applications, users expect to be able to type immediately upon launch and trigger the primary action using the Enter key. Lacking these small workflow efficiencies is a noticeable friction point.
**Action:** Always auto-focus (`widget.focus_set()`) the most critical input field on startup. Bind the `<Return>` key (`widget.bind('<Return>', callback)`) to the main submit action, ensuring the callback method accepts an `event` parameter (e.g., `def callback(self, event=None)`).
