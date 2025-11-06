def apply_all(session, patch_store) -> list[dict]:
    """Apply naive replace patches; return list of conflicts."""
    conflicts = []
    for p in patch_store.load_all():
        t, k = p["target"]["type"], p["target"]["key"]
        try:
            new_data = p["ops"][0]["value"]
            session.update_record(t, k, new_data)
        except Exception as e:
            conflicts.append({"patch": p["id"], "error": str(e)})
    return conflicts
