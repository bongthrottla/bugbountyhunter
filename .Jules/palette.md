## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.
## 2024-05-24 - [Add autofocus and Enter key bind to target entry]
**Learning:** Users benefit from being able to immediately type their target domain when the application opens, and submitting via Enter key speeds up their workflow.
## 2024-05-24 - [Add autofocus and Enter key bind to target entry]
**Learning:** Users benefit from being able to immediately type their target domain when the application opens, and submitting via Enter key speeds up their workflow.
**Action:** Always consider `focus_set()` on primary inputs and binding `<Return>` to main actions in forms.
