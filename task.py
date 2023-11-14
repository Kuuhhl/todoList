import uuid
from datetime import datetime


class Task:
    def __init__(
        self,
        uuid_=None,
        image_uri="",
        description="Unnamed Task",
        deadline=datetime.now().strftime("%Y-%m-%d"),
        completed=False,
    ):
        if uuid_ is None:
            uuid_ = str(uuid.uuid4())
        self.uuid = uuid_
        self.description = description
        self.deadline = deadline
        self.image_uri = image_uri
        self.completed = completed

    def toggle_completed(self):
        self.completed = not self.completed
