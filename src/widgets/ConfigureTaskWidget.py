import os
import sys
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task import Task
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDateEdit,
    QGridLayout,
    QDialogButtonBox,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QDate, pyqtSignal


class ConfigureTaskWidget(QWidget):
    task_done = pyqtSignal()

    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.apply()

    def setup_ui(self):
        layout = QGridLayout()
        self.setLayout(layout)

        image_layout = QVBoxLayout()
        layout.addLayout(image_layout, 0, 0, 2, 1)

        self.image_label = QLabel()
        image_layout.addWidget(self.image_label)

        button_layout = QHBoxLayout()
        image_layout.addLayout(button_layout)

        self.add_change_image_button = QPushButton()
        self.add_change_image_button.clicked.connect(self.add_change_image)
        button_layout.addWidget(self.add_change_image_button)

        self.remove_image_button = QPushButton("Remove Image")
        self.remove_image_button.clicked.connect(self.remove_image)

        button_layout.addWidget(self.remove_image_button)

        layout.addWidget(QLabel("Description:"), 2, 0)
        self.description_edit = QLineEdit(self.task.description)
        layout.addWidget(self.description_edit, 2, 1)

        layout.addWidget(QLabel("Due Date:"), 3, 0)
        self.due_date_edit = QDateEdit(
            QDate.fromString(self.task.due_date, "yyyy-MM-dd")
        )
        layout.addWidget(self.due_date_edit, 3, 1)

        self.image_path = self.task.image_uri

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.apply)
        button_box.rejected.connect(self.cancel)
        layout.addWidget(button_box, 4, 0, 1, 2)

        self.update_image()

    def remove_image(self):
        self.image_path = ""
        self.update_image()

    def update_image(self):
        if self.image_path != "":
            pixmap = QPixmap(self.image_path)
            scaled_pixmap = pixmap.scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(scaled_pixmap)
            self.add_change_image_button.setText("Change Image")
        else:
            self.image_label.clear()
            self.add_change_image_button.setText("Add Image")

        self.image_label.setVisible(bool(self.image_path))
        self.remove_image_button.setEnabled(bool(self.image_path))

    def add_change_image(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)"
        )
        if image_path:
            self.image_path = image_path
            self.update_image()

    def apply(self):
        pass

    def cancel(self):
        self.task_done.emit()


class EditTaskWidget(ConfigureTaskWidget):
    def __init__(self, shared_state, task):
        super().__init__(shared_state)
        self.editing = True
        self.task = copy.copy(task)

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Edit Task")
        super().setup_ui()

    def apply(self):
        # Update the task fields
        self.task.description = self.description_edit.text()
        self.task.due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        self.task.image_uri = self.image_path

        # Edit the task
        self.shared_state.database_client.edit_task(edited_task=self.task)

        self.task_done.emit()


class AddTaskWidget(ConfigureTaskWidget):
    def __init__(self, shared_state):
        super().__init__(shared_state)
        self.editing = False
        self.task = Task()

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Add Task")
        super().setup_ui()

    def apply(self):
        # Update the task fields
        self.task.description = self.description_edit.text()
        self.task.due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        self.task.image_uri = self.image_path

        # Add the task
        self.shared_state.database_client.add_task(self.task)

        self.task_done.emit()


if __name__ == "__main__":
    pass
