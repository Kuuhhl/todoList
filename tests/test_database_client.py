import sys
import tempfile
import os
import unittest
import sqlite3
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from database_client import DatabaseClient, Task


class TestDatabaseClient(unittest.TestCase):
    def setUp(self):
        self.db_name = ":memory:"
        self.client = DatabaseClient(self.db_name)

    def test_connect_db(self):
        conn, cur = self.client.connect_db()
        self.assertIsInstance(conn, sqlite3.Connection)
        self.assertIsInstance(cur, sqlite3.Cursor)

    def test_get_all_tasks(self):
        tasks = self.client.get_all_tasks()
        self.assertIsInstance(tasks, list)
        for task in tasks:
            self.assertIsInstance(task, Task)

    def test_get_task_when_task_is_in_database(self):
        # Setup: Add a task to the database
        task_uuid = "task_uuid"
        original_task = Task(task_uuid, "image_uri", "description", "due_date", False)
        self.client.add_task(original_task)

        # Fetch the task from the database
        task = self.client.get_task(task_uuid)

        # Check that the fetched task matches the original task
        self.assertIsInstance(task, Task)
        self.assertEqual(task.uuid, original_task.uuid)
        self.assertEqual(task.image_uri, original_task.image_uri)
        self.assertEqual(task.description, original_task.description)
        self.assertEqual(task.due_date, original_task.due_date)
        self.assertEqual(task.complete, original_task.complete)

    def test_get_task_when_task_is_not_in_database(self):
        # Try to fetch a task that doesn't exist in the database
        task_uuid = "non_existent_task_uuid"
        task = self.client.get_task(task_uuid)

        # Check that no task was returned
        self.assertIsNone(task)

    def test_count_tasks(self):
        count = self.client.count_tasks()
        self.assertIsInstance(count, int)

    def test_lazy_load_tasks(self):
        offset = 0
        limit = 10
        tasks = self.client.lazy_load_tasks(offset, limit)
        self.assertIsInstance(tasks, list)
        for task in tasks:
            self.assertIsInstance(task, Task)

    def test_add_task(self):
        # Create a new task and add it to the database
        new_task = Task("uuid", "image_uri", "description", "due_date", True)
        self.client.add_task(new_task)

        # Fetch the task from the database
        fetched_task = self.client.get_task(new_task.uuid)

        # Check that the fetched task's attributes match the original task's attributes
        self.assertEqual(fetched_task.uuid, new_task.uuid)
        self.assertEqual(fetched_task.image_uri, new_task.image_uri)
        self.assertEqual(fetched_task.description, new_task.description)
        self.assertEqual(fetched_task.due_date, new_task.due_date)
        self.assertEqual(fetched_task.complete, new_task.complete)

    def test_edit_task(self):
        # Setup: Add a task to the database
        original_task = Task("uuid", "image_uri", "description", "due_date", False)
        self.client.add_task(original_task)

        # Edit the task
        edited_task = Task(
            "uuid", "new_image_uri", "new_description", "new_due_date", False
        )
        self.client.edit_task(edited_task)

        # Fetch the task from the database and check its properties
        task = self.client.get_task(edited_task.uuid)
        self.assertEqual(task.image_uri, edited_task.image_uri)
        self.assertEqual(task.description, edited_task.description)
        self.assertEqual(task.due_date, edited_task.due_date)
        self.assertEqual(task.complete, edited_task.complete)

    def test_delete_task(self):
        task_uuid = "task_uuid"
        self.client.delete_task(task_uuid)
        tasks = self.client.get_all_tasks()
        self.assertNotIn(task_uuid, [task.uuid for task in tasks])

    def test_clear_all(self):
        self.client.clear_all()
        tasks = self.client.get_all_tasks()
        self.assertEqual(len(tasks), 0)

    def test_import_from_file(self):
        file_path = os.path.join(tempfile.gettempdir(), "test_tasks.json")
        tasks = [
            {
                "uuid": "uuid1",
                "image_uri": "image_uri1",
                "description": "description1",
                "due_date": "due_date1",
                "complete": True,
            },
            {
                "uuid": "uuid2",
                "image_uri": "image_uri2",
                "description": "description2",
                "due_date": "due_date2",
                "complete": False,
            },
        ]
        with open(file_path, "w") as f:
            json.dump(tasks, f)
        self.client.import_from_file(file_path)
        imported_tasks = self.client.get_all_tasks()
        self.assertEqual(len(imported_tasks), len(tasks))

        os.remove(file_path)

    def test_export_to_file(self):
        file_path = os.path.join(tempfile.gettempdir(), "test_exported_tasks.json")
        self.client.export_to_file(file_path)
        with open(file_path, "r") as f:
            exported_tasks = json.load(f)
        self.assertIsInstance(exported_tasks, list)
        for task in exported_tasks:
            self.assertIsInstance(task, dict)
        os.remove(file_path)

    def tearDown(self):
        self.client.conn.close()


if __name__ == "__main__":
    unittest.main()
