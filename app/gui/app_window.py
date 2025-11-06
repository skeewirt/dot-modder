from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QFileDialog, QToolBar, QMessageBox
from PySide6.QtGui import QAction
from .panes.object_types import ObjectTypesPane
from .panes.record_list import RecordListPane
from .panes.record_editor import RecordEditorPane
from app.data.jar_io import JarSession
from app.safety.backups import BackupManager
from app.patch_engine.patch_store import PatchStore

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DoT Modder (MVP)")
        self.resize(1200, 800)

        # Core services
        self.session = None
        self.patch_store = PatchStore()
        self.backups = BackupManager()

        # Panes
        self.types_pane = ObjectTypesPane(on_select=self.on_type_selected)
        self.list_pane = RecordListPane(on_select=self.on_record_selected)
        self.editor_pane = RecordEditorPane(
            on_save=self.on_record_save,
            on_restore=self.on_record_restore
        )

        # Layout
        central = QWidget(self); layout = QHBoxLayout(central)
        layout.addWidget(self.types_pane, 1)
        layout.addWidget(self.list_pane, 2)
        layout.addWidget(self.editor_pane, 3)
        self.setCentralWidget(central)

        # Toolbar
        tb = QToolBar("Main", self); self.addToolBar(tb)
        open_act = QAction("Open DOT.jar", self, triggered=self.open_jar)
        reapply_act = QAction("Reapply My Changes", self, triggered=self.reapply_changes)
        restore_type_act = QAction("Restore This Object Type", self, triggered=self.restore_object_type)
        restore_all_act = QAction("Restore All to Default", self, triggered=self.restore_all)
        tb.addAction(open_act); tb.addSeparator()
        tb.addAction(reapply_act); tb.addSeparator()
        tb.addAction(restore_type_act)
        tb.addAction(restore_all_act)

        self.update_enables(False)

    def update_enables(self, enabled: bool):
        self.types_pane.setEnabled(enabled)
        self.list_pane.setEnabled(enabled)
        self.editor_pane.setEnabled(enabled)

    def open_jar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select DOT.jar", filter="JAR Files (*.jar)")
        if not path: return
        try:
            self.session = JarSession.open(path, self.backups)
            self.types_pane.load_types(["Loadouts"])
            self.list_pane.clear()
            self.editor_pane.clear()
            self.update_enables(True)
        except Exception as e:
            QMessageBox.critical(self, "Open failed", str(e))

    def on_type_selected(self, type_name: str):
        if not self.session: return
        self.list_pane.set_type(type_name)
        records = self.session.list_records(type_name)
        self.list_pane.load_records(records)

    def on_record_selected(self, type_name: str, key: str):
        if not self.session: return
        data = self.session.get_record(type_name, key)
        self.editor_pane.load_record(type_name, key, data)

    def on_record_save(self, type_name: str, key: str, new_data: dict):
        if not self.session: return
        self.session.update_record(type_name, key, new_data)
        self.patch_store.record_patch(type_name, key, new_data, base_hash=self.session.base_hash(type_name, key))
        QMessageBox.information(self, "Saved", f"{type_name}:{key} saved (patch recorded).")

    def on_record_restore(self, type_name: str, key: str):
        if not self.session: return
        self.session.restore_record(type_name, key)
        data = self.session.get_record(type_name, key)
        self.editor_pane.load_record(type_name, key, data)
        QMessageBox.information(self, "Restored", f"{type_name}:{key} restored to default.")

    def restore_object_type(self):
        if not self.session: return
        t = self.types_pane.current_type()
        if not t: return
        self.session.restore_object_type(t)
        self.on_type_selected(t)

    def restore_all(self):
        if not self.session: return
        self.session.restore_all()
        self.types_pane.clear(); self.list_pane.clear(); self.editor_pane.clear()
        self.update_enables(False)

    def reapply_changes(self):
        if not self.session: return
        from app.patch_engine.patch_apply import apply_all
        conflicts = apply_all(self.session, self.patch_store)
        if conflicts:
            QMessageBox.warning(self, "Conflicts", f"{len(conflicts)} conflicts need review (conflict UI coming).")
        else:
            QMessageBox.information(self, "Reapplied", "Your changes were reapplied successfully.")
