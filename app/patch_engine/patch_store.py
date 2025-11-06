import os, json, datetime
from app.safety.hashes import sha256_json

class PatchStore:
    def __init__(self, profile_dir="profiles/default"):
        self.dir = profile_dir
        os.makedirs(self.dir, exist_ok=True)
        self.file = os.path.join(self.dir, "patches.jsonl")

    def record_patch(self, type_name: str, key: str, new_data: dict, base_hash: str):
        patch = {
            "id": f"{type_name}:{key}:{datetime.datetime.utcnow().isoformat()}Z",
            "target": {"type": type_name, "key": key, "baseHash": base_hash},
            "ops": [{"op":"replace","path":"/","value":new_data}],
            "hash": sha256_json(new_data),
            "created": datetime.datetime.utcnow().isoformat()+"Z"
        }
        with open(self.file, "a", encoding="utf-8") as f:
            f.write(json.dumps(patch, ensure_ascii=False) + "\n")

    def load_all(self) -> list[dict]:
        if not os.path.exists(self.file): return []
        with open(self.file, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
