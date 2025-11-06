# app/data/dat_parser.py
import os, json, subprocess
from typing import List, Dict, Any

# tools/java relative to this file: app/data -> ../../tools/java
JAVA_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tools", "java"))
DUMP_MAIN = "DumpLoadouts"

def _is_java_serialized(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            hdr = f.read(2)
        return len(hdr) >= 2 and hdr[0] == 0xAC and hdr[1] == 0xED
    except Exception:
        return False

def _dot_jar() -> str:
    env = os.getenv("DOT_JAR_PATH")
    if env and os.path.exists(env):
        return env
    # fallback guess
    return r"C:\Program Files (x86)\Steam\steamapps\common\The Doors of Trithius\DOT.jar"

def parse_dat(path: str, type_name: str) -> List[Dict[str, Any]]:
    """Read modules/*.dat via Java helper (FileCache -> LoadoutsXml -> JSON arrays)."""
    if not os.path.exists(path):
        return [{"key": f"missing_{type_name.lower()}",
                 "name": f"{type_name} file not found"}]

    if _is_java_serialized(path):
        dotjar = _dot_jar()
        cmd = [
            "java",
            "-Dfile.encoding=UTF-8",         # force UTF-8 stdout on Windows
            "-cp", f".;{dotjar}",
            DUMP_MAIN, path, "true"          # arrays=true
        ]
        # capture as BYTES; we’ll decode ourselves
        proc = subprocess.run(cmd, cwd=JAVA_DIR, capture_output=True)
        if proc.returncode != 0:
            err = (proc.stderr or b"").decode("utf-8", "ignore")
            return [{
                "key": f"raw_{type_name.lower()}",
                "name": "Java deserialization failed",
                "error": err.strip()
            }]

        raw = proc.stdout or b""
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("cp1252", errors="replace")  # Windows fallback

        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            return [{"key": f"raw_{type_name.lower()}",
                     "name": "Unexpected helper output"}]
        except Exception as e:
            return [{
                "key": f"raw_{type_name.lower()}",
                "name": "Bad JSON from helper",
                "error": str(e),
                "firstOut": text[:400]
            }]

    # Fallback for future plain-text files (not used for loadouts)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    return [{"key": f"raw_{type_name.lower()}",
             "name": f"Unparsed {type_name}",
             "raw": txt[:4000]}]

def serialize_dat(path: str, type_name: str, records: List[Dict[str, Any]]):
    """
    V1: don’t rewrite the Java-serialized .dat yet.
    Write a preview JSON next to it so we can inspect diffs.
    (The writer helper will replace this in the next step.)
    """
    preview = os.path.splitext(path)[0] + ".json"
    os.makedirs(os.path.dirname(preview), exist_ok=True)
    with open(preview, "w", encoding="utf-8", newline="\n") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
