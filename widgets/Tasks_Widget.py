from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import (
    QScrollArea,
    QApplication,
    QMainWindow,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QTabWidget,
    QCheckBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QStatusBar,
    QToolBar,
)


class Task_Widget(QWidget):
    edit_task_signal = pyqtSignal(str)

    def __init__(self, task, database_client, parent=None):
        super().__init__(parent)

        self.task = task
        self.database_client = database_client

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # Add an image thumbnail
        if task.image_uri != "":
            self.image_label = QLabel()
            pixmap = QPixmap(task.image_uri)
            pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio)

            self.image_label.setPixmap(pixmap)
            self.layout.addWidget(self.image_label)

        # Add a due date label
        self.due_date_label = QLabel(task.deadline)
        self.layout.addWidget(self.due_date_label)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.stateChanged.connect(self.toggle_completed)
        self.layout.addWidget(self.checkbox)

        self.label = QLabel(self.task.description)
        self.layout.addWidget(self.label)

        self.editButton = QPushButton("Edit", self)
        self.editButton.clicked.connect(self.emit_edit_signal)
        self.layout.addWidget(self.editButton)

        self.layout.addStretch()

        self.delete_button = QPushButton("x", self)
        self.delete_button.setStyleSheet("color: red")
        self.delete_button.clicked.connect(self.delete_task)
        self.layout.addWidget(self.delete_button)

    def update(self):
        # Update the due date label
        self.due_date_label.setText(self.task.due_date.strftime("%Y-%m-%d"))

        # Change the background color if the due date is over
        if datetime.strptime(self.task.due_date, "%Y-%m-%d") < datetime.date.today():
            self.setStyleSheet("background-color: #ffcccc;")
        else:
            self.setStyleSheet("")

    def emit_edit_signal(self):
        self.edit_task_signal.emit(self.task.uuid)

    def toggle_completed(self, state):
        self.task.toggle_completed()
        self.database_client.edit_task(self.task.uuid, self.task)

    def delete_task(self):
        self.database_client.delete_task(self.task.uuid)
        self.destroy()


class Tasks_Widget(QWidget):
    add_task_signal = pyqtSignal()

    def __init__(self, database_client):
        super().__init__()
        self.database_client = database_client

        self.task_widgets = []
        # Create a QTabWidget
        self.tab_widget = QTabWidget()

        # Create a QWidget for the scroll area content
        self.content_widget_completed = QWidget()
        self.content_widget_not_completed = QWidget()

        if not self.content_widget_completed.layout():
            self.content_widget_completed.setLayout(QVBoxLayout())
        if not self.content_widget_not_completed.layout():
            self.content_widget_not_completed.setLayout(QVBoxLayout())

        # Crea
        # Create a QScrollArea and set its properties
        self.scroll_area_completed = QScrollArea()
        self.scroll_area_completed.setWidgetResizable(True)
        self.scroll_area_completed.setWidget(self.content_widget_completed)
        self.scroll_area_not_completed = QScrollArea()
        self.scroll_area_not_completed.setWidgetResizable(True)
        self.scroll_area_not_completed.setWidget(self.content_widget_not_completed)

        # Add the scroll areas to the tab widget
        self.tab_widget.addTab(self.scroll_area_completed, "Completed Tasks")
        self.tab_widget.addTab(self.scroll_area_not_completed, "Not Completed Tasks")

        # Set the default tab
        self.tab_widget.setCurrentIndex(1)

        # Create a QVBoxLayout for the main widget and add the tab widget to it
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)

        self.tasks = self.database_client.get_all_tasks()
        self.update_tasks()

    def emit_add_signal(self):
        self.add_task_signal.emit()

    def update_tasks(self):
        self.tasks = self.database_client.get_all_tasks()
        completed_tasks = [task for task in self.tasks if task.completed]
        not_completed_tasks = [task for task in self.tasks if not task.completed]

        # Sort the tasks by deadline
        completed_tasks.sort(key=lambda task: task.deadline)
        not_completed_tasks.sort(key=lambda task: task.deadline)

        self.task_widgets.clear()

        for i in reversed(range(self.content_widget_completed.layout().count())):
            self.content_widget_completed.layout().itemAt(i).widget().setParent(None)

        for task in completed_tasks:
            task_widget = self.add_task(task, self.content_widget_completed.layout())
            self.task_widgets.append(task_widget)

        for i in reversed(range(self.content_widget_not_completed.layout().count())):
            self.content_widget_not_completed.layout().itemAt(i).widget().setParent(
                None
            )
        for task in not_completed_tasks:
            task_widget = self.add_task(
                task, self.content_widget_not_completed.layout()
            )
            self.task_widgets.append(task_widget)

    def add_task(self, task, layout):
        task_widget = Task_Widget(task, self.database_client, self)
        layout.addWidget(task_widget)
        return task_widget
