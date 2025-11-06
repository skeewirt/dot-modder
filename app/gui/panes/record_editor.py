from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel
import json

class RecordEditorPane(QWidget):
    def __init__(self, on_save, on_restore):
        super().__init__()
        self.on_save = on_save
        self.on_restore = on_restore
        self._type = None
        self._key = None

        self.layout = QVBoxLayout(self)
        self.title = QLabel("Select a record")
        self.editor = QTextEdit()  # MVP: raw JSON editor; replace with schema-driven form later
        self.btn_save = QPushButton("Save")
        self.btn_restore = QPushButton("Restore to Default")

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.editor)
        self.layout.addWidget(self.btn_save)
        self.layout.addWidget(self.btn_restore)

        self.btn_save.clicked.connect(self._save)
        self.btn_restore.clicked.connect(self._restore)
        self.setEnabled(False)

    def load_record(self, type_name: str, key: str, data: dict):
        self._type, self._key = type_name, key
        self.title.setText(f"{type_name} — {key}")
        self.editor.setPlainText(json.dumps(data, indent=2))
        self.setEnabled(True)

    def clear(self):
        self._type = self._key = None
        self.title.setText("Select a record")
        self.editor.setPlainText("")
        self.setEnabled(False)

    def _save(self):
        if not self._type or not self._key: return
        data = json.loads(self.editor.toPlainText() or "{}")
        self.on_save(self._type, self._key, data)

    def _restore(self):
        if not self._type or not self._key: return
        self.on_restore(self._type, self._key)
