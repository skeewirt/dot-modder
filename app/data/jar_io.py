import os, zipfile, json, tempfile, shutil, re
from .dat_parser import parse_dat, serialize_dat
from app.safety.backups import BackupManager
from app.safety.atomic import atomic_replace
from app.safety.hashes import sha256_json

class JarSession:
    def __init__(self, jar_path: str, workdir: str, backups: BackupManager):
        self.jar_path = jar_path
        self.workdir = workdir
        self.backups = backups
        self._cache = {}        # {(type,key): dict}
        self._original = {}     # {(type,key): dict}
        self._resolved = {}     # {"Loadouts": abs_path}

    @classmethod
    def open(cls, jar_path: str, backups: BackupManager) -> "JarSession":
        if not os.path.exists(jar_path): raise FileNotFoundError(jar_path)
        backups.ensure_backup(jar_path)
        workdir = tempfile.mkdtemp(prefix="dotmodder_")
        with zipfile.ZipFile(jar_path, "r") as z:
            z.extractall(workdir)
        print(f"[DoT-Modder] Extracted JAR to: {workdir}")
        return cls(jar_path, workdir, backups)

    def _find_in_modules(self, name_regex: str) -> str|None:
        """Search extracted workdir for modules/<something> that matches the regex."""
        rx = re.compile(name_regex, re.IGNORECASE)
        for root, _, files in os.walk(self.workdir):
            # Look only under *modules* dirs to keep it fast
            if "modules" not in root.replace("\\","/").lower():
                continue
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), self.workdir).replace("\\","/")
                if rx.search(rel):
                    path = os.path.join(self.workdir, rel)
                    print(f"[DoT-Modder] Auto-located: {rel}")
                    return path
        return None

    def _dat_path(self, type_name: str) -> str:
        if type_name in self._resolved:
            return self._resolved[type_name]

        if type_name == "Loadouts":
            # Try common locations first
            candidates = [
                "modules/loadouts.dat",
                "dot/modules/loadouts.dat",
            ]
            for rel in candidates:
                p = os.path.join(self.workdir, rel)
                if os.path.exists(p):
                    self._resolved[type_name] = p
                    print(f"[DoT-Modder] Using Loadouts at: {rel}")
                    return p
            # Fallback: search anywhere under modules for a file with 'loadouts' in the name and .dat
            found = self._find_in_modules(r"modules/.*/?loadouts.*\.dat$|modules/loadouts\.dat$")
            if not found:
                print("[DoT-Modder] Loadouts .dat not found in JAR extraction.")
                # keep a best-guess path so error messages have a filename
                found = os.path.join(self.workdir, "modules", "loadouts.dat")
            self._resolved[type_name] = found
            return found

        raise KeyError(f"Unsupported type: {type_name}")

    def list_records(self, type_name: str) -> list[str]:
        path = self._dat_path(type_name)
        print(f"[DoT-Modder] Reading {type_name} from: {os.path.relpath(path, self.workdir).replace('\\','/')}")
        data = parse_dat(path, type_name)
        keys = []
        for rec in data:
            k = rec.get("key") or rec.get("id")
            if k:
                keys.append(k)
                self._cache[(type_name,k)] = rec
                self._original.setdefault((type_name,k), json.loads(json.dumps(rec)))
        if not keys:
            print(f"[DoT-Modder] No records parsed for {type_name}.")
        return keys

    def get_record(self, type_name: str, key: str) -> dict:
        return json.loads(json.dumps(self._cache[(type_name,key)]))

    def update_record(self, type_name: str, key: str, new_data: dict):
        self._cache[(type_name,key)] = new_data
        allrecs = [v for (t,k),v in self._cache.items() if t==type_name]
        serialize_dat(self._dat_path(type_name), type_name, allrecs)
        self._repack()

    def restore_record(self, type_name: str, key: str):
        orig = self._original[(type_name,key)]
        self.update_record(type_name, key, json.loads(json.dumps(orig)))

    def restore_object_type(self, type_name: str):
        # Restore the file from the .backup jar
        bak = self.backups.jar_backup_path(self.jar_path)
        with zipfile.ZipFile(bak, "r") as z:
            target = self._dat_path(type_name)
            rel = os.path.relpath(target, self.workdir).replace("\\","/")
            tmp = tempfile.mkdtemp()
            try:
                z.extract(rel, tmp)
                shutil.copy2(os.path.join(tmp, rel), target)
            except KeyError:
                print(f"[DoT-Modder] Could not find {rel} in backup JAR.")
        self._reload_type(type_name)
        self._repack()

    def restore_all(self):
        bak = self.backups.jar_backup_path(self.jar_path)
        atomic_replace(bak, self.jar_path)

    def base_hash(self, type_name: str, key: str) -> str:
        return sha256_json(self._original[(type_name,key)])

    def _reload_type(self, type_name: str):
        for (t,k) in list(self._cache.keys()):
            if t==type_name:
                del self._cache[(t,k)]
                del self._original[(t,k)]
        self.list_records(type_name)

    def _repack(self):
        tmp = self.jar_path + ".tmp.zip"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(self.workdir):
                for f in files:
                    abspath = os.path.join(root, f)
                    rel = os.path.relpath(abspath, self.workdir)
                    z.write(abspath, rel)
        atomic_replace(tmp, self.jar_path)
