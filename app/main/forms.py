from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, Email, ValidationError
from ..models import Role, User


# flaskr-wtf
class MyForm(FlaskForm):
    # 定义个input type=text字段并且验证数据要求不为空
    name = StringField('name', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    """资料编辑表单"""
    name = StringField('全名', validators=[Length(1, 64)])
    location = StringField('位置', validators=[Length(1, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')


class EditProfileAdminForm(FlaskForm):
    """管理员资料编辑表单"""
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                          Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名必须含有字母，数字，.或者下划线')])
    confirmed = BooleanField('确认')
    role = SelectField('角色', coerce=int)  # coerce把字段的id值转换为整数
    name = StringField('全名', validators=[Length(0, 64)])
    location = StringField('位置', validators=[Length(0, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # choice是元组构成的列表
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        """管理员编辑时验证邮箱"""
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册.')

    def validate_username(self, field):
        """管理员编辑时验证用户名"""
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用.')


class PostForm(FlaskForm):
    """博客文章表单"""
    body = PageDownField("此时的想法?", validators=[DataRequired()])
    submit = SubmitField('提交')


class CommentForm(FlaskForm):
    """评论输入表单"""
    body = StringField('输入评论', validators=[DataRequired()])
    submit = SubmitField('提交')
