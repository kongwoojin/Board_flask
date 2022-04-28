import pymysql


def dbConnection():
    conn = pymysql.connect(
        user='',
        passwd='',
        host='',
        db='',
        charset='utf8',
        port=3306
    )
    return conn
