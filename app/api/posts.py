from flask import jsonify, request, g, url_for
from .decorators import permission_required
from .. import db
from ..models import Post, Permission
from . import api
from .errors import forbidden


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_post():
    """文章资源POST 请求的处理程序"""
    # print("request.json", request.json)
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, \
        {'Location': url_for('api.get_post', id=post.id)}


@api.route('/posts/')
def get_posts():
    """文章资源GET 请求的处理程序"""
    """处理获取文章集合的请求。这个函数使用列表推导生成所有文章的JSON 版本。"""
    posts = Post.query.all()
    return jsonify({'posts': [post.to_json() for post in posts]})


@api.route('/posts/<int:id>')
def get_post(id):
    """返回单篇博客文章"""
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required
def edit_post(id):
    """文章资源PUT 请求的处理程序"""
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())
