from pysqlcipher3 import dbapi2 as sqlite3
import os
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
import json
from PyQt6.QtCore import pyqtSignal, QObject
from task import Task


class DatabaseClient(QObject):
    """
    A class to handle database operations for a todo list application.

    Attributes:
    - db_name (str): The name of the database file.
    - conn (sqlite3.Connection): The connection object to the database.
    - cur (sqlite3.Cursor): The cursor object to execute SQL statements.
    """

    task_modified = pyqtSignal()

    def __init__(self, key, db_name):
        """
        Initializes a DatabaseClient object by connecting to the database and creating a cursor object.
        """
        super().__init__()
        self.db_name = db_name
        self.key = key
        self.conn, self.cur = self.connect_db()

    def connect_db(self):
        """
        Connects to the database and creates a cursor object.

        Returns:
        - conn (sqlite3.Connection): The connection object to the database.
        - cur (sqlite3.Cursor): The cursor object to execute SQL statements.
        """
        if os.path.exists(self.db_name):
            try:
                conn = sqlite3.connect(self.db_name)
                conn.execute(f"PRAGMA key = '{self.key}';")
                cur = conn.cursor()
            except sqlite3.DatabaseError as exc:
                raise (sqlite3.DatabaseError("Incorrect encryption key")) from exc
        else:
            conn = sqlite3.connect(self.db_name)
            conn.execute(f"PRAGMA key = '{self.key}';")
            cur = conn.cursor()

        cur.execute(
            "create table if not exists todo (uuid text primary key, image_uri text, task_desc text, deadline datetime, completed boolean)"
        )
        return conn, cur

    def get_all_tasks(self):
        """
        Retrieves all tasks from the database.

        Returns:
        - tasks (list): A list of Task objects.
        """
        self.cur.execute("select uuid from todo")
        task_uuids = self.cur.fetchall()
        tasks = []
        for task_uuid in task_uuids:
            tasks.append(self.get_task(task_uuid[0]))
        return tasks

    def get_task(self, task_uuid):
        """
        Retrieves a task from the database by its UUID.

        Args:
        - task_uuid (str): The UUID of the task to retrieve.

        Returns:
        - task (Task): A Task object.
        """
        self.cur.execute("select * from todo where uuid=?", (task_uuid,))
        task = self.cur.fetchone()
        return Task(
            task[0],
            task[1],
            task[2],
            task[3],
            bool(task[4]),
        )

    def count_tasks(self):
        """
        Count the total number of tasks in the database.
        """
        self.cur.execute("SELECT COUNT(*) FROM tasks")
        return self.cur.fetchone()[0]

    def lazy_load_tasks(self, offset, limit):
        """
        Load a specific number of tasks from the database starting from a specific offset.
        """
        self.cur.execute(
            "SELECT * FROM tasks ORDER BY deadline ASC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [Task(*row) for row in self.cur.fetchall()]

    def add_task(self, new_task):
        """
        Adds a new task to the database.

        Args:
        - new_task (Task): The Task object to add to the database.
        """
        self.cur.execute(
            "insert into todo (uuid, image_uri, task_desc, deadline, completed) values (?, ?, ?, ?, ?)",
            (
                new_task.uuid,
                new_task.image_uri,
                new_task.description,
                new_task.deadline,
                new_task.completed,
            ),
        )
        self.conn.commit()
        self.task_modified.emit()

    def edit_task(self, task_uuid, new_task):
        """
        Edits an existing task in the database.

        Args:
        - task_uuid (str): The UUID of the task to edit.
        - new_task (Task): The new Task object to replace the existing task.
        """
        self.cur.execute(
            "update todo set image_uri=?, task_desc=?, deadline=?, completed=? where uuid=?",
            (
                new_task.image_uri,
                new_task.description,
                new_task.deadline,
                new_task.completed,
                task_uuid,
            ),
        )
        self.conn.commit()
        self.task_modified.emit()

    def delete_task(self, task_uuid):
        """
        Deletes a task from the database.

        Args:
        - task_uuid (str): The UUID of the task to delete.
        """
        self.cur.execute("delete from todo where uuid=?", (task_uuid,))
        self.conn.commit()
        self.task_modified.emit()

    def clear_all(self):
        """
        Deletes all tasks from the database.
        """
        self.cur.execute("delete from todo")
        self.conn.commit()
        self.task_modified.emit()

    def import_from_file(self, file_path):
        """
        Imports tasks from a JSON file and adds them to the database.

        Args:
        - file_path (str): The path to the JSON file.
        """
        with open(file_path, "r") as f:
            try:
                tasks = json.loads(f.read())
            except json.JSONDecodeError as exc:
                raise Exception("Invalid JSON file") from exc

        # Prepare the tasks for insertion
        task_objects = [
            Task(
                uuid_=task.get("uuid", None),
                image_uri=task.get("image_uri", None),
                description=task.get("description", None),
                deadline=task.get("deadline", None),
                completed=task.get("completed", None),
            )
            for task in tasks
        ]

        tasks_to_insert = [
            (
                task.uuid,
                task.image_uri,
                task.description,
                task.deadline,
                task.completed,
            )
            for task in task_objects
        ]

        # Insert the tasks into the database
        self.cur.executemany(
            "INSERT INTO todo (uuid, image_uri, task_desc, deadline, completed) VALUES (?, ?, ?, ?, ?)",
            tasks_to_insert,
        )
        self.conn.commit()
        self.task_modified.emit()

    def export_to_file(self, file_path):
        """
        Exports all tasks from the database to a JSON file.

        Args:
        - file_path (str): The path to the JSON file.
        """
        tasks = self.get_all_tasks()
        with open(file_path, "w") as f:
            f.write(json.dumps([self.task_to_dict(task) for task in tasks], indent=4))

    def task_to_dict(self, task):
        """
        Converts a Task object to a dictionary.

        Args:
        - task (Task): The Task object to convert.

        Returns:
        - task_dict (dict): A dictionary representation of the Task object.
        """
        return {
            "image_uri": task.image_uri,
            "description": task.description,
            "deadline": task.deadline,
            "completed": task.completed,
        }


if __name__ == "__main__":
    pass
