from PySide6.QtWidgets import QListWidget

class ObjectTypesPane(QListWidget):
    def __init__(self, on_select):
        super().__init__()
        self.on_select = on_select
        self.currentItemChanged.connect(self._changed)

    def load_types(self, types: list[str]):
        self.clear()
        for t in types:
            self.addItem(t)

    def _changed(self, cur, prev):
        if cur:
            self.on_select(cur.text())

    def current_type(self):
        i = self.currentItem()
        return i.text() if i else None
