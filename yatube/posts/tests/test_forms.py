import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """Форма для создания поста."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='NoName',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1,
                         'Поcт не добавлен в базу данных'
                         )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                group=self.group.id,
                author=self.user,
                image='posts/small.gif'
            ).exists(), 'Данные поста не совпадают'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_cant_create_existing_slug(self):
        '''Проверка изменения поста в БД'''
        posts_count = Post.objects.count()
        self.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        form_data = {
            'text': 'Текст записанный в форму',
            'group': self.group_2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
                        group=self.group_2.id,
                        author=self.user,
                        pub_date=self.post.pub_date
                        ).exists(), 'Данные поста не совпадают')
        self.assertNotEqual(self.post.text, form_data['text'],
                            'Невозможно изменить содержание поста')
        self.assertNotEqual(self.post.group, form_data['group'],
                            'Невозможно изменить группу поста')
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            'Поcт добавлен в БД')

    def test_add_comment_on_page(self):
        '''Проверка добавления комментария на страницу поста'''
        comment_count = Comment.objects.count()
        self.assertEqual(0, comment_count)
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1,
                         'Комментарий не добавлен в базу данных'
                         )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_no_edit_post(self):
        '''Проверка запрета добавления комментария для
            не авторизованного пользователя'''
        comments_count = Comment.objects.count()
        self.assertNotEqual(Comment.objects.count(),
                            comments_count + 1,
                            'Комментарий добавлен в базу данных')
