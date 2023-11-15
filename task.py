import uuid
from datetime import datetime


class Task:
    """
    A class representing a task in a todo list.

    Attributes:
    -----------
    uuid : str
        Unique identifier for the task.
    image_uri : str
        URI for the image associated with the task.
    description : str
        Description of the task.
    deadline : str
        Deadline for the task in the format '%Y-%m-%d'.
    completed : bool
        Indicates whether the task is completed or not.
    """

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
        """
        Toggles the completed status of the task.
        """
        self.completed = not self.completed
