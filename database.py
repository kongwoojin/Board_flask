import pymysql


class Database:
    def __init__(self):
        self.conn = None

    def dbConnection(self):
        self.conn = pymysql.connect(
            user='',
            passwd='',
            host='',
            db='',
            charset='',
            port=3306
        )
        return self.conn

    def dbDisconnection(self):
        if self.conn.open:
            self.conn.close()

    def getCursor(self):
        if self.conn is None or not self.conn.open:
            self.dbConnection()

        return self.conn.cursor(pymysql.cursors.DictCursor)
