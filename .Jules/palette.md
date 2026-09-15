## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2025-02-28 - [Keyboard accessibility in Tkinter forms]
**Learning:** Tkinter entry fields do not automatically trigger form submission on `<Return>` and require explicit focus management. Users expect to type and hit enter without using the mouse.
**Action:** Bind `<Return>` to the primary action for `tk.Entry` fields (updating the target method to accept an `event` parameter) and use `focus_set()` on the primary input field to support keyboard-only navigation.
