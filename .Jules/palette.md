## 2024-05-24 - [Add hand cursor to Tkinter buttons]
**Learning:** By default, Tkinter `tk.Button` widgets do not change the mouse cursor when hovering over them. This creates a disconnect in standard modern UI expectations where clickable elements provide visual feedback on hover.
**Action:** When adding new buttons in Tkinter applications for this repo, ensure they explicitly set `cursor="hand2"` to match the new interactive pattern.

## 2024-05-24 - [Add Return key binding and focus to input fields]
**Learning:** For a better user experience and keyboard accessibility, input fields should allow users to submit forms by pressing Enter. Additionally, auto-focusing the primary input field upon application load saves the user a click.
**Action:** When adding or updating `tk.Entry` widgets that act as the primary input for an action, bind the `<Return>` key to the action method and set initial focus using `.focus_set()`. Ensure the action method signature accepts an `event` parameter (e.g., `event=None`).
