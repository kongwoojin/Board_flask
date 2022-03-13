#  Copyright © 2022 WooJin Kong. All rights reserved.

from datetime import datetime

import pymysql
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'secret string'


def connection():
    return pymysql.connect(
        user='',
        passwd='',
        host='',
        db='',
        charset='utf8',
        port=3306
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
    if session['id'] == "":
        return redirect(url_for("signin"))

    return render_template('write.html')


@app.route('/post', methods=['POST'])
def post():
    title = request.form.get('title')
    text = request.form.get('text')
    writerId = session['username']

    conn = connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    now = datetime.now()
    sql = f'INSERT INTO article(title, text, writerId, date) ' \
          f'VALUES("{title}", "{text}", "{writerId}", "{now.strftime("%Y-%m-%d %H:%M:%S")}")'
    cursor.execute(sql)
    conn.commit()

    conn.close()

    return redirect(url_for("index"))


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/signuppost', methods=['POST'])
def signuppost():
    userid = request.form.get('userid')
    password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
    username = request.form.get('username')
    email = request.form.get('email')

    conn = connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sqlForCheck = f"select * from users where userid = '{userid}';"
    cursor.execute(sqlForCheck)

    rowCount = cursor.rowcount

    if rowCount != 0:
        conn.close()
        return '<script>alert("Exist!")</script>' \
               '<script>document.location.href = document.referrer</script>'

    sql = f'INSERT INTO users(userid, password, username, email) ' \
          f'VALUES("{userid}", "{password}", "{username}", "{email}")'
    cursor.execute(sql)
    conn.commit()

    conn.close()

    return '<script>document.location.href = document.referrer</script>'


@app.route('/signin')
def signin():
    return render_template('signin.html')


@app.route('/signinpost', methods=['POST'])
def signinpost():
    userid = request.form.get('userid')
    password = request.form.get('password')

    conn = connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    sql = f"select * from users where userid = '{userid}';"
    cursor.execute(sql)
    result = cursor.fetchall()

    if cursor.rowcount == 0:
        return '<script>alert("Not found!")</script>' \
               '<script>document.location.href = document.referrer</script>'

    if bcrypt.check_password_hash(result[0]['password'], password):
        session['id'] = userid
        session['username'] = result[0]['username']
        conn.close()
        return redirect(url_for("index"))
    else:
        conn.close()
        return redirect(url_for("signin"))


@app.route('/signout')
def signout():
    session['id'] = ""
    return redirect(url_for("index"))


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
