from flask import Flask, request, current_app, render_template, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from datetime import datetime

app = Flask(__name__)
# 设置秘钥,CSRF需要用到
app.config['SECRET_KEY'] = 'hard to guess string'
moment = Moment(app)  # 实例化时间对象
Bootstrap(app)  # 实例化bootstrap对象

# app.debug = True  # 打开调试模式,flask1.0后不支持,使用set FLASK_DEBUG = True
app_ctx = app.app_context()  # 获取应用上下文，不激活直接使用会报错
app_ctx.push()

print(current_app.name)

# flask-wtf
class MyForm(FlaskForm):
    # 定义个input type=text字段并且验证数据要求不为空
    name = StringField('name', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/')
def hello_world():
    # 格式化时间
    return render_template('index.html', current_time=datetime.utcnow())


@app.route('/user/<name>')
def user(name):
    return '<h1>Hello, {}</h1>'.format(name)


@app.route('/index')
def index():
    user_agent = request.headers.get('User-Agent')
    return 'your browser is %s' % user_agent


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = MyForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            # 消息闪现 flash()函数把消息存储在session中
            # html页面使用get_flashed_messages()获取消息
            flash('你似乎改了用户名','error')
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('register.html', name=session.get('name'), form=form)


@app.route('/redirect')
def myredirect():
    return redirect(url_for('hello_world'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(error):
    return render_template('500.html'), 500


print(app.url_map)

# if __name__ == '__main__':
#     python.exe -m flaskr run
#
#     app.run()
