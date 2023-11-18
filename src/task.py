import uuid
from datetime import datetime


class Task:
    def __init__(
        self,
        uuid_=None,
        image_uri="",
        description="Unnamed Task",
        due_date=datetime.now().strftime("%Y-%m-%d"),
        complete=False,
    ):
        if uuid_ is None:
            uuid_ = str(uuid.uuid4())
        self.uuid = uuid_
        self.description = description
        self.due_date = due_date
        self.image_uri = image_uri
        self.complete = complete
