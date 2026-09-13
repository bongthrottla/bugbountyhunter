## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2024-05-25 - [Tkinter Accessibility]
**Learning:** By default, Tkinter `tk.Entry` input fields do not trigger form submission or main actions when pressing the Enter key, reducing keyboard accessibility. Additionally, they do not automatically receive focus.
**Action:** Always add `.bind('<Return>', submit_method)` to key input fields (ensuring the target method accepts an optional `event=None` argument) and call `.focus_set()` on the primary input field upon application startup.
