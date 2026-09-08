## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2024-05-25 - [Tkinter Keyboard Navigation & Focus]
**Learning:** In Tkinter applications, main input fields (like search or target domains) should automatically receive focus using `focus_set()` when the application/tab loads. Additionally, binding the `<Return>` key to the primary action using `.bind('<Return>', callback)` significantly improves workflow speed by reducing reliance on mouse clicks.
**Action:** When adding primary input fields in Tkinter, always add `widget.focus_set()` if it's the main entry point, and bind `<Return>` to the primary submit action. Remember to add `event=None` to the callback signature to handle Tkinter's event parameter.
