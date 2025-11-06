import os, shutil, datetime

class BackupManager:
    def __init__(self, root="profiles"):
        self.root = root

    def jar_backup_path(self, jar_path: str) -> str:
        return jar_path + ".backup"

    def ensure_backup(self, jar_path: str):
        bak = self.jar_backup_path(jar_path)
        if not os.path.exists(bak):
            shutil.copy2(jar_path, bak)
        return bak

    def dat_rollback_dir(self, profile_name="default"):
        d = os.path.join(self.root, profile_name, "backups", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.makedirs(d, exist_ok=True)
        return d
