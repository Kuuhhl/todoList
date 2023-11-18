from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import (
    QFrame,
    QScrollArea,
    QApplication,
    QMainWindow,
    QMessageBox,
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

    def __init__(
        self,
        task,
        shared_state,
    ):
        super().__init__()

        # set the shared state
        self.shared_state = shared_state

        # setup the ui
        self.setup_ui()

        # set the task
        self.task = task

    def setup_ui(self):
        # Create the main layout
        self.layout = QHBoxLayout()

        self.setFixedHeight(100)

        # Create the left, middle, and right layouts
        left_layout = QHBoxLayout()
        middle_layout = QHBoxLayout()
        right_layout = QHBoxLayout()

        left_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        middle_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Create and add the checkbox to the left layout
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.toggle_complete)
        left_layout.addWidget(self.checkbox)

        # due date label
        self.due_date_label = QLabel()
        left_layout.addWidget(self.due_date_label)

        # due badge
        self.due_badge = QLabel("Due")
        self.due_badge.setStyleSheet("color: red;")
        self.due_badge.hide()
        left_layout.addWidget(self.due_badge)

        # Create and add the label to the middle layout
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 20px;")
        middle_layout.addWidget(self.label)

        # Create the edit and delete buttons and add them to the right layout
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.emit_edit_task_signal)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete)
        right_layout.addWidget(self.edit_button)
        right_layout.addWidget(self.delete_button)

        # Add the left, middle, and right layouts to the main layout
        self.layout.addLayout(left_layout)
        self.layout.addLayout(middle_layout)
        self.layout.addLayout(right_layout)

        self.setLayout(self.layout)

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, value):
        self._task = value

        self.checkbox.setChecked(self.task.complete)
        self.due_date_label.setText(self.task.due_date)

        if datetime.strptime(self.task.due_date, "%Y-%m-%d") < datetime.now():
            self.due_badge.show()
        else:
            self.due_badge.hide()

        if len(self.task.description) > 30:
            self.label.setText(self.task.description[:30] + "...")
        else:
            self.label.setText(self.task.description)

    def emit_edit_task_signal(self):
        self.edit_task_signal.emit(self.task.uuid)

    def toggle_complete(self, state):
        self.task.complete = not self.task.complete
        self.shared_state.database_client.edit_task(self.task)

    def delete(self):
        if (
            QMessageBox.question(
                self,
                "Delete Task",
                "Are you sure you want to delete this task?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.shared_state.database_client.delete_task(self.task.uuid)


class Tasks_Widget(QWidget):
    add_task_signal = pyqtSignal()

    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state

        # setup the ui
        self.setup_ui()

        # reload tasks when the tab is changed
        self.tab_widget.currentChanged.connect(self.reload_tasks)

        # update the tasks when tasks are changed
        self.shared_state.reload_signal.connect(self.reload_tasks)

        # load more tasks when the scroll bar reaches the top
        self.tab_widget.currentWidget().verticalScrollBar().valueChanged.connect(
            self.check_scrollbar
        )

        # load initial tasks
        self.reload_tasks()

    def setup_ui(self):
        # Create a QTabWidget
        self.tab_widget = QTabWidget()

        # Create a QWidget for the scroll area content
        self.content_widget_complete = QWidget()
        self.content_widget_incomplete = QWidget()

        if not self.content_widget_complete.layout():
            self.content_widget_complete.setLayout(QVBoxLayout())
        if not self.content_widget_incomplete.layout():
            self.content_widget_incomplete.setLayout(QVBoxLayout())

        # Create a QScrollArea and set its properties
        self.scroll_area_complete = QScrollArea()
        self.scroll_area_complete.setWidgetResizable(True)
        self.scroll_area_complete.setWidget(self.content_widget_complete)

        self.scroll_area_incomplete = QScrollArea()
        self.scroll_area_incomplete.setWidgetResizable(True)
        self.scroll_area_incomplete.setWidget(self.content_widget_incomplete)
        # lazy loading variables
        self.scroll_area_complete.lazy_offset = 0
        self.scroll_area_complete.lazy_limit = 20
        self.scroll_area_incomplete.lazy_offset = 0
        self.scroll_area_incomplete.lazy_limit = 20

        # complete attributes
        self.scroll_area_complete.complete = True
        self.scroll_area_incomplete.complete = False

        # Add the scroll areas to the tab widget
        self.tab_widget.addTab(self.scroll_area_complete, "Finished")
        self.tab_widget.addTab(self.scroll_area_incomplete, "To Do")

        # Set the default tab
        self.tab_widget.setCurrentIndex(1)

        # Create a QVBoxLayout for the main widget and add the tab widget to it
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)

    def load_more_tasks(self, all_tabs=False):
        tasks = []
        if all_tabs:
            for scroll_area in [self.scroll_area_complete, self.scroll_area_incomplete]:
                tasks += self.shared_state.database_client.lazy_load_tasks(
                    scroll_area.lazy_offset,
                    scroll_area.lazy_limit,
                    scroll_area.complete,
                )
                scroll_area.lazy_offset += len(tasks)
        else:
            current_tab = self.tab_widget.currentWidget()
            tasks = self.shared_state.database_client.lazy_load_tasks(
                current_tab.lazy_offset,
                current_tab.lazy_limit,
                current_tab.complete,
            )
            current_tab.lazy_offset += len(tasks)

        for task in tasks:
            task_widget = Task_Widget(task, self.shared_state)
            layout = (
                self.content_widget_complete.layout()
                if task.complete
                else self.content_widget_incomplete.layout()
            )
            layout.insertWidget(0, task_widget)

    def scroll_to_bottom(self):
        self.scroll_area_complete.verticalScrollBar().setValue(
            self.scroll_area_complete.verticalScrollBar().maximum()
        )
        self.scroll_area_incomplete.verticalScrollBar().setValue(
            self.scroll_area_incomplete.verticalScrollBar().maximum()
        )

    def emit_add_signal(self):
        self.add_task_signal.emit()

    def __clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def check_scrollbar(self, value):
        # If the scrollbar's value is within 5% of the minimum value, check if there are still tasks to load
        if (
            value
            <= self.tab_widget.currentWidget().verticalScrollBar().maximum() * 0.05
        ):
            total_tasks = self.shared_state.database_client.count_tasks()
            loaded_widgets_count = (
                self.content_widget_complete.layout().count()
                + self.content_widget_incomplete.layout().count()
            )
            if loaded_widgets_count < total_tasks:
                # Save the current maximum value of the scrollbar
                old_max = self.tab_widget.currentWidget().verticalScrollBar().maximum()

                self.load_more_tasks()

                # Adjust the scrollbar's position to maintain the user's place
                # Set the value to the old maximum plus 5% of the new maximum
                self.tab_widget.currentWidget().verticalScrollBar().setValue(
                    old_max
                    + int(
                        self.tab_widget.currentWidget().verticalScrollBar().maximum()
                        * 0.05
                    )
                )

    def reload_tasks(self):
        # reset the lazy loading variables
        self.scroll_area_complete.lazy_offset = 0
        self.scroll_area_incomplete.lazy_offset = 0

        # clear the list of task widgets
        self.__clear_layout(self.content_widget_complete.layout())
        self.__clear_layout(self.content_widget_incomplete.layout())

        # load the tasks
        self.load_more_tasks()

        # scroll to bottom in both tabs
        self.scroll_to_bottom()
