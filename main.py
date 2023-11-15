import sys
import os
from pysqlcipher3.dbapi2 import DatabaseError
from database_client import DatabaseClient
from widgets.Edit_Task_Widget import Edit_Task_Widget
from widgets.Tasks_Widget import Tasks_Widget
from widgets.About_Dialog import About_Dialog
from PyQt6.QtGui import QPixmap, QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QProgressBar,
    QLineEdit,
    QInputDialog,
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
    """
    The main window of the Todo App.

    Attributes:
    - database_client (DatabaseClient): The database client used to interact with the task database.
    - tasks_widget (Tasks_Widget): The widget that displays the list of tasks.
    - edit_task_widget (Edit_Task_Widget): The widget used to create or edit a task.
    - stacked_widget (QStackedWidget): The widget that contains both the tasks_widget and the edit_task_widget.
    - addButton (QPushButton): The button used to add a new task.
    - task_widgets (list): A list of all the task widgets displayed in the tasks_widget.
    - progress_bar (QProgressBar): The progress bar displayed at the bottom of the window.
    """

    def __init__(self):
        super().__init__()

        db_name = "todo.db"

        if os.path.exists(db_name):
            while True:
                key, ok = QInputDialog.getText(
                    self,
                    "Enter Encryption Key",
                    "Enter the encryption key for the database:",
                    echo=QLineEdit.EchoMode.Password,
                )
                if not ok:
                    sys.exit()
                try:
                    self.database_client = DatabaseClient(key, db_name)
                    break
                except DatabaseError:
                    QMessageBox.critical(
                        self, "Error", "Incorrect encryption key. Please try again."
                    )
        else:
            while True:
                key, ok = QInputDialog.getText(
                    self,
                    "Enter Encryption Key",
                    "Enter an new encryption key for the database:",
                    echo=QLineEdit.EchoMode.Password,
                )
                if not ok:
                    sys.exit()
                if len(key) < 1:
                    QMessageBox.critical(
                        self,
                        "Error",
                        "Encryption key cannot be empty. Please try again.",
                    )
                    continue
                key2, ok = QInputDialog.getText(
                    self,
                    "Confirm Encryption Key",
                    "Confirm the encryption key for the database:",
                    echo=QLineEdit.EchoMode.Password,
                )
                if not ok:
                    sys.exit()
                if key == key2:
                    self.database_client = DatabaseClient(key, db_name)
                    break
                else:
                    QMessageBox.critical(
                        self, "Error", "Encryption keys do not match. Please try again."
                    )

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

        self.task_widgets = self.tasks_widget.task_widgets
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
        # Disconnect old signals
        for task_widget in self.task_widgets:
            try:
                task_widget.edit_task_signal.disconnect()
            except TypeError:
                pass

        # Update the task widgets
        self.task_widgets = self.tasks_widget.task_widgets

        # Connect new signals
        for task_widget in self.task_widgets:
            task_widget.edit_task_signal.connect(self.add_edit_task)

        self.tasks_widget.update_tasks()

    def updateProgressBar(
        self, visible=False, curr_value=0, min_value=0, max_value=100
    ):
        """
        Updates the progress bar displayed at the bottom of the window.

        Args:
        - visible (bool): Whether to show or hide the progress bar.
        - curr_value (int): The current value of the progress bar.
        - min_value (int): The minimum value of the progress bar.
        - max_value (int): The maximum value of the progress bar.
        """
        if visible:
            self.progress_bar.show()
            self.progress_bar.setValue(curr_value)
            self.progress_bar.setMinimum(min_value)
            self.progress_bar.setMaximum(max_value)
        else:
            self.progress_bar.hide()

    def import_tasks(self):
        """
        Imports tasks from a JSON file.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Tasks", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                task_num_before = len(self.database_client.get_all_tasks())
                self.database_client.import_from_file(file_path)
                self.database_client.update_progress_bar.connect(self.updateProgressBar)
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
        """
        Exports tasks to a JSON file.
        """
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
        """
        Clears all tasks from the database.
        """
        if len(self.database_client.get_all_tasks()) == 0:
            QMessageBox.information(self, "Clear Tasks", "There are no tasks to clear.")
            return
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
        """
        Displays information about the application.
        """
        About_Dialog().exec()

    def add_edit_task(self, task_uuid=None):
        """
        Displays the edit_task_widget to create or edit a task.

        Args:
        - task_uuid (str): The UUID of the task to edit. If None, a new task will be created.
        """
        self.edit_task_widget.task_done.connect(self.task_done)
        self.stacked_widget.setCurrentWidget(self.edit_task_widget)

        if task_uuid:
            self.edit_task_widget.edit_task(task_uuid)
        else:
            self.edit_task_widget.create_task()

        self.addButton.hide()

    def task_done(self):
        """
        Called when a task has been created or edited. Returns to the tasks_widget and shows the addButton.
        """
        self.stacked_widget.setCurrentWidget(self.tasks_widget)
        self.addButton.show()


app = QApplication(sys.argv)

window = Main_Window()
window.show()

app.exec()
