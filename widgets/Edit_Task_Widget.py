import os
import sys
import json
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


class Edit_Task_Widget(QWidget):
    task_done = pyqtSignal()

    def __init__(self, database_client):
        super().__init__()

        self.database_client = database_client
        self.editing = False
        print("init")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.apply()

    def setup_ui(self):
        image_layout = QVBoxLayout()
        layout = self.layout()

        # Check if the widget already has a layout
        if layout is None:
            layout = QGridLayout()
            self.setLayout(layout)
            layout.addLayout(image_layout, 0, 0, 2, 1)

        self.image_label = QLabel()
        image_layout.addWidget(self.image_label)
        self.image_label.setVisible(bool(self.new_task.image_uri))

        button_layout = QHBoxLayout()
        image_layout.addLayout(button_layout)

        self.add_change_image_button = QPushButton(
            "Add Image" if self.new_task.image_uri is None else "Change Image"
        )
        self.add_change_image_button.clicked.connect(self.add_change_image)

        layout.addWidget(QLabel("Description:"), 2, 0)
        self.description_edit = QLineEdit(self.new_task.description)
        layout.addWidget(self.description_edit, 2, 1)

        layout.addWidget(QLabel("Due Date:"), 3, 0)
        self.due_date_edit = QDateEdit(
            QDate.fromString(self.new_task.deadline, "yyyy-MM-dd")
        )
        layout.addWidget(self.due_date_edit, 3, 1)

        # Define remove_image_button
        self.remove_image_button = QPushButton("Remove Image")
        self.remove_image_button.setEnabled(False)
        self.remove_image_button.setVisible(False)
        self.remove_image_button.clicked.connect(self.remove_image)
        button_layout.addWidget(self.remove_image_button)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.apply)
        button_box.rejected.connect(self.cancel)
        layout.addWidget(button_box, 4, 0, 1, 2)

    def create_task(self):
        print("create task")
        self.new_task = Task()
        self.setWindowTitle("Create Task")
        self.setup_ui()

    def edit_task(self, task_uuid):
        print("edit task")
        self.editing = True
        self.new_task = copy.copy(self.database_client.get_task(task_uuid))
        print("Before: " + json.dumps(self.new_task.__dict__, indent=4))
        self.setWindowTitle("Edit Task")
        self.setup_ui()

    def add_change_image(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)"
        )
        if image_path:
            self.image_path = image_path
            pixmap = QPixmap(self.image_path)
            scaled_pixmap = pixmap.scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setVisible(True)
            self.add_change_image_button.setText("Change Image")

            self.remove_image_button.setEnabled(True)
            self.remove_image_button.setVisible(True)

    def remove_image(self):
        self.image_path = ""
        self.image_label.clear()
        self.image_label.setVisible(False)
        self.add_change_image_button.setText("Add Image")
        self.remove_image_button.setEnabled(False)
        self.remove_image_button.setVisible(False)

    def apply(self):
        # Extract input fields
        description = self.description_edit.text()
        deadline = self.due_date_edit.date().toString("yyyy-MM-dd")
        image_uri = getattr(self, "image_path", "")

        if self.editing:
            # Update the task fields
            self.new_task.description = description
            self.new_task.deadline = deadline
            self.new_task.image_uri = image_uri

            # Edit the task
            self.database_client.edit_task(
                task_uuid=self.new_task.uuid, new_task=self.new_task
            )
        else:
            # Create a new task
            task = Task(
                description=description,
                deadline=deadline,
                image_uri=image_uri,
                completed=False,
            )

            # Add the task
            self.database_client.add_task(task)

        self.task_done.emit()
        self.reset_fields()

    def reset_fields(self):
        print("resetting input fields")
        tmp_task = Task()
        self.description_edit.setText(tmp_task.description)
        self.due_date_edit.setDate(QDate.fromString(tmp_task.deadline, "yyyy-MM-dd"))
        self.image_path = tmp_task.image_uri
        self.image_label.clear()
        self.image_label.setVisible(False)
        self.add_change_image_button.setText("Add Image")
        self.remove_image_button.setEnabled(False)
        self.remove_image_button.setVisible(False)

    def cancel(self):
        self.task_done.emit()


if __name__ == "__main__":
    pass
