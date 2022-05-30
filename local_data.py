from expiringdict import ExpiringDict
from database import Database

database = Database()


class Data:
    def __init__(self):
        self.user_name_cache = ExpiringDict(max_len=100, max_age_seconds=3600)  # Caching usernames for 60 minutes

    def get_user_name(self, id):
        if self.user_name_cache.get(id) is None:
            cursor = database.get_cursor()
            sql = f'select * from users where id = {id}'
            cursor.execute(sql)
            result = cursor.fetchone()

            user_name = result['username']

            self.user_name_cache[id] = user_name

            database.db_disconnection()

            return user_name
        else:
            return self.user_name_cache[id]
