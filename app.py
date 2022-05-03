#  Copyright © 2022 WooJin Kong. All rights reserved.
import math
from datetime import datetime

import pymysql
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt

from forms import *

import database

app = Flask(__name__)
bcrypt = Bcrypt(app)

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
    curPage = (request.args.get('page'))
    if curPage is None:
        curPage = 1
    else:
        curPage = int(curPage)

    articlePerPage = 15

    sql = 'select count(*) from article;'
    cursor.execute(sql)
    result = cursor.fetchone()
    rowCount = int(result['count(*)'])
    pages = math.ceil(rowCount / articlePerPage)

    sql = f'select * from article order by id desc limit {(curPage - 1) * articlePerPage}, {articlePerPage};'

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

    return render_template('index.html', data_list=data_list, pages=pages, curPage=curPage)


@app.route('/board/<id>', methods=['GET', 'POST'])
def board(id):
    form = CommentForm(request.form)

    if not form.is_submitted():
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

    if form.is_submitted() and form.validate_on_submit():
        if session.get('userid') is None:
            flash("Login first!")
            return redirect(url_for('signIn'))
        else:
            comment = form.comment.data
            writer_id = int(session['id'])
            article_id = id

            sql = f'insert into comments(comment, article_id, reply_to, writer_id) ' \
                  f'values(\'{comment}\', \'{article_id}\', 0, {writer_id})'
            cursor.execute(sql)
            conn.commit()
            return redirect(url_for('board', id=id))

    return render_template('board.html', data=data, comments=comments, form=form)


@app.route('/write', methods=['GET', 'POST'])
def write():
    if session.get('userid') is None:
        flash("Login first!")
        return redirect(url_for('signIn'))

    form = WriteForm(request.form)

    if form.validate_on_submit():
        title = form.title.data
        text = form.text.data
        writer_id = int(session['id'])

        now = datetime.now()
        if isXSSPossible(text):
            flash("XSS detected!")
            return redirect(url_for('index'))

        sql = f'insert into article(title, text, date, writer_id) ' \
              f'values(\'{title}\', \'{text}\', \'{now.strftime("%Y-%m-%d %H:%M:%S")}\', {writer_id})'
        cursor.execute(sql)
        conn.commit()

        return redirect(url_for('index'))

    return render_template('write.html', form=form)


@app.route('/edit/<int:id>')
def edit(id):
    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if session['id'] != result['writer_id']:
        flash("No permission!")
        return redirect(url_for('index'))

    sql = f'select * from article where id = {id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    form = WriteForm(request.form)

    if result is not None:
        data = {
            'title': result['title'],
            'text': result['text']
        }

        form.title.data = data['title']
        form.text.data = data['text']

        if form.validate_on_submit():
            title = form.title.data
            text = form.text.data

            if isXSSPossible(text):
                flash("XSS detected!")
                return redirect(url_for('index'))

            sql = f'update article set title = \'{title}\', text = \'{text}\' ' \
                  f'where id = {request.referrer.split("/")[-1]}'
            cursor.execute(sql)
            conn.commit()

            return redirect(url_for('index'))

    return render_template('write.html', form=form)


@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if session['id'] != result['writer_id']:
        flash("No permission!")
        return redirect(url_for('index'))

    sql = f'delete from article where id = {id}'
    cursor.execute(sql)
    conn.commit()

    flash("Deleted!")
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    form = SignUpForm(request.form)
    if form.validate_on_submit():
        userid = form.userid.data
        username = form.username.data
        email = form.email.data
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        sqlForCheck = f'select * from users where userid = \'{userid}\';'
        cursor.execute(sqlForCheck)

        rowCount = cursor.rowcount

        if rowCount != 0:
            flash("User Exist!")
            return redirect(url_for('signUp'))

        sql = f'insert into users(userid, password, username, email) ' \
              f'values(\'{userid}\', \'{password}\', \'{username}\', \'{email}\')'
        cursor.execute(sql)
        conn.commit()

        return redirect(url_for('signIn'))
    else:
        for e in form.errors.values():
            print(e[0])
            flash(e[0])

    return render_template('signup.html', form=form)


@app.route('/signin', methods=['GET', 'POST'])
def signIn():
    form = SignInForm(request.form)
    if form.validate_on_submit():
        userid = form.userid.data
        password = form.password.data

        sql = f'select * from users where userid = \'{userid}\';'
        cursor.execute(sql)
        result = cursor.fetchone()

        if cursor.rowcount == 0:
            flash("Wrong username!")
            return redirect(url_for('signIn'))

        if bcrypt.check_password_hash(result['password'], password):
            session['userid'] = userid
            session['username'] = result['username']
            session['id'] = result['id']

            return redirect(url_for('index'))
        else:
            flash("Wrong password!")
            return redirect(url_for('signIn'))

    return render_template('signin.html', form=form)


@app.route('/signout')
def signOut():
    session.pop('username', None)
    session.pop('userid', None)
    session.pop('id', None)
    return redirect(url_for('index'))


# API part
@app.route('/api')
def api():
    sql = 'select * from article;'

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
    sql = 'select * from article;'

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
    app.config['SECRET_KEY'] = 'abcdefg1234567'

    csrf = CSRFProtect()
    csrf.init_app(app)

    app.run()
