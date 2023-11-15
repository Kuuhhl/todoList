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

        # Create the main layout
        self.layout = QHBoxLayout()

        # Create the left, middle, and right layouts
        left_layout = QHBoxLayout()
        middle_layout = QHBoxLayout()
        right_layout = QHBoxLayout()

        # Create and add the checkbox to the left layout
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.completed)
        self.checkbox.stateChanged.connect(self.toggle_completed)
        left_layout.addWidget(self.checkbox)

        # Create and add the label to the middle layout
        if len(self.task.description) > 30:
            ellipsis_description = self.task.description[:30] + "..."
        else:
            ellipsis_description = self.task.description
        self.label = QLabel(ellipsis_description)
        middle_layout.addWidget(self.label)

        # Create the edit and delete buttons and add them to the right layout
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        right_layout.addWidget(self.edit_button)
        right_layout.addWidget(self.delete_button)

        # Add the left, middle, and right layouts to the main layout
        self.layout.addLayout(left_layout)
        self.layout.addLayout(middle_layout)
        self.layout.addLayout(right_layout)

        self.setLayout(self.layout)

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
    """
    A widget that displays a list of tasks, separated into two tabs: completed tasks and not completed tasks.

    Attributes:
    - add_task_signal (pyqtSignal): A signal emitted when the user wants to add a new task.
    - database_client: A client for interacting with the database.
    - task_widgets (list): A list of Task_Widget objects representing the tasks displayed in the widget.
    - tab_widget (QTabWidget): A tab widget containing two tabs: one for completed tasks and one for not completed tasks.
    - content_widget_completed (QWidget): A widget containing the completed tasks.
    - content_widget_not_completed (QWidget): A widget containing the not completed tasks.
    - scroll_area_completed (QScrollArea): A scroll area containing the completed tasks.
    - scroll_area_not_completed (QScrollArea): A scroll area containing the not completed tasks.
    - tasks (list): A list of Task objects representing all the tasks in the database.
    """

    add_task_signal = pyqtSignal()

    class Tasks_Widget(QWidget):
        def __init__(self, database_client):
            super().__init__()
            self.database_client = database_client

            # lazy loading variables
            self.lazy_offset = 0
            self.lazy_limit = 20

            self.task_widgets = []

            # setup the ui
            self.setup_ui()

            # Load the initial tasks
            self.load_more_tasks()

            # scroll to bottom
            self.scroll_to_bottom()

            # always scroll to bottom on tab change
            self.tab_widget.currentChanged.connect(self.scroll_to_bottom)

            # load initial tasks
            self.reload_tasks()

        def setup_ui(self):
            # Create a QTabWidget
            self.tab_widget = QTabWidget()

            # Create a QWidget for the scroll area content
            self.content_widget_completed = QWidget()
            self.content_widget_not_completed = QWidget()

            if not self.content_widget_completed.layout():
                self.content_widget_completed.setLayout(QVBoxLayout())
            if not self.content_widget_not_completed.layout():
                self.content_widget_not_completed.setLayout(QVBoxLayout())

            # Create a QScrollArea and set its properties
            self.scroll_area_completed = QScrollArea()
            self.scroll_area_completed.setWidgetResizable(True)
            self.scroll_area_completed.setWidget(self.content_widget_completed)
            self.scroll_area_not_completed = QScrollArea()
            self.scroll_area_not_completed.setWidgetResizable(True)
            self.scroll_area_not_completed.setWidget(self.content_widget_not_completed)

            # Add the scroll areas to the tab widget
            self.tab_widget.addTab(self.scroll_area_completed, "Completed")
            self.tab_widget.addTab(self.scroll_area_not_completed, "Not Completed")

            # Set the default tab
            self.tab_widget.setCurrentIndex(1)

            # Create a QVBoxLayout for the main widget and add the tab widget to it
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(self.tab_widget)

    def load_more_tasks(self):
        # If the scroll bar is at the top
        if self.verticalScrollBar().value() == 0:
            # query if we are in completed or non completed tab
            completed = self.tab_widget.currentIndex() == 0

            # Load more tasks from the database
            tasks = self.database_client.lazy_load_tasks(
                self.lazy_offset, self.lazy_limit
            )
            self.lazy_offset += len(tasks)

            # Create a Task_Widget for each task and add it to the tasks layout
            for task in tasks:
                task_widget = Task_Widget(task, self.database_client)
                self.tasks_layout.addWidget(task_widget)

    def scroll_to_bottom(self):
        self.scroll_area_completed.verticalScrollBar().setValue(
            self.scroll_area_completed.verticalScrollBar().maximum()
        )
        self.scroll_area_not_completed.verticalScrollBar().setValue(
            self.scroll_area_not_completed.verticalScrollBar().maximum()
        )

    def emit_add_signal(self):
        """
        Emits the add_task_signal.
        """
        self.add_task_signal.emit()

    def add_tasks(self, tasks):
        """
        Updates the list of tasks displayed in the widget by inserting the new lazy-loaded tasks at the top.
        """
        completed_tasks = [task for task in tasks if task.completed]
        not_completed_tasks = [task for task in tasks if not task.completed]

        # Sort the tasks by deadline
        completed_tasks.sort(key=lambda task: task.deadline)
        not_completed_tasks.sort(key=lambda task: task.deadline)

        for task in completed_tasks:
            task_widget = Task_Widget(task, database_client=self.database_client)
            self.content_widget_completed.layout().insertWidget(0, task_widget)
            self.task_widgets.append(task_widget)

        for task in not_completed_tasks:
            task_widget = Task_Widget(task, database_client=self.database_client)
            self.content_widget_not_completed.layout().insertWidget(0, task_widget)
            self.task_widgets.append(task_widget)

    def reload_tasks(self):
        """
        Reloads tasks from the database and updates the widget.
        """
        self.lazy_offset = 0

        # get first tasks from db
        self.tasks = self.database_client.lazy_load_tasks(
            offset=self.lazy_offset, limit=self.lazy_limit
        )

        # delete all tasks from the widget
        for task_widget in self.task_widgets:
            task_widget.deleteLater()

        # clear the list of task widgets
        self.task_widgets.clear()

        # add the tasks to the widget
        self.add_tasks(self.tasks)

    def add_task(self, task, layout):
        """
        Adds a task to the widget.

        Args:
        - task: A Task object representing the task to be added.
        - layout: The layout to which the task widget should be added.

        Returns:
        - The Task_Widget object representing the added task.
        """
        task_widget = Task_Widget(task, self.database_client, self)
        layout.addWidget(task_widget)
        return task_widget
