#  Copyright © 2022 WooJin Kong. All rights reserved.
import os
from datetime import datetime

import pymysql
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash, send_from_directory
from flask_bcrypt import Bcrypt

import database

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'secret string'
app.config['CKEDITOR_FILE_UPLOADER'] = 'upload'

conn = database.dbConnection()

cursor = conn.cursor(pymysql.cursors.DictCursor)


def isXSSPossible(text):
    if "alert" in text:
        return True
    else:
        return False


def getUserName(id):
    sql = f'select * from users where id = {id}'
    cursor.execute(sql)
    result = cursor.fetchone()

    return result['username']


@app.route('/')
def index():
    sql = "select * from article;"
    cursor.execute(sql)
    result = cursor.fetchall()

    data_list = []

    for obj in result:
        data_dic = {
            'id': obj['id'],
            'title': obj['title'],
            'username': getUserName(obj['writer_id']),
            'date': obj['date'],
            'view_count': obj['view_count']
        }
        data_list.append(data_dic)

    return render_template('index.html', data_list=data_list, username=session['username'])


@app.route('/board/<id>')
def board(id):
    sql = f'update article set view_count = view_count + 1 where id = {id};'

    cursor.execute(sql)
    conn.commit()

    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    data = {
        'title': result['title'],
        'text': result['text'],
        'username': getUserName(result['writer_id']),
        'date': result['date'],
        'view_count': result['view_count'],
        'id': result['id']
    }

    sql = f'select * from comments where article_id ={id};'
    cursor.execute(sql)
    result = cursor.fetchall()

    comments = []

    for obj in result:
        comments_dic = {
            'writer': getUserName(obj['writer_id']),
            'comment': obj['comment'],
            'id': obj['id']
        }
        comments.append(comments_dic)

    return render_template('board.html', data=data, comments=comments, username=session['username'])


@app.route('/write')
def write():
    if session['userid'] == "":
        flash("Login first!")
        return redirect(url_for("signIn"))

    return render_template('write.html', username=session['username'])


@app.route('/edit/<int:id>')
def edit(id):
    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if session['id'] != result['writer_id']:
        flash("No permission!")
        return redirect(url_for("index"))

    sql = f'select * from article where id = {id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if result is not None:
        data = {
            'title': result['title'],
            'text': result['text']
        }

        return render_template('write.html', data=data, username=session['username'])
    else:
        return render_template('write.html', username=session['username'])


@app.route('/post', methods=['POST'])
def post():
    title = request.form.get('title')
    text = request.form.get('text').replace("\n", "<br/>")
    username = session['username']
    writer_id = int(session['id'])

    print(writer_id)
    print(request.referrer.split('/')[-1])

    now = datetime.now()
    if isXSSPossible(text):
        flash("XSS detected!")
        return redirect(url_for("index"))

    if "edit" in request.referrer:  # Edit article
        sql = f'update article set title = \'{title}\', text = \'{text}\' where id = {request.referrer.split("/")[-1]}'
    else:  # Write article
        sql = f'insert into article(title, text, username, date, writer_id) ' \
              f'values(\'{title}\', \'{text}\', \'{username}\', \'{now.strftime("%Y-%m-%d %H:%M:%S")}\', {writer_id})'
    print(sql)
    cursor.execute(sql)
    conn.commit()

    return redirect(url_for("index"))


@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if session['id'] != result['writer_id']:
        flash("No permission!")
        return redirect(url_for("index"))

    sql = f'delete from article where id = {id}'
    cursor.execute(sql)
    conn.commit()

    flash("Deleted!")
    return redirect(url_for("index"))


@app.route('/comment', methods=['POST'])
def comment():
    if session['userid'] == "":
        flash("Login first!")
        return '<script>document.location.href = document.referrer</script>'

    comment = request.form.get('comment')
    writer_id = int(session['id'])
    article_id = int(request.referrer.split('/')[-1])

    sql = f'insert into comments(comment, article_id, reply_to, writer_id) ' \
          f'values(\'{comment}\', \'{article_id}\', 0, {writer_id})'
    cursor.execute(sql)
    conn.commit()

    return '<script>document.location.href = document.referrer</script>'


@app.route('/signup')
def signUp():
    return render_template('signup.html')


@app.route('/signuppost', methods=['POST'])
def signUpPost():
    userid = request.form.get('userid')
    password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
    username = request.form.get('username')
    email = request.form.get('email')

    sqlForCheck = f"select * from users where userid = '{userid}';"
    cursor.execute(sqlForCheck)

    rowCount = cursor.rowcount

    if rowCount != 0:
        flash("User Exist!")
        return redirect(url_for("signUp"))

    sql = f'insert into users(userid, password, username, email) ' \
          f'values(\'{userid}\', \'{password}\', \'{username}\', \'{email}\')'
    cursor.execute(sql)
    conn.commit()

    flash("Success!")
    return redirect(url_for("index"))


@app.route('/signin')
def signIn():
    return render_template('signin.html')


@app.route('/signinpost', methods=['POST'])
def signInPost():
    userid = request.form.get('userid')
    password = request.form.get('password')

    sql = f"select * from users where userid = '{userid}';"
    cursor.execute(sql)
    result = cursor.fetchone()

    if cursor.rowcount == 0:
        flash("Wrong username!")
        return redirect(url_for("signIn"))

    if bcrypt.check_password_hash(result['password'], password):
        session['userid'] = userid
        session['username'] = result['username']
        session['id'] = result['id']

        return redirect(url_for("index"))
    else:
        flash("Wrong password!")
        return redirect(url_for("signIn"))


@app.route('/signout')
def signOut():
    session['userid'] = ""
    session['username'] = ""
    session['id'] = ""

    flash("Success!")
    return redirect(url_for("index"))


@app.route('/files/<path:filename>')
def uploaded_files(filename):
    path = '/the/uploaded/directory'
    return send_from_directory(path, filename)


# API part
@app.route('/api')
def api():
    sql = "select * from article;"

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
def apiPost():
    sql = "select * from article;"

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
def apiId(id):
    sql = f'select * from article where id={id};'

    cursor.execute(sql)
    result = cursor.fetchone()

    data = {
        'title': result['title'],
        'text': result['text'],
        'username': getUserName(result['id']),
        'date': result['date'],
        'view_count': result['view_count']
    }

    return jsonify(data)


@app.route('/api/comments/<int:id>')
def apiCommentId(id):
    sql = f'select * from comments where article_id ={id};'
    cursor.execute(sql)
    result = cursor.fetchall()

    comments = []

    for obj in result:
        comments_dic = {
            'writer': getUserName(obj['writer_id']),
            'comment': obj['comment'],
            'id': obj['id']
        }
        comments.append(comments_dic)

    return jsonify(comments)


@app.route('/api/users')
def apiUsers():
    sql = f'select * from users;'

    cursor.execute(sql)
    result = cursor.fetchone()

    data = {
        'id': result['id'],
        'userid': result['userid'],
        'username': getUserName(result['id']),
        'email': result['email']
    }

    return jsonify(data)


if __name__ == '__main__':
    app.run()
