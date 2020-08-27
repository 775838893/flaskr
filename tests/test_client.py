import unittest
import re
from app import create_app, db
from app.models import User, Role

"""使用Flask 测试客户端模拟新用户注册的整个流程"""


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)  # flask测试客户端对象

    def tearDown(self):
        db.session.remove()
        # db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        """测试首页"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Stranger' in response.get_data(as_text=True))

    # @unittest.expectedFailure
    # 把测试标记为预计失败。如果测试不通过，会被认为测试成功；如果测试通过了，则被认为是测试失败。
    def test_register_and_login(self):
        """测试用户注册和登录"""

        # 注册
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertEqual(response.status_code, 302)

        # 使用新注册的账户登录
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat'
        }, follow_redirects=True)  # 自动向重定向的URL 发起GET 请求
        self.assertTrue(re.search('Hello,\s+john!',
                                  response.get_data(as_text=True)))
        self.assertIn('You have not confirmed your account yet',
                      response.get_data(as_text=True))

        # 发送确认令牌
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token),
                                   follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertIn('你已认证', response.get_data(as_text=True))

        # 退出
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('你已登出', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
