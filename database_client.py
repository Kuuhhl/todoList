import sqlite3
import time
import json
from PyQt6.QtCore import pyqtSignal, QObject
from task import Task


class DatabaseClient(QObject):
    task_modified = pyqtSignal()
    update_progress_bar = pyqtSignal(bool, int, int, int)

    def __init__(self):
        super().__init__()
        self.db_name = "todo.db"
        self.conn, self.cur = self.connect_db()

    def connect_db(self):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute(
            "create table if not exists todo (uuid text primary key, image_uri text, task_desc text, deadline datetime, completed boolean)"
        )
        return conn, cur

    def get_all_tasks(self):
        self.cur.execute("select uuid from todo")
        task_uuids = self.cur.fetchall()
        tasks = []
        for task_uuid in task_uuids:
            tasks.append(self.get_task(task_uuid[0]))
        return tasks

    def get_task(self, task_uuid):
        self.cur.execute("select * from todo where uuid=?", (task_uuid,))
        task = self.cur.fetchone()
        return Task(
            task[0],
            task[1],
            task[2],
            task[3],
            bool(task[4]),
        )

    def add_task(self, new_task):
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
        print("added task modified")
        self.task_modified.emit()

    def edit_task(self, task_uuid, new_task):
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
        print("edited task modified")
        self.task_modified.emit()

    def delete_task(self, task_uuid):
        self.cur.execute("delete from todo where uuid=?", (task_uuid,))
        self.conn.commit()
        print("deleted task modified")
        self.task_modified.emit()

    def clear_all(self):
        self.cur.execute("delete from todo")
        self.conn.commit()
        print("cleared all tasks modified")
        self.task_modified.emit()

    def import_from_file(self, file_path):
        with open(file_path, "r") as f:
            try:
                tasks = json.loads(f.read())
            except json.JSONDecodeError as exc:
                raise Exception("Invalid JSON file") from exc
        self.update_progress_bar.emit(True, 0, 0, len(tasks))
        for i, task in enumerate(tasks):
            self.add_task(
                Task(
                    image_uri=task.get("image_uri", None),
                    description=task.get("description", None),
                    deadline=task.get("deadline", None),
                    completed=task.get("completed", None),
                )
            )
            self.update_progress_bar.emit(True, i + 1, 0, len(tasks))
            print(f"imported {i+1}/{len(tasks)} tasks")
        self.update_progress_bar.emit(False, 0, 0, 0)

    def export_to_file(self, file_path):
        tasks = self.get_all_tasks()
        with open(file_path, "w") as f:
            f.write(json.dumps([self.task_to_dict(task) for task in tasks], indent=4))

    def task_to_dict(self, task):
        return {
            "image_uri": task.image_uri,
            "description": task.description,
            "deadline": task.deadline,
            "completed": task.completed,
        }


if __name__ == "__main__":
    pass
