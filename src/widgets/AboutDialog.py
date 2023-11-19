from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("About")
        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        self.setLayout(layout)

        bold_font = QFont()
        bold_font.setWeight(QFont.Weight.Bold)

        italic_font = QFont()
        italic_font.setItalic(True)

        layout.addWidget(QLabel("Todo List", font=bold_font))
        layout.addWidget(
            QLabel("Manage your tasks before they manage you.", font=italic_font)
        )
        layout.addWidget(QLabel("License: General Public License Version 2"))

        link_label = QLabel(
            '<a href="https://github.com/Kuuhhl/todoList">GitHub Repo</a>'
        )
        link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)

        for i in range(layout.count()):
            layout.itemAt(i).widget().setAlignment(Qt.AlignmentFlag.AlignCenter)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        layout.addWidget(ok_button)


if __name__ == "__main__":
    app = QApplication([])
    dialog = AboutDialog()
    dialog.exec()
