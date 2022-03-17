#  Copyright © 2022 WooJin Kong. All rights reserved.

from datetime import datetime

import pymysql
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'secret string'

conn = pymysql.connect(
    user='',
    passwd='',
    host='',
    db='',
    charset='utf8',
    port=3306
)

cursor = conn.cursor(pymysql.cursors.DictCursor)


@app.route('/')
def index():
    sql = "SELECT * FROM `article`;"
    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'username': obj['username'],
            'date': obj['date']
        }
        data_list.append(data_dic)

    return render_template('index.html', data_list=data_list)


@app.route('/board/<id>')
def board(id):
    sql = f'update article set view_count = view_count + 1 where id = {id};'

    cursor.execute(sql)
    conn.commit()

    sql = f'SELECT * FROM `article` where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchall()

    data = {
        'title': result[0]['title'],
        'text': result[0]['text'],
        'username': result[0]['username'],
        'date': result[0]['date'],
        'view_count': result[0]['view_count'],
        'id': result[0]['id']
    }

    return render_template('board.html', data=data)


@app.route('/write')
def write():
    if session['userid'] == "":
        return redirect(url_for("signin"))

    return render_template('write.html')


@app.route('/edit/<int:id>')
def edit(id):
    sql = f'SELECT * FROM article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchall()

    if session['id'] != result[0]['writer_id']:
        return redirect(url_for("index"))

    return render_template('write.html')


@app.route('/post', methods=['POST'])
def post():
    title = request.form.get('title')
    text = request.form.get('text')
    username = session['username']
    writer_id = int(session['id'])

    print(writer_id)
    print(request.referrer.split('/')[-1])

    now = datetime.now()
    if "edit" in request.referrer:
        sql = f'update article set title = "{title}", text = "{text}" where id = {request.referrer.split("/")[-1]}'
    else:
        sql = f'INSERT INTO article(title, text, username, date, writer_id) ' \
              f'VALUES("{title}", "{text}", "{username}", "{now.strftime("%Y-%m-%d %H:%M:%S")}", {writer_id})'
    cursor.execute(sql)
    conn.commit()

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

    sqlForCheck = f"select * from users where userid = '{userid}';"
    cursor.execute(sqlForCheck)

    rowCount = cursor.rowcount

    if rowCount != 0:
        return '<script>alert("Exist!")</script>' \
               '<script>document.location.href = document.referrer</script>'

    sql = f'INSERT INTO users(userid, password, username, email) ' \
          f'VALUES("{userid}", "{password}", "{username}", "{email}")'
    cursor.execute(sql)
    conn.commit()

    return '<script>document.location.href = document.referrer</script>'


@app.route('/signin')
def signin():
    return render_template('signin.html')


@app.route('/signinpost', methods=['POST'])
def signinpost():
    userid = request.form.get('userid')
    password = request.form.get('password')

    sql = f"select * from users where userid = '{userid}';"
    cursor.execute(sql)
    result = cursor.fetchall()

    if cursor.rowcount == 0:
        return '<script>alert("Not found!")</script>' \
               '<script>document.location.href = document.referrer</script>'

    if bcrypt.check_password_hash(result[0]['password'], password):
        session['userid'] = userid
        session['username'] = result[0]['username']
        session['id'] = result[0]['id']

        return redirect(url_for("index"))
    else:

        return redirect(url_for("signin"))


@app.route('/signout')
def signout():
    session['userid'] = ""
    return redirect(url_for("index"))


@app.route('/api')
def api():
    sql = "SELECT * FROM `article`;"

    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'username': obj['username'],
            'date': obj['date']
        }
        data_list.append(data_dic)

    return jsonify(data_list)


@app.route('/api/post')
def api_post():
    sql = "SELECT * FROM `article`;"

    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'username': obj['username'],
            'date': obj['date'],
            'view_count': obj['view_count']
        }
        data_list.append(data_dic)

    return jsonify(data_list)


@app.route('/api/<int:id>')
def api_id(id):
    sql = f'SELECT * FROM article where id={id};'

    cursor.execute(sql)
    result = cursor.fetchall()

    data = {
        'title': result[0]['title'],
        'text': result[0]['text'],
        'username': result[0]['username'],
        'date': result[0]['date'],
        'view_count': result[0]['view_count']
    }

    return jsonify(data)


@app.route('/api/users')
def api_users():
    sql = f'SELECT * FROM users;'

    cursor.execute(sql)
    result = cursor.fetchall()

    data = {
        'id': result[0]['id'],
        'userid': result[0]['userid'],
        'username': result[0]['username'],
        'email': result[0]['email']
    }

    return jsonify(data)


if __name__ == '__main__':
    app.run()