# app/data/dat_parser.py
import os, json, subprocess, tempfile
from typing import List, Dict, Any

# tools/java relative to this file: app/data -> ../../tools/java
JAVA_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tools", "java"))
DUMP_MAIN = "DumpLoadouts"
WRITE_MAIN = "WriteLoadouts"


def _java_classpath(dotjar: str) -> str:
    helper_root = os.path.abspath(JAVA_DIR)
    if dotjar:
        return os.pathsep.join([helper_root, dotjar])
    return helper_root


def _ensure_java_helper(main: str, classpath: str | None = None) -> None:
    source = os.path.join(JAVA_DIR, f"{main}.java")
    if not os.path.exists(source):
        raise FileNotFoundError(source)
    target = os.path.join(JAVA_DIR, f"{main}.class")
    needs_compile = not os.path.exists(target) or os.path.getmtime(target) < os.path.getmtime(source)
    if not needs_compile:
        return
    cmd = ["javac"]
    if classpath:
        cmd.extend(["-cp", classpath])
    cmd.append(source)
    proc = subprocess.run(cmd, cwd=JAVA_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "javac failed")

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
        if not os.path.exists(dotjar):
            return [{
                "key": f"raw_{type_name.lower()}",
                "name": "DOT.jar not found",
                "error": dotjar
            }]
        try:
            _ensure_java_helper(DUMP_MAIN, _java_classpath(dotjar))
        except Exception as exc:
            return [{
                "key": f"raw_{type_name.lower()}",
                "name": "Java helper compile failed",
                "error": str(exc)
            }]
        cmd = [
            "java",
            "-Dfile.encoding=UTF-8",         # force UTF-8 stdout on Windows
            "-cp", _java_classpath(dotjar),
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
    preview = os.path.splitext(path)[0] + ".json"
    os.makedirs(os.path.dirname(preview), exist_ok=True)
    with open(preview, "w", encoding="utf-8", newline="\n") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    if type_name == "Loadouts":
        _write_loadouts(path, records)


def _write_loadouts(path: str, records: List[Dict[str, Any]]):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    dotjar = _dot_jar()
    if not os.path.exists(dotjar):
        raise FileNotFoundError(dotjar)
    try:
        _ensure_java_helper(WRITE_MAIN, _java_classpath(dotjar))
    except Exception as exc:
        raise RuntimeError(f"javac failed for {WRITE_MAIN}: {exc}") from exc

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".json") as tmp:
        json.dump(records, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        cmd = [
            "java",
            "-Dfile.encoding=UTF-8",
            "-cp", _java_classpath(dotjar),
            WRITE_MAIN,
            path,
            tmp_path,
        ]
        proc = subprocess.run(cmd, cwd=JAVA_DIR, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "WriteLoadouts failed")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
