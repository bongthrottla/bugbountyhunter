## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.
## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2024-05-24 - [Add hand cursor to Tkinter radiobuttons]
**Learning:** Similar to standard buttons, Tkinter `tk.Radiobutton` widgets do not automatically change the mouse cursor when hovering over them, which can make them feel non-interactive.
**Action:** When adding or modifying radio buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to maintain interaction consistency.

## 2024-05-24 - [Add Entry Autofocus & Return Key Binding]
**Learning:** To improve keyboard accessibility and seamless data entry in Tkinter forms, the primary text input should auto-focus, and the `<Return>` key should submit the form. Without this, users are forced to manually click into fields and click submit buttons.
**Action:** In Tkinter apps, always `focus_set()` the most prominent entry and bind `<Return>` to the primary submit action using `bind('<Return>', callback)`. Ensure the target callback handles the optional `event` parameter.
