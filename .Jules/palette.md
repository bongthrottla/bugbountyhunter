## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2024-05-24 - [Keyboard accessibility in Tkinter forms]
**Learning:** By default, Tkinter entry widgets do not capture the `<Return>` key to trigger form submissions, and applications may not focus the primary input field upon launch. This leads to a poor keyboard accessibility experience, forcing users to reach for the mouse to start core actions like running a scan.
**Action:** When creating forms in Tkinter applications for this repo, ensure the primary input field is focused on startup using `.focus_set()`, and bind the `<Return>` key to the primary action (e.g., `.bind('<Return>', self.submit_action)`) making sure the action method signature accepts the event parameter (`def submit_action(self, event=None):`).
