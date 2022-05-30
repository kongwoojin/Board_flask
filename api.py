from flask import jsonify, Blueprint

from database import Database
from local_data import Data

database = Database()
local_data = Data()
api_blue_print = Blueprint('api', __name__, url_prefix='/api')


def get_database():
    conn = database.db_connection()
    cursor = database.get_cursor()
    return conn, cursor


# API part
@api_blue_print.route('/')
def api():
    conn, cursor = get_database()
    sql = 'select * from article order by id desc;'

    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'username': local_data.get_user_name(obj['writer_id']),
            'date': obj['date'],
            'view_count': obj['view_count']
        }
        data_list.append(data_dic)

    database.db_disconnection()

    return jsonify(data_list)


@api_blue_print.route('/<int:id>/')
def apiId(id):
    conn, cursor = get_database()
    sql = f'select * from article where id={id};'

    cursor.execute(sql)
    result = cursor.fetchone()

    data = {
        'title': result['title'],
        'text': result['text'],
        'username': local_data.get_user_name(result['writer_id']),
        'date': result['date'],
        'view_count': result['view_count']
    }

    database.db_disconnection()

    return jsonify(data)


@api_blue_print.route('/comments/<int:id>/')
def apiCommentId(id):
    conn, cursor = get_database()
    sql = f'select * from comments where article_id ={id};'
    cursor.execute(sql)
    result = cursor.fetchall()

    comments = []

    for obj in result:
        comments_dic = {
            'writer': local_data.get_user_name(obj['writer_id']),
            'comment': obj['comment'],
            'id': obj['id']
        }
        comments.append(comments_dic)

    database.db_disconnection()

    return jsonify(comments)
