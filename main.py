import json

def normalize_ssid(raw_ssid: str) -> str:
    ssid = raw_ssid.strip()
    if not ssid.startswith("42"):
        return ssid
    try:
        parsed = json.loads(ssid[2:])
        if (
            isinstance(parsed, list)
            and len(parsed) >= 2
            and isinstance(parsed[1], dict)
        ):
            auth_data = parsed[1]
            if "session" not in auth_data and "sessionToken" in auth_data:
                auth_data["session"] = auth_data["sessionToken"]
            return "42" + json.dumps(parsed, separators=(",", ":"))
    except Exception:
        logger.exception("Failed to normalize SSID; passing raw value.")
    return ssid
