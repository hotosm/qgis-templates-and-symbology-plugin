
import os
import sqlite3

DB_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'sqlite',
        'resources.db')
)


class DBManager:

    def __init__(
            self,
    ):
        self.connection = None

    def connect(self):
        self.connection = sqlite3.connect(DB_PATH)

    def get_all_templates(self):
        cur = self.connection.cursor()
        res = cur.execute("SELECT * FROM templates")
        templates = []

        for temp in res:
            template = Template(
                title=temp.title
            )
            templates.append(template)

        return templates


db_manager = DBManager()
db_manager.connect()
