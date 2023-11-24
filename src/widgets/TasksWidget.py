import os
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import (
    QScrollArea,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QTabWidget,
    QCheckBox,
)


class TaskWidget(QWidget):
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

        # Create the image label
        self.image_label = QLabel()
        self.image_label.setStyleSheet("border-radius: 10px;")
        middle_layout.addWidget(self.image_label)
        self.image_label.hide()

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

        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(self.task.complete)
        self.checkbox.blockSignals(False)

        self.due_date_label.setText(self.task.due_date)

        if datetime.strptime(self.task.due_date, "%Y-%m-%d") < datetime.now():
            self.due_badge.show()
        else:
            self.due_badge.hide()

        if self.task.image_uri != "" and os.path.exists(self.task.image_uri):
            image = QPixmap(self.task.image_uri)
            image = image.scaled(
                100,
                100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(image)
            self.image_label.show()
        else:
            self.image_label.hide()

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


class TasksWidget(QWidget):
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

        # delete task widget when task is deleted
        self.shared_state.database_client.deleted_task.connect(
            lambda task_uuid: self.delete_task_widget(task_uuid)
        )

        # insert task widget when task is added
        self.shared_state.database_client.added_task.connect(
            lambda task: self.insert_task(task)
        )

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
        self.scroll_area_complete.lazy_limit = 30
        self.scroll_area_incomplete.lazy_offset = 0
        self.scroll_area_incomplete.lazy_limit = 30

        # Add the scroll areas to the tab widget
        self.tab_widget.addTab(self.scroll_area_complete, "Finished")
        self.tab_widget.addTab(self.scroll_area_incomplete, "To Do")

        # Set the default tab
        self.tab_widget.setCurrentIndex(1)

        # Create a QVBoxLayout for the main widget and add the tab widget to it
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)

    def update_tab_labels(self):
        # count the number of loaded tasks in each category
        num_complete_tasks_loaded = len(self.shared_state.task_widgets.complete)
        num_incomplete_tasks_loaded = len(self.shared_state.task_widgets.incomplete)

        # get the total number of tasks in each category
        total_complete_tasks = self.shared_state.database_client.count_tasks(
            complete=True
        )
        total_incomplete_tasks = self.shared_state.database_client.count_tasks(
            complete=False
        )

        # update the tab text
        if self.tab_widget.currentIndex() == 0:
            self.tab_widget.setTabText(
                1,
                f"To Do ({self._format_task_count(total_incomplete_tasks)})",
            )
            if num_complete_tasks_loaded < total_complete_tasks:
                self.tab_widget.setTabText(
                    0,
                    f"Finished ({num_complete_tasks_loaded}/{self._format_task_count(total_complete_tasks)} loaded)",
                )
            else:
                self.tab_widget.setTabText(
                    0, f"Finished ({self._format_task_count(total_complete_tasks)})"
                )
        elif self.tab_widget.currentIndex() == 1:
            self.tab_widget.setTabText(
                0, f"Finished ({self._format_task_count(total_complete_tasks)})"
            )
            if num_incomplete_tasks_loaded < total_incomplete_tasks:
                self.tab_widget.setTabText(
                    1,
                    f"To Do ({num_incomplete_tasks_loaded}/{self._format_task_count(total_incomplete_tasks)} loaded)",
                )
            else:
                self.tab_widget.setTabText(
                    1, f"To Do ({self._format_task_count(total_incomplete_tasks)})"
                )

    def _format_task_count(self, count):
        if count == 0:
            return "no Tasks"
        elif count == 1:
            return "1 Task"
        else:
            return f"{count} Tasks"

    def edit_task(self, new_task):
        # Choose the correct layout based on the task's completion status
        layout = (
            self.content_widget_complete.layout()
            if new_task.complete
            else self.content_widget_incomplete.layout()
        )

        for i in range(layout.count()):
            task_widget = layout.itemAt(i).widget()
            if task_widget and task_widget.task.uuid == new_task.uuid:
                complete_toggled = task_widget.task.complete != new_task.complete
                task_widget.task = new_task
                if complete_toggled:
                    self.delete_task_widget(task_widget)
                    self.shared_state.task_widgets.delete(task_widget.task.uuid)
                    self.insert_task(new_task)
                return

    def delete_task_widget(self, task_uuid):
        for layout in [
            self.content_widget_complete.layout(),
            self.content_widget_incomplete.layout(),
        ]:
            for i in range(layout.count()):
                task_widget = layout.itemAt(i).widget()
                if task_widget and task_widget.task.uuid == task_uuid:
                    layout.removeWidget(
                        task_widget
                    )  # Remove the widget from the layout
                    task_widget.hide()  # Hide the widget
                    task_widget.deleteLater()  # Schedule the widget for deletion

                    self.update_tab_labels()
                    return

    def insert_task(self, task):
        task_widget = TaskWidget(task, self.shared_state)
        layout = (
            self.content_widget_complete.layout()
            if task.complete
            else self.content_widget_incomplete.layout()
        )

        # Find the correct index to insert the new task
        index = 0
        for i in range(layout.count()):
            existing_task_widget = layout.itemAt(i).widget()
            if (
                existing_task_widget
                and existing_task_widget.task.due_date < task.due_date
            ):
                break
            index += 1

        layout.insertWidget(index, task_widget)

        # add to shared state
        self.shared_state.task_widgets.add(task_widget)
        self.update_tab_labels()

    def load_more_tasks(self, all_tabs=False):
        tasks = []
        if all_tabs:
            complete_tasks = self.shared_state.database_client.lazy_load_tasks(
                self.scroll_area_complete.lazy_offset,
                self.scroll_area_complete.lazy_limit,
                True,
            )
            self.scroll_area_complete.lazy_offset += len(complete_tasks)
            incomplete_tasks = self.shared_state.database_client.lazy_load_tasks(
                self.scroll_area_incomplete.lazy_offset,
                self.scroll_area_incomplete.lazy_limit,
                False,
            )
            self.scroll_area_incomplete.lazy_offset += len(incomplete_tasks)
            tasks = complete_tasks + incomplete_tasks
        else:
            current_tab = self.tab_widget.currentWidget()
            tasks = self.shared_state.database_client.lazy_load_tasks(
                current_tab.lazy_offset,
                current_tab.lazy_limit,
                True if self.tab_widget.currentIndex() == 0 else False,
            )
            current_tab.lazy_offset += len(tasks)

        task_widgets = [TaskWidget(task, self.shared_state) for task in tasks]
        complete_widgets = [widget for widget in task_widgets if widget.task.complete]
        incomplete_widgets = [
            widget for widget in task_widgets if not widget.task.complete
        ]

        complete_layout = self.content_widget_complete.layout()
        for widget in complete_widgets:
            complete_layout.insertWidget(0, widget)

        incomplete_layout = self.content_widget_incomplete.layout()
        for widget in incomplete_widgets:
            incomplete_layout.insertWidget(0, widget)

        # update shared state with new widgets
        self.shared_state.task_widgets.add(task_widgets)
        self.update_tab_labels()

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
            # Check the current tab and use the appropriate list for the count
            if (
                self.tab_widget.currentIndex() == 0
            ):  # Assuming the "Complete" tab is at index 0
                loaded_widgets_count = len(self.shared_state.task_widgets.complete)
                total_tasks = self.shared_state.database_client.count_tasks(
                    complete=True
                )
            else:  # Assuming the "Incomplete" tab is at index 1
                loaded_widgets_count = len(self.shared_state.task_widgets.incomplete)
                total_tasks = self.shared_state.database_client.count_tasks(
                    complete=False
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
        self.shared_state.task_widgets.clear()

        # load the tasks
        self.load_more_tasks()

        # scroll to bottom in both tabs
        self.scroll_to_bottom()

        self.update_tab_labels()
