import sqlite3


class DBManager:

    def __init__(
            self,
    ):
        self.connection = sqlite3.connect("../sqlite/resources.db")

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


resource_manager = DBManager()
