from flask import jsonify, Blueprint

from database import Database
from local_data import Data

database = Database()
localData = Data()
blue_api = Blueprint('api', __name__, url_prefix='/api')


def getDatabase():
    conn = database.dbConnection()
    cursor = database.getCursor()
    return conn, cursor


# API part
@blue_api.route('/')
def api():
    conn, cursor = getDatabase()
    sql = 'select * from article;'

    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'username': localData.getUserName(obj['writer_id']),
            'date': obj['date'],
            'view_count': obj['view_count']
        }
        data_list.append(data_dic)

    database.dbDisconnection()

    return jsonify(data_list)


@blue_api.route('/<int:id>/')
def apiId(id):
    conn, cursor = getDatabase()
    sql = f'select * from article where id={id};'

    cursor.execute(sql)
    result = cursor.fetchone()

    data = {
        'title': result['title'],
        'text': result['text'],
        'username': localData.getUserName(result['writer_id']),
        'date': result['date'],
        'view_count': result['view_count']
    }

    database.dbDisconnection()

    return jsonify(data)


@blue_api.route('/comments/<int:id>/')
def apiCommentId(id):
    conn, cursor = getDatabase()
    sql = f'select * from comments where article_id ={id};'
    cursor.execute(sql)
    result = cursor.fetchall()

    comments = []

    for obj in result:
        comments_dic = {
            'writer': localData.getUserName(obj['writer_id']),
            'comment': obj['comment'],
            'id': obj['id']
        }
        comments.append(comments_dic)

    database.dbDisconnection()

    return jsonify(comments)
