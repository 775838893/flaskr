from . import db, login_manager
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app.exceptions import ValidationError
from datetime import datetime
from markdown import markdown
import bleach
import hashlib


class Follow(db.Model):
    """自引用关系表，关注者和被关注者是从user表关联"""
    __tablename__ = 'follows'
    # users to follow other
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    # users to be followed
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# UserMixin 实现了flask_login必须要实现的方法
# (is_authenticated,is_active,get_id,is_anonymous)
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))  # 全名
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))  # 头像hash值
    # 定义外键
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    # 关注了User表中的谁
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')
    # 被User表的谁关注了
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        """赋予角色，如果请求的邮件含有FLASKY_ADMIN，给管理员权限"""
        super().__init__(**kwargs)
        self.follow(self)  # 自己关注自己
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    def __repr__(self):
        return '<Role %r>' % self.username

    def generate_confirmation_token(self, expiration=3600):
        """给id加密生成token添加到验证地址上,用于邮箱验证"""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        '''验证email token是否等于user id'''

        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            if data.get('confirm') != self.id:
                return False

        self.confirmed = True
        db.session.add(self)
        return True

    def ping(self):
        """刷新用户登录时的时间"""
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    @property
    def password(self):
        '''如果直接读取密码报错，因为生成散列值后无法还原回原密码'''
        raise AttributeError('password is not readable attribute')

    @password.setter
    def password(self, password):
        """给密码加密"""
        self.password_hash = generate_password_hash(password)

    def valify_password(self, password):
        """解密数据库的password_pash并与password比较，返回Boolean"""
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expiration=3600):
        """重置密码前生成邮件token"""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        """重置密码"""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def change_email(self, token):
        """修改邮箱"""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        """判断是否管理员级别"""
        return self.can(Permission.ADMIN)

    def gravatar(self, size=100, default='identicon', rating='g'):
        """生成Gravatar URL"""
        # 如果是https请求
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        # 先查是否有hash值，没有则创建，减少频繁计算hash值
        hash = self.avatar_hash or self.gravatar_hash()
        # s图像尺寸像素，g图像级别，d默认图像
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def gravatar_hash(self):
        print('生成hash')
        hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        # self.avatar_hash = hash
        # db.session.add(self)
        # db.session.commit()
        return hash

    """以下4个为关注关系的辅助方法"""

    def follow(self, user):
        """如果user没有被关注，就关注它"""
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        """取消关注，使用followed 关系找到连接用户和被关注用户的Follow 实例。"""
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        """判断user关注了谁"""
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        """被谁关注"""
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        """只查询关注的人的文章
        select * from posts inner join follows
        on follows.followed_id=posts.author_id
        where follower_id=current_user.id
        """
        query = Post.query.join(Follow, Follow.followed_id == Post.author_id) \
            .filter(Follow.follower_id == self.id)
        print(str(query))
        return query

    @staticmethod
    def add_self_follows():
        """
        创建函数更新数据库这一技术经常用来更新已部署的应用
        如果用户没有自己关注自己，则关注，用于首页查看关注
        他人的文章时也显示自己的文章"""
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def generate_auth_token(self, expiration):
        """产生验证令牌,expiration为过期时间（秒）"""
        s = Serializer(current_app.config['SECRET_KEY'], expiration=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def varify_auth_token(token):
        """验证令牌"""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'followed_posts_url': url_for('api.get_user_followed_posts',
                                          id=self.id),
            'post_count': self.posts.count()
        }
        return json_user


class AnonymousUser(AnonymousUserMixin):
    """匿名用户无权限"""

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# 使用应用自定义的匿名用户类
login_manager.anonymous_user = AnonymousUser


# 装饰器把这个函数注册给Flask-Login，在这个扩展需要获取已
# 登录用户的信息时调用
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Role(db.Model):
    # 定义在数据库中使用的表名
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)  # 默认角色
    permissions = db.Column(db.Integer)
    # 定义多的一方对应的关系，backref表示在User新建一个属性role
    users = db.relationship('User', backref='role', lazy='dynamic')

    """非必须, 用于在调试或测试时, 返回一个具有可读性的字符串表示模型."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        # 默认User权限
        default_role = 'User'

        # 往数据库操作,只有当数据库中没有某个角色名时，才会创建新角色对象
        for i in roles:
            role = Role.query.filter_by(name=i).first()
            if role is None:
                role = Role(name=i)
            role.reset_permissions()
            for perm in roles[i]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
            db.session.commit()

    def add_permission(self, perm):
        """增加权限"""
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        """删除权限"""
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        """重设权限"""
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)  # 正文
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 時間戳
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        """将body 字段中的文本渲染成HTML格式"""
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']

        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        """把文章转换成JSON 格式的序列化字典"""
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comment_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        """从JSON 格式数据创建一篇博客文章"""
        print(json_post)
        body = json_post.get('body')
        print(body)
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)


class Comment(db.Model):
    """评论表 与文章，和用户多对一的关系"""
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)  # 协管员通过这个字段查禁不当评论
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        """将body 字段中的文本渲染成HTML格式"""
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


class Permission:
    FOLLOW = 1  # 关注用户
    COMMENT = 2  # 在他人的文章中发表评论
    WRITE = 4  # 写文章
    MODERATE = 8  # 管理他人发表的评论
    ADMIN = 16  # 管理员权限


# sqlalchemy "set"事件，监听Post.body
# 意味着只要body 字段设了新值，on_changed_body就会自动被调用
db.event.listen(Post.body, 'set', Post.on_changed_body)

db.event.listen(Comment.body, 'set', Comment.on_changed_body)
