from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, StopValidation, ValidationError
from ..models import User
import re


class LoginForm(FlaskForm):
    # 必填，最大长度，邮件类型，如出错按顺序弹出最初的错误
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email(message='不符合的邮箱格式')])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    """注册form"""
    email = StringField('邮箱', validators=[
        DataRequired(), Length(1, 64),
        Email()])
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(1, 64),
        # 以字母开头，而且只包含字母、数字、下划线和点号
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               '用户名必须含有字母，数字，.或下划线 ')])
    password = PasswordField('密码', validators=[
        DataRequired(), EqualTo('password2', message='密码必须匹配.')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    # 效验邮箱是否存在
    def validate_email(self, field):
        """如果表单类中定义了以validate_开头且后面跟着字段名的方法，这个方法
        就和常规的验证函数一起调用。validate_后面的字段就是数据库定义的字段。
        自定义的验证函数要想表示验证失败，可以抛出ValidationError 异常"""

        # <input id="email" name="email" required type="text" value="775838893@qq.com">
        # print(field)
        # 此时的field.data就是email字段
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已存在.')

    # 效验用户名是否存在
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在.')


class ChangePasswordForm(FlaskForm):
    """修改用户密码form"""
    old_password = PasswordField('原密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='密码必须匹配.')])
    password2 = PasswordField('确认密码',
                              validators=[DataRequired()])
    submit = SubmitField('提交')


class PasswordResetRequestForm(FlaskForm):
    """忘记密码form"""
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                          Email(message="邮箱格式不正确")])
    submit = SubmitField('提交')


class ChangeEmailForm(FlaskForm):
    """修改邮箱请求form"""
    email = StringField('新的邮箱地址', validators=[DataRequired(), Length(1, 64),
                                              Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('邮箱已存在。')


class PasswordResetForm(FlaskForm):
    """修改邮箱form"""
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='二次密码不一致！')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('提交')
