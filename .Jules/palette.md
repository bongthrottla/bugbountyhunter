## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2025-02-14 - [Add keyboard accessibility for Tkinter entries]
**Learning:** By default, Tkinter `tk.Entry` widgets don't trigger their primary associated action (like starting a search or scan) when the `<Return>` key is pressed, and they don't automatically receive focus when a form opens. This can make the app feel unintuitive and slow down keyboard navigation.
**Action:** Bind `<Return>` to the primary action function using `.bind('<Return>', function)` (remembering to add `event=None` to the function signature) and use `.focus_set()` to auto-focus primary input fields.
