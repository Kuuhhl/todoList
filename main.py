import sys
import copy
from database_client import DatabaseClient
from widgets.Edit_Task_Widget import Edit_Task_Widget
from widgets.Tasks_Widget import Tasks_Widget
from widgets.About_Dialog import About_Dialog
from PyQt6.QtGui import QPixmap, QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QProgressBar,
    QPushButton,
    QMessageBox,
    QApplication,
    QStackedWidget,
    QMainWindow,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QCheckBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QStatusBar,
    QToolBar,
)


class Main_Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.database_client = DatabaseClient()
        self.setWindowTitle("Todo App")

        self.tasks_widget = Tasks_Widget(self.database_client)
        self.edit_task_widget = Edit_Task_Widget(database_client=self.database_client)
        self.setCentralWidget(self.tasks_widget)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.tasks_widget)
        self.stacked_widget.addWidget(self.edit_task_widget)

        self.setCentralWidget(self.stacked_widget)

        # menubar
        menu = self.menuBar()

        # file menu
        file_menu = menu.addMenu("&File")

        # import button
        button_action = QAction("&Import Tasks", self)
        button_action.setStatusTip("import tasks from .json file")
        button_action.triggered.connect(self.import_tasks)
        file_menu.addAction(button_action)
        file_menu.addSeparator()

        # export button
        button_action = QAction("&Export Tasks", self)
        button_action.setStatusTip("Import Tasks from .json file")
        button_action.triggered.connect(self.export_tasks)
        file_menu.addAction(button_action)
        file_menu.addSeparator()

        # clear button
        button_action = QAction("&Clear All Tasks", self)
        button_action.setStatusTip("Clear All Tasks")
        button_action.triggered.connect(self.clear_tasks)
        file_menu.addAction(button_action)

        # about button
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this Application")
        about_action.triggered.connect(self.about)
        menu.addAction(about_action)

        # Create a round button with a "+" sign
        self.addButton = QPushButton("+", self)
        self.addButton.setStyleSheet(
            """
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 25px;
                font-size: 20px;
                width: 50px;
                height: 50px;
            }
        """
        )
        self.addButton.clicked.connect(self.add_edit_task)
        self.tasks_widget.add_task_signal.connect(self.add_edit_task)

        self.task_widgets = copy.copy(self.tasks_widget.task_widgets)
        for task_widget in self.task_widgets:
            task_widget.edit_task_signal.connect(self.add_edit_task)

        self.database_client.task_modified.connect(self.update_tasks)

        # Change the cursor to a pointer when hovering over the button
        self.addButton.setCursor(Qt.CursorShape.PointingHandCursor)

        # Position the button in the lower right corner
        self.addButton.setGeometry(self.width() - 60, self.height() - 60, 50, 50)

        # Define the progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setGeometry(0, self.height() - 10, self.width(), 10)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border-radius: 5px;
                background-color: green;
            }
        """
        )
        self.progress_bar.hide()

    def resizeEvent(self, event):
        # Update the position of the button when the window is resized
        self.progress_bar.setGeometry(0, self.height() - 10, self.width(), 10)
        self.addButton.setGeometry(self.width() - 60, self.height() - 60, 50, 50)

    def update_tasks(self):
        # disconnect old signals
        for task_widget in self.task_widgets:
            task_widget.edit_task_signal.disconnect()

        # create new signals
        self.task_widgets = copy.copy(self.tasks_widget.task_widgets)
        for task_widget in self.task_widgets:
            task_widget.edit_task_signal.connect(self.add_edit_task)

        self.tasks_widget.update_tasks()

        print(str(len(self.task_widgets)) + " tasks right now")

    def updateProgressBar(
        self, visible=False, curr_value=0, min_value=0, max_value=100
    ):
        if visible:
            self.progress_bar.show()
            self.progress_bar.setValue(curr_value)
            self.progress_bar.setMinimum(min_value)
            self.progress_bar.setMaximum(max_value)
        else:
            self.progress_bar.hide()

    def import_tasks(self):
        print("called import tasks")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Tasks", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                task_num_before = len(self.database_client.get_all_tasks())
                self.database_client.import_from_file(file_path)
                self.database_client.update_progress_bar.connect(self.updateProgressBar)
                print("imported")
                QMessageBox.information(
                    self,
                    "Import Tasks",
                    f"{len(self.database_client.get_all_tasks())-task_num_before} Tasks imported successfully.",
                )
                return
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Tasks", f"Failed to import tasks: {e}"
                )

    def export_tasks(self, s):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Tasks", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.database_client.export_to_file(file_path)
                QMessageBox.information(
                    self, "Export Tasks", "Tasks exported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Tasks", f"Failed to export tasks: {e}"
                )

    def clear_tasks(self, s):
        if (
            QMessageBox.question(
                self,
                "Clear Tasks",
                "Are you sure you want to clear all tasks?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.database_client.clear_all()

    def about(self, s):
        About_Dialog().exec()

    def add_edit_task(self, task_uuid=None):
        self.edit_task_widget.task_done.connect(self.task_done)
        self.stacked_widget.setCurrentWidget(self.edit_task_widget)

        if task_uuid:
            self.edit_task_widget.edit_task(task_uuid)
        else:
            self.edit_task_widget.create_task()

        self.addButton.hide()

    def task_done(self):
        self.stacked_widget.setCurrentWidget(self.tasks_widget)
        self.addButton.show()


app = QApplication(sys.argv)

window = Main_Window()
window.show()

app.exec()
