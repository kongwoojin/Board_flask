#  Copyright © 2022 WooJin Kong. All rights reserved.

from datetime import datetime

import pymysql
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)


def connection():
    return pymysql.connect(
        user='',
        passwd='',
        host='',
        db='',
        charset='utf8'
    )


@app.route('/')
def index():
    conn = connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT * FROM `article`;"
    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'writerId': obj['writerId'],
            'date': obj['date']
        }
        data_list.append(data_dic)

    conn.close()

    return render_template('index.html', data_list=data_list)


@app.route('/board/<id>')
def board(id):
    conn = connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    sql = f'SELECT * FROM `article` where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchall()

    data = {
        'title': result[0]['title'],
        'text': result[0]['text'],
        'writerId': result[0]['writerId'],
        'date': result[0]['date']
    }

    conn.close()

    return render_template('board.html', data=data)


@app.route('/write')
def write():
    return render_template('write.html')


@app.route('/post', methods=['POST'])
def post():
    title = request.form.get('title')
    text = request.form.get('text')
    writerId = request.form.get('writerId')

    conn = connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    now = datetime.now()
    sql = f'INSERT INTO article(title, text, writerId, date) ' \
          f'VALUES("{title}", "{text}", "{writerId}", "{now.strftime("%Y-%m-%d %H:%M:%S")}")'
    cursor.execute(sql)
    conn.commit()

    conn.close()

    return "Done!"


@app.route('/api')
def api():
    conn = connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT * FROM `article`;"

    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'writerId': obj['writerId'],
            'date': obj['date']
        }
        data_list.append(data_dic)

    conn.close()

    return jsonify(data_list)


if __name__ == '__main__':
    app.run()
