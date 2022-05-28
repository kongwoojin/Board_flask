from expiringdict import ExpiringDict
from database import Database

database = Database()


class Data:
    def __init__(self):
        self.userNameCache = ExpiringDict(max_len=100, max_age_seconds=3600)  # Caching usernames for 60 minutes

    def getUserName(self, id):
        if self.userNameCache.get(id) is None:
            cursor = database.getCursor()
            sql = f'select * from users where id = {id}'
            cursor.execute(sql)
            result = cursor.fetchone()

            userName = result['username']

            self.userNameCache[id] = userName

            database.dbDisconnection()

            return userName
        else:
            return self.userNameCache[id]
