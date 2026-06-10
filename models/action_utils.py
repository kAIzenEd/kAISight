# -*- coding: utf-8 -*-


def prepare_act_window_action(action):
    """Ensure act_window dicts include a ``views`` key (required by the web client)."""
    action = dict(action)
    if action.get("views"):
        action["views"] = [tuple(v) for v in action["views"]]
        return action
    view_mode = (action.get("view_mode") or "list,form").strip()
    modes = [m.strip() for m in view_mode.split(",") if m.strip()]
    if not modes:
        modes = ["list", "form"]
    action["view_mode"] = ",".join(modes)

    view_id = action.pop("view_id", False)
    if isinstance(view_id, (list, tuple)):
        view_id = view_id[0]

    if len(modes) == 1:
        action["views"] = [(view_id or False, modes[0])]
    else:
        if view_id:
            raise ValueError(
                "Cannot combine a fixed view_id with multiple view modes."
            )
        action["views"] = [(False, mode) for mode in modes]
    return action
