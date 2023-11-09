import sys
from PyQt6.QtWidgets import (
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
    QCheckBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from todo import TodoList


from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class TaskWidget(QFrame):
    def __init__(self, task):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Add some margins
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the layout

        # Add a checkbox to toggle completion
        checkbox = QCheckBox()
        checkbox.setEnabled(task["completed"])
        layout.addWidget(checkbox)

        # Add a preview image
        if task["image_uri"]:
            label = QLabel()
            pixmap = QPixmap(task["image_uri"])
            label.setPixmap(
                pixmap.scaled(
                    256, 256, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio
                )
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the image
            layout.addWidget(label)  # Add the label to the main layout

        # Add a description
        desc = QLabel(task["description"])
        desc.setFont(QFont("Arial", 14))  # Change the font size
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the description
        layout.addWidget(desc)  # Add the description to the main layout

        # Add a deadline
        if task["deadline"]:
            deadline = QLabel(task["deadline"])
            deadline.setFont(QFont("Arial", 12))  # Change the font size
            deadline.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )  # Center align the deadline
            layout.addWidget(deadline)  # Add the deadline to the main layout

        self.setLayout(layout)
        self.setStyleSheet(
            """
            border-radius: 10px;
            padding: 10px;
        """
        )  # Add some styling


class TaskList(QWidget):
    def __init__(self, tasks):
        super().__init__()

        # Create a QListWidget
        self.listwidget = QListWidget()

        # Create a QVBoxLayout for the QListWidget
        layout = QVBoxLayout()
        layout.addWidget(self.listwidget)

        # Add a spacer at the top and bottom of the layout
        layout.insertSpacerItem(
            0,
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            ),
        )
        layout.addSpacerItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )

        # Create custom items for the QListWidget
        for task in tasks:
            item = QListWidgetItem()

            # Create a widget for the item
            widget = TaskWidget(task)
            item.setSizeHint(widget.sizeHint())

            self.listwidget.addItem(item)
            self.listwidget.setItemWidget(item, widget)

        # Set minimum width for the widget
        self.setMinimumWidth(200)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        todo_list = TodoList()
        self.setWindowTitle("Todo App")

        # Create a TaskList
        tasklist = TaskList(todo_list.get_all_tasks())

        # Create a QVBoxLayout and add the tasklist widget to it
        layout = QVBoxLayout()
        layout.addWidget(tasklist)

        # Set the layout as the central widget of the MainWindow
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
