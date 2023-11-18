import sys
import os
from pysqlcipher3.dbapi2 import DatabaseError
from database_client import DatabaseClient
from widgets.Edit_Task_Widget import Edit_Task_Widget
from widgets.Tasks_Widget import Tasks_Widget, Task_Widget
from widgets.About_Dialog import About_Dialog
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QLineEdit,
    QInputDialog,
    QProgressDialog,
    QPushButton,
    QMessageBox,
    QApplication,
    QStackedWidget,
    QMainWindow,
    QFileDialog,
    QDialog,
)


class Task_Widgets:
    def __init__(self):
        self.complete = []
        self.incomplete = []

    def add(self, task_objs):
        if not isinstance(task_objs, list):
            task_objs = [task_objs]

        for task_obj in task_objs:
            task_widget = Task_Widget(task_obj, shared_state)

            if task_obj.complete:
                self.complete.append(task_widget)
                self.complete.sort(
                    key=lambda task_widget: task_widget.task.due_date, reverse=True
                )
            else:
                self.incomplete.append(task_widget)
                self.incomplete.sort(
                    key=lambda task_widget: task_widget.task.due_date, reverse=True
                )

    def edit(self, new_task):
        # replace old task with new task
        for task_list in [self.complete, self.incomplete]:
            for task_widget in task_list:
                if task_widget.task.uuid == new_task.uuid:
                    task_widget.task = new_task
                    break

    def delete(self, task_uuid):
        for task_list in [self.complete, self.incomplete]:
            for task_widget in task_list:
                if task_widget.task.uuid == task_uuid:
                    task_list.remove(task_widget)
                    break

    def clear(self):
        self.complete.clear()
        self.incomplete.clear()


class Shared_State(QObject):
    reload_signal = pyqtSignal()

    def __init__(self, database_client):
        super().__init__()
        self.database_client = database_client
        self.task_widgets = Task_Widgets()

        # connect signals from database
        self.database_client.added_task.connect(self.handle_added_task)
        self.database_client.imported_tasks.connect(self.handle_imported_tasks)
        self.database_client.edited_task.connect(self.handle_edited_task)
        self.database_client.deleted_task.connect(self.handle_deleted_task)
        self.database_client.cleared_tasks.connect(self.handle_cleared_tasks)

    def handle_added_task(self, task_uuid):
        task_obj = self.database_client.get_task(task_uuid)
        self.task_widgets.add(task_obj)
        self.reload_signal.emit()

    def handle_edited_task(self, task_uuid):
        new_task = self.database_client.get_task(task_uuid)
        self.task_widgets.edit(new_task)
        self.reload_signal.emit()

    def handle_deleted_task(self, task_uuid):
        self.task_widgets.delete(task_uuid)
        self.reload_signal.emit()

    def handle_imported_tasks(self):
        # clear the task widgets
        self.task_widgets.clear()

        # add the new tasks
        task_widgets = self.database_client.get_all_tasks()
        self.task_widgets.add(task_widgets)

        # emit the reload signal
        self.reload_signal.emit()

    def handle_cleared_tasks(self):
        self.task_widgets.clear()
        self.reload_signal.emit()


class Password_Dialog(QDialog):
    def __init__(self, db_name):
        super().__init__()
        self.db_name = db_name
        if os.path.exists(self.db_name):
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
                    self.database_client = DatabaseClient(key, self.db_name)
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
                QMessageBox.critical(
                    self, "Error", "Encryption keys do not match. Please try again."
                )


class Main_Window(QMainWindow):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state
        self.setWindowTitle("Todo App")

        self.tasks_widget = Tasks_Widget(self.shared_state)
        self.edit_task_widget = Edit_Task_Widget(self.shared_state)
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
            border: 2px solid white;
        }
        QPushButton:hover {
            background-color: #555;
            color: yellow;
        }
    """
        )
        # connect buttons
        self.addButton.clicked.connect(self.add_edit_task)
        self.tasks_widget.add_task_signal.connect(self.add_edit_task)
        self.shared_state.database_client.added_task.connect(self.add_connections)
        self.shared_state.database_client.imported_tasks.connect(self.add_connections)

        # Change the cursor to a pointer when hovering over the button
        self.addButton.setCursor(Qt.CursorShape.PointingHandCursor)
        # Position the button in the top right corner
        self.addButton.setGeometry(self.width() - 80, 20, 50, 50)
        self.tmpConnections = []

    def add_connections(self):
        # Disconnect all previous connections
        for connection in self.tmpConnections:
            try:
                connection.disconnect()
            except TypeError:
                pass
            self.tmpConnections.remove(connection)

        # Connect each task_widget and save a reference
        for task_widget in (
            self.shared_state.task_widgets.complete
            + self.shared_state.task_widgets.incomplete
        ):
            task_widget.edit_task_signal.connect(self.add_edit_task)
            self.tmpConnections.append(task_widget.edit_task_signal)

    def resizeEvent(self, event):
        # Update the position of the button when the window is resized
        self.addButton.setGeometry(self.width() - 80, 20, 50, 50)

    def import_tasks(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Tasks", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                task_num_before = self.shared_state.database_client.count_tasks()
                self.shared_state.database_client.import_from_file(file_path)
                QMessageBox.information(
                    self,
                    "Import Tasks",
                    f"{self.shared_state.database_client.count_tasks()-task_num_before} Tasks imported successfully.",
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
                self.shared_state.database_client.export_to_file(file_path)
                QMessageBox.information(
                    self, "Export Tasks", "Tasks exported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Tasks", f"Failed to export tasks: {e}"
                )

    def clear_tasks(self, s):
        if self.shared_state.database_client.count_tasks() == 0:
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
            self.shared_state.database_client.clear_all()

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

# ask for password
db_name = "tasks.db"
password_dialog = Password_Dialog(db_name)
database_client = password_dialog.database_client

# setup shared state
shared_state = Shared_State(database_client)


# start main window
window = Main_Window(shared_state)


# Set the window icon
icon_path = "icon.png"
if os.path.exists(icon_path):
    window.setWindowIcon(QIcon(icon_path))
else:
    print(f"Icon file {icon_path} does not exist.")


window.show()

app.exec()
