import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your_email_address')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'igjhjhmrsaqnbfbe')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <your_email_address>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    FLASKY_POSTS_PER_PAGE = 10  # 分页显示的条数
    FLASKY_FOLLOWERS_PER_PAGE = 10  # 关注者分页显示条数
    FLASKY_COMMENTS_PER_PAGE = 10  # 评论分页显示条数
    FLASKY_SLOW_DB_QUERY_TIME = 0.5  # 慢查询阈值
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True  # 告诉Flask-SQLAlchemy 启用记录查询统计数据的功


@staticmethod
def init_app(app):
    pass


class DevelopmentConfig(Config):
    '''开发环境'''
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              r'mysql+mysqlconnector://root@127.0.0.1/flaskdemo'


class TestingConfig(Config):
    '''测试环境'''
    TESTING = True
    WTF_CSRF_ENABLED = False  # 禁用csrf
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              r'mysql+mysqlconnector://root@127.0.0.1/flaskdemo'


class ProductionConfig(Config):
    '''生产环境'''
    # mysql: // username: password @ hostname / database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              r'mysql+mysqlconnector://root@127.0.0.1/flaskdemo'

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # 出错时邮件通知管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class DockerConfig(ProductionConfig):
    """docker 配置"""

    @staticmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # 把日志输出到stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}
