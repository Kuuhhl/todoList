import json
import uuid
import sqlite3
from PyQt6.QtCore import pyqtSignal, QObject
from task import Task


class DatabaseClient(QObject):
    # Signals
    added_task = pyqtSignal(object)
    imported_tasks = pyqtSignal(int)
    edited_task = pyqtSignal(object)
    deleted_task = pyqtSignal(str)
    cleared_tasks = pyqtSignal()
    loaded_tasks = pyqtSignal(list)

    def __init__(self, db_name):
        super().__init__()
        self.db_name = db_name
        self.conn, self.cur = self.connect_db()

    def connect_db(self):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        cur.execute(
            "create table if not exists todo (uuid text primary key, image_uri text, task_desc text, due_date text, complete integer)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_todo_complete_due_date ON todo (complete, due_date)"
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
        if task is None:
            return None
        return Task(
            task[0],
            task[1],
            task[2],
            task[3],
            bool(task[4]),
        )

    def count_tasks(self, complete=None):
        if complete is None:
            self.cur.execute("SELECT COUNT(*) FROM todo")
        else:
            self.cur.execute(
                "SELECT COUNT(*) FROM todo WHERE complete=?", (int(complete),)
            )
        return self.cur.fetchone()[0]

    def lazy_load_tasks(self, offset, limit, complete=None):
        if complete is None:
            query = "SELECT * FROM todo ORDER BY due_date ASC LIMIT ? OFFSET ?"
            params = (limit, offset)
        else:
            query = "SELECT * FROM todo WHERE complete = ? ORDER BY due_date ASC LIMIT ? OFFSET ?"
            params = (int(complete), limit, offset)

        self.cur.execute(query, params)
        res = [Task(*row) for row in self.cur.fetchall()]
        self.loaded_tasks.emit(res)
        return res

    def add_task(self, new_task):
        self.cur.execute(
            "insert into todo (uuid, image_uri, task_desc, due_date, complete) values (?, ?, ?, ?, ?)",
            (
                new_task.uuid,
                new_task.image_uri,
                new_task.description,
                new_task.due_date,
                int(new_task.complete),
            ),
        )
        self.conn.commit()
        self.added_task.emit(new_task)

    def edit_task(self, edited_task):
        self.cur.execute(
            "update todo set image_uri=?, task_desc=?, due_date=?, complete=? where uuid=?",
            (
                edited_task.image_uri,
                edited_task.description,
                edited_task.due_date,
                int(edited_task.complete),
                edited_task.uuid,
            ),
        )
        self.conn.commit()
        self.edited_task.emit(edited_task)

    def delete_task(self, task_uuid):
        self.cur.execute("delete from todo where uuid=?", (task_uuid,))
        self.conn.commit()
        self.deleted_task.emit(task_uuid)

    def clear_all(self):
        self.cur.execute("delete from todo")
        self.conn.commit()
        self.cleared_tasks.emit()

    def import_from_file(self, file_path):
        with open(file_path, "r") as f:
            tasks = json.load(f)

        task_objects = [
            (
                str(uuid.uuid4()),
                task.get("image_uri", None),
                task.get("description", None),
                task.get("due_date", None),
                int(task.get("complete", None)),
            )
            for task in tasks
        ]

        self.conn.execute("BEGIN TRANSACTION")

        try:
            self.cur.executemany(
                "INSERT INTO todo (uuid, image_uri, task_desc, due_date, complete) VALUES (?, ?, ?, ?, ?)",
                task_objects,
            )
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"An error occurred: {e}")
        else:
            self.conn.commit()

        self.imported_tasks.emit(len(tasks))

    def export_to_file(self, file_path):
        tasks = self.get_all_tasks()
        with open(file_path, "w") as f:
            f.write(json.dumps([self.task_to_dict(task) for task in tasks], indent=4))

    @staticmethod
    def task_to_dict(task):
        return {
            "image_uri": task.image_uri,
            "description": task.description,
            "due_date": task.due_date,
            "complete": task.complete,
        }


if __name__ == "__main__":
    pass
