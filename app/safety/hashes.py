import hashlib, json

def sha256_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()

def sha256_json(d: dict) -> str:
    return sha256_bytes(json.dumps(d, sort_keys=True).encode("utf-8"))
