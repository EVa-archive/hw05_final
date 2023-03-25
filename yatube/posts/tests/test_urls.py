from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostUrlTest.user)

    def test_page_ctatus_code_authorized_client(self):
        templates_url_names = {
            '/': HTTPStatus.OK,
            f'/group/{PostUrlTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostUrlTest.user.username}/': HTTPStatus.OK,
            f'/posts/{PostUrlTest.post.id}/': HTTPStatus.OK,
            f'/posts/{PostUrlTest.post.id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, template)

    def test_page_ctatus_code_guest_client(self):
        templates_url_names = {
            '/': HTTPStatus.OK,
            f'/group/{PostUrlTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostUrlTest.user.username}/': HTTPStatus.OK,
            f'/posts/{PostUrlTest.post.id}/': HTTPStatus.OK,
            f'/posts/{PostUrlTest.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, template)

    def test_url_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        templates_url_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        ]
        for url in templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_exists_at_desired_location(self):
        """Страница /edit/ доступна автору поста."""
        if self.user == self.post.author:
            response = self.authorized_client.get(
                f'/posts/{self.post.id}/edit/')
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostUrlTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostUrlTest.user.username}/': 'posts/profile.html',
            f'/posts/{PostUrlTest.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostUrlTest.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_unixisting_page_dont_exists(self):
        """Страница /unexisting_page/ не существует."""
        user_client = [
            'guest_client'
            'authorized_client'
        ]
        for client in user_client:
            with self.subTest(client=client):
                response = self.client.get('/unexisting_page/')
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # Проверяем редиректы для неавторизованного пользователя
    def test_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница /edit/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{PostUrlTest.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostUrlTest.post.id}/edit/')

    def test_comment_url_redirect_anonymous_on_admin_login(self):
        """При добавлении комментария анонимный пользователь
        будет перенаправлен на страницу логина.
        """
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.guest_client.post(
            f'/posts/{PostUrlTest.post.id}/edit/',
            data=form_data,
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')


class StaticUrlTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
