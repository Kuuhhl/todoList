import sqlite3
import uuid


class TodoList:
    def __init__(self):
        self.db_name = "todo.db"
        self.conn, self.cur = self.connect_db()

    def connect_db(self):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS todo (id TEXT PRIMARY KEY, image_uri TEXT, task_desc TEXT, deadline DATETIME, completed BOOLEAN)"
        )
        return conn, cur

    def get_all_tasks(self):
        self.cur.execute("SELECT id FROM todo")
        task_ids = self.cur.fetchall()
        tasks = []
        for task_id in task_ids:
            tasks.append(self.get_task(task_id[0]))
        return tasks

    def get_task(self, taskId):
        self.cur.execute("SELECT * FROM todo WHERE id=?", (taskId,))
        task = self.cur.fetchone()
        return {
            "image_uri": task[1],
            "description": task[2],
            "deadline": task[3],
            "completed": bool(task[4]),
        }

    def add_task(self, new_task):
        # set default values
        defaults = {
            "description": "",
            "completed": False,
            "deadline": "",
            "image_uri": "",
        }
        new_task = {**defaults, **new_task}

        # generate uuid for the new task
        new_task["id"] = str(uuid.uuid4())

        self.cur.execute(
            "INSERT INTO todo (id, image_uri, task_desc, deadline, completed) VALUES (?, ?, ?, ?, ?)",
            (
                new_task["id"],
                new_task["image_uri"],
                new_task["description"],
                new_task["deadline"],
                new_task["completed"],
            ),
        )
        self.conn.commit()
        return new_task["id"]


# testing code
if __name__ == "__main__":
    db_name = "todo.db"
    todo = TodoList()
    task = {
        "image_uri": "images/1.png",
        "description": "Finish this tutorial",
        "deadline": "2020-07-31",
        "completed": True,
    }
    task_id = todo.add_task(task)
    print(todo.get_task(task_id))
    todo.conn.close()
