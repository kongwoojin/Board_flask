#  Copyright © 2022 WooJin Kong. All rights reserved.
import math
from datetime import datetime

from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt

from forms import *

from database import Database
from local_data import Data

import api

app = Flask(__name__)
app.register_blueprint(api.api_blue_print)

app.config['SECRET_KEY'] = 'abcdefg1234567'
bcrypt = Bcrypt(app)

database = Database()
local_data = Data()


def get_database():
    conn = database.db_connection()
    cursor = database.get_cursor()
    return conn, cursor


def is_xss_possible(text):
    if "<script>" in text:
        return True
    else:
        return False


@app.route('/')
def index():
    conn, cursor = get_database()
    cur_page = request.args.get('page')
    if cur_page is None:
        cur_page = 1
    else:
        cur_page = int(cur_page)

    article_per_page = 15

    sql = 'select count(*) from article;'
    cursor.execute(sql)
    result = cursor.fetchone()
    row_count = int(result['count(*)'])
    pages = math.ceil(row_count / article_per_page)

    sql = f'select * from article order by id desc limit {(cur_page - 1) * article_per_page}, {article_per_page};'
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

    return render_template('index.html', data_list=data_list, pages=pages, cur_page=cur_page)


@app.route('/board/<id>', methods=['GET', 'POST'])
def board(id):
    conn, cursor = get_database()
    form = CommentForm(request.form)

    if not form.is_submitted():
        sql = f'update article set view_count = view_count + 1 where id = {id};'

        cursor.execute(sql)
        conn.commit()

    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if cursor.rowcount == 0:
        flash("Article not exist!")
        return redirect(url_for('index'))
    else:
        data = {
            'title': result['title'],
            'text': result['text'],
            'username': local_data.get_user_name(result['writer_id']),
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
                'writer': local_data.get_user_name(obj['writer_id']),
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

        database.db_disconnection()

        return render_template('board.html', data=data, comments=comments, form=form)


@app.route('/write', methods=['GET', 'POST'])
def write():
    conn, cursor = get_database()
    if session.get('userid') is None:
        flash("Login first!")
        return redirect(url_for('signIn'))

    form = WriteForm(request.form)

    if form.validate_on_submit():
        title = form.title.data
        text = form.text.data
        writer_id = int(session['id'])

        now = datetime.now()
        if is_xss_possible(text):
            flash("XSS detected!")
            return redirect(url_for('index'))

        title = title.replace("'", "''")
        text = text.replace("'", "''")
        sql = f'insert into article(title, text, date, writer_id) ' \
              f'values(\'{title}\', \'{text}\', \'{now.strftime("%Y-%m-%d %H:%M:%S")}\', {writer_id})'
        cursor.execute(sql)
        conn.commit()

        return redirect(url_for('index'))

    database.db_disconnection()

    return render_template('write.html', form=form)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn, cursor = get_database()
    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if session.get('id') is None or session['id'] != result['writer_id']:
        flash("No permission!")
        return redirect(url_for('index'))

    sql = f'select * from article where id = {id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    form = WriteForm(request.form)

    if form.validate_on_submit(): # On submit
        title = form.title.data
        text = form.text.data

        if is_xss_possible(text):
            flash("XSS detected!")
            return redirect(url_for('index'))

        title = title.replace("'", "''")
        text = text.replace("'", "''")
        sql = f'update article set title = \'{title}\', text = \'{text}\' ' \
              f'where id = {request.referrer.split("/")[-1]}'
        cursor.execute(sql)
        conn.commit()

        return redirect(url_for('index'))

    else:
        data = {
            'title': result['title'],
            'text': result['text']
        }

        form.title.data = data['title']
        form.text.data = data['text']

    database.db_disconnection()

    return render_template('write.html', form=form)


@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    conn, cursor = get_database()
    sql = f'select * from article where id ={id};'
    cursor.execute(sql)
    result = cursor.fetchone()

    if session.get('id') is None or session['id'] != result['writer_id']:
        flash("No permission!")
        return redirect(url_for('index'))

    sql = f'delete from article where id = {id}'
    cursor.execute(sql)
    conn.commit()

    flash("Deleted!")
    database.db_disconnection()
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    conn, cursor = get_database()
    form = SignUpForm(request.form)
    if form.validate_on_submit():
        userid = form.userid.data
        username = form.username.data
        email = form.email.data
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        sql_for_check = f'select * from users where userid = \'{userid}\';'
        cursor.execute(sql_for_check)

        row_count = cursor.rowcount

        if row_count != 0:
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

    database.db_disconnection()

    return render_template('signup.html', form=form)


@app.route('/signin', methods=['GET', 'POST'])
def sign_in():
    conn, cursor = get_database()
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

    database.db_disconnection()

    return render_template('signin.html', form=form)


@app.route('/signout')
def sign_out():
    session.pop('username', None)
    session.pop('userid', None)
    session.pop('id', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    csrf = CSRFProtect()
    csrf.init_app(app)

    app.run()
