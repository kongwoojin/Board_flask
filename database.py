import pymysql


class Database:
    def __init__(self):
        self.conn = None

    def db_connection(self):
        self.conn = pymysql.connect(
            user='',
            passwd='',
            host='',
            db='',
            charset='',
            port=3306
        )
        return self.conn

    def db_disconnection(self):
        if self.conn.open:
            self.conn.close()

    def get_cursor(self):
        if self.conn is None or not self.conn.open:
            self.db_connection()

        return self.conn.cursor(pymysql.cursors.DictCursor)
