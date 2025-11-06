from PySide6.QtWidgets import QListWidget

class RecordListPane(QListWidget):
    def __init__(self, on_select):
        super().__init__()
        self.on_select = on_select
        self.currentItemChanged.connect(self._changed)
        self._type = None

    def load_records(self, keys: list[str], type_name: str|None=None):
        if type_name: self._type = type_name
        self.clear()
        for k in keys:
            self.addItem(k)

    def _changed(self, cur, prev):
        if cur and self._type:
            self.on_select(self._type, cur.text())

    def set_type(self, t: str):
        self._type = t
