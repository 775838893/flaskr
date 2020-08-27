from flask import Flask, redirect, render_template, session, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_migrate import Migrate
import pymysql

pymysql.install_as_MySQLdb()

app = Flask(__name__)
Bootstrap(app)  # 实例化bootstrap对象
moment = Moment(app)  # 实例化时间对象
app.config['SECRET_KEY'] = 'hard to guess string'

# 定义数据库URL
# mysql://username:password@hostname/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@127.0.0.1/flaskdemo'
# 如果设置成 True (默认情况)，Flask-SQLAlchemy 将会追踪对象的修改并且发送信号。
# 这需要额外的内存， 如果不必要的可以禁用它。
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 记录所有发到标准输出(stderr)的语句
# app.config['SQLALCHEMY_ECHO'] = True

# 应用使用的数据库
db = SQLAlchemy(app)

# 1.要使用flask_migrate,必须绑定app和DB
migrate = Migrate(app, db)


class Role(db.Model):
    # 定义在数据库中使用的表名
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 定义多的一方对应的关系，backref表示在User新建一个属性role
    users = db.relationship('User', backref='role', lazy='dynamic')

    """非必须, 用于在调试或测试时, 返回一个具有可读性的字符串表示模型."""

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    address = db.Column(db.String(128), nullable=True)
    hobby = db.Column(db.Text, default='看电影')
    telephone = db.Column(db.SmallInteger, nullable=True)
    # 定义外键
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<Role %r>' % self.username


# flaskr-wtf
class MyForm(FlaskForm):
    # 定义个input type=text字段并且验证数据要求不为空
    name = StringField('name', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/register/', methods=['GET', 'POST'])
def index():
    form = MyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
            session['name'] = form.name.data
            form.name.data = ''
        return redirect(url_for('index'))
    return render_template('register.html',
                           form=form, name=session.get('name'),
                           known=session.get('known', False))
