import re
import threading
import time
import unittest
from selenium import webdriver
from app import create_app, db, fake
from app.models import Role, User, Post


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        """在运行单个类中的测试之前调用，必须被修饰为classmothod"""
        # 启动谷歌浏览器
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        try:
            cls.client = webdriver.Chrome(options=options)
            # cls.client = webdriver.Chrome()
        except:
            pass

        # 如果无法启动浏览器，跳过这些测试
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # 禁止日志，保持输出简洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # # 创建数据库，并使用一些虚拟数据填充
            # db.create_all()
            # Role.insert_roles()
            # fake.users(5)
            # fake.posts(5)
            #
            # # 添加管理员
            # admin_role = Role.query.filter_by(name='Administrator').first()
            # admin = User(email='john1@example.com',
            #              username='john1', password='cat',
            #              role=admin_role, confirmed=True)
            # db.session.add(admin)
            # db.session.commit()

            # 在一个线程中启动Flask服务器
            cls.server_thread = threading.Thread(target=cls.app.run,
                                                 kwargs={'debug': False})
            cls.server_thread.start()

            # give the server a second to ensure it is up
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # 关闭Flask服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # 删除数据库
            # db.drop_all()
            db.session.remove()

            # 删除应用上下文
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            # 跳出整个test
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        # 进入首页
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Hello,\s+Stranger!',
                                  self.client.page_source))

        # 模拟点击进入登录页面
        self.client.find_element_by_link_text('登录').click()
        self.assertIn('<h1>Login</h1>', self.client.page_source)

        # 登录
        self.client.find_element_by_name('email').send_keys('john1@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('Hello,\s+john1!', self.client.page_source))

        # 进入用户资料页面
        self.client.find_element_by_link_text('简介').click()
        self.assertIn('<h1>john1</h1>', self.client.page_source)


if __name__ == '__main__':
    unittest.main()
