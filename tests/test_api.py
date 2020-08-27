import unittest
import json
from flask import url_for
from base64 import b64encode
from app import create_app, db
from app.models import Role, User


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        # db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization':
                'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def test_no_auth(self):
        """如果请求没有提供验证，则返回401"""
        response = self.client.get(url_for('/api/v1/posts/'),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401),

    def test_posts(self):
        """测试提交和请求post文章"""

        # 创建用户
        # r = Role.query.filter_by(name="User").first()
        # self.assertIsNotNone(r)
        # u = User(email='john@example.com', password='cat', confirmed=True,
        #          role=r)
        # db.session.add(u)
        # db.session.commit()

        # 写一篇文章
        response = self.client.post(
            '/api/v1/posts/',
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({'body': 'body of the *blog* post'}))
        print(response.status_code)
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # 获取刚发布的文章
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], 'body of the *blog* post')
        self.assertEqual(json_response['body_html'],
                         '<p>body of the <em>blog</em> post</p>')


if __name__ == '__main__':
    unittest.main()
