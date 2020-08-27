import pymysql
from flask import render_template, url_for, request, flash, redirect
from flask_login import login_user, login_required, logout_user, current_user

from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
    PasswordResetRequestForm, PasswordResetForm
from ..email import send_email
from ..models import User, db

pymysql.install_as_MySQLdb()


@auth.route('/login', methods=['GET', 'POST'])
def login():
    '''登录'''
    form = LoginForm()
    # post 当表单提交时执行
    if form.validate_on_submit():
        # 校验数据
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.valify_password(form.password.data):
            login_user(user, form.remember_me.data)
            # 获取url参数中是否访问了其他页面的地址，类似Django的next
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('账户或密码有误')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    '''注销'''
    # ，删除并重设用户会话
    logout_user()
    flash('你已登出')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    # 是否点击提交按钮：POST
    if form.validate_on_submit():
        # 插入数据
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)  # 调用User的setter属性方法password
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()

        # 发送电子邮件
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)

        flash('一封验证用户的邮件已发送到你的邮箱.')

        # 跳转
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('你已认证你的账户，感谢！')
    else:
        flash('认证链接无效或者已过期.')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    '''请求钩子，在请求之前做点事'''
    if current_user.is_authenticated:  # 当前用户已登录
        # 更新已登录用户的最后访问时间
        current_user.ping()
        # 如果用户的comfirmed为Flase
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    """没有认证则判断是否匿名用户，或者已经认证过了，不是就调到认证页面"""
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    '''重新发送账户确认邮件'''
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('一封新的认证邮件已经发送到你邮箱.')
    return redirect(url_for('main.index'))


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('你的邮件地址已更新.')
    else:
        flash('无效的请求.')
    return redirect(url_for('main.index'))


@auth.route('/change_password/', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码视图函数"""
    form = ChangePasswordForm()

    if form.validate_on_submit():

        # 校验数据
        if current_user.valify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('密码已更新')
            return redirect(url_for('main.index'))
        else:
            flash('原密码不正确')

    return render_template('auth/change_password.html', form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    """重置密码前的请求"""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '重置你的密码', 'auth/email/reset_password',
                       user=user, token=token, next=request.args.get('next'))
            flash('重置密码的邮件已发送到你邮箱')
            return redirect(url_for('auth.login'))
        else:
            flash('邮箱不存在')
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """重置密码"""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('密码已更新。')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))

    return render_template('auth/reset_password.html', form=form)


# @auth.route('/check_email', methods=['POST'])
# def check_email_response():
#     recv_data = request.get_json()  # 得到前端传送的json数据
#     email = recv_data.get('email')
#     if not email:
#         return jsonify({'res': 0, 'errmsg': '邮箱不能为空'})
#
#     has_email = User.query.filter_by(email=email).first()
#     if has_email:
#         return jsonify({'res': 1, 'message': 'success'})
#     else:
#         return jsonify({'res': 2, 'errmsg': '没有此邮箱账户'})

