from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User
from . import api
from .errors import unauthorized, forbidden

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    """初始化Flask-HTTPAuth"""
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User.valify_password(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False

    g.current_user = user
    g.token_used = False
    return user.valify_password(password)


@auth.error_handler
def auth_error():
    """Flask-HTTPAuth 错误处理程序"""
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    """据绝已通过身份验证但还没有确认账户的用户"""
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/tokens/', methods=['GET', 'POST'])
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
