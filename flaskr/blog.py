from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from flask.views import MethodView
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


class IndexView(MethodView):
    def get(self):
        db = get_db()
        posts = db.execute(
            'SELECT p.id, title, body, created, author_id, username'
            ' FROM post p JOIN user u ON p.author_id = u.id'
            ' ORDER BY created DESC'
        ).fetchall()
        return render_template('blog/index.html', posts=posts)


class CreateView(MethodView):
    decorators = [login_required]

    def get(self):
        return render_template('blog/create.html')

    def post(self):
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

        return render_template('blog/create.html')


class UpdateView(MethodView):
    decorators = [login_required]

    def get(self, id):
        post = get_post(id)
        return render_template('blog/update.html', post=post)

    def post(self, id):
        post = get_post(id)
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

        return render_template('blog/update.html', post=post)


class DeleteView(MethodView):
    decorators = [login_required]

    def delete(self, id):
        get_post(id)
        db = get_db()
        db.execute('DELETE FROM post WHERE id = ?', (id,))
        db.commit()
        return redirect(url_for('blog.index'))


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


bp.add_url_rule('/', view_func=IndexView.as_view('index'))
bp.add_url_rule('/create', view_func=CreateView.as_view('create'))
bp.add_url_rule('/<int:id>/update', view_func=UpdateView.as_view('update'))
bp.add_url_rule('/<int:id>/delete', view_func=DeleteView.as_view('delete'))