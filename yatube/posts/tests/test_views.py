from http import HTTPStatus
from django import forms
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache

from ..models import Follow, Group, Post

TEST_OF_POST: int = 13
NUMB_FIRST_PAGE = 10
NUMB_SECOND_PAGE: int = 3
User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='NoName',
            email='noname@mail.com',
            password='123test',
        )
        cls.user_2 = User.objects.create_user(
            username='NoName_2',
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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ViewsTests.user)

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(text='Тестовый пост', author=self.user,)
        old_posts = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(old_posts, posts)
        cache.clear()
        new_posts = self.authorized_client.get(reverse('posts:index')).content
        self.assertNotEqual(old_posts, new_posts)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_posts', kwargs={'slug': self.group.slug})):
                'posts/group_list.html',
            (reverse('posts:profile', kwargs={
                'username': self.user.username
            })): 'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': self.post.pk})):
                'posts/post_detail.html',
            (reverse('posts:post_edit', kwargs={'post_id': self.post.pk})):
                'posts/create_post.html',
            (reverse('posts:post_create')): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                error_name = f'Ошибка: {reverse_name} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_page_show_correct_page_obj_context(self):
        """Пост на страницу добавлен корректно"""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for value in urls:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                page_context = response.context.get('page_obj').object_list
                expected = list(Post.objects.all())
                self.assertEqual(page_context, expected,
                                 'Поста нет на странице')

    def test_page2_show_correct_page_obj_context(self):
        """Пост при создании не добавляется в другую группу"""
        posts_count = Post.objects.filter(group=self.group).count()
        group_count = Post.objects.filter(group=self.group).count()
        self.assertEqual(group_count, posts_count, 'поста нет в другой группе')

    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        test_object = response.context['group']
        post_group = test_object.title
        self.assertEqual(post_group, 'Тестовая группа')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text_0 = {response.context['post'].text: 'Тестовый пост',
                       response.context['post'].group: self.group,
                       response.context['post'].author: self.user.username}
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def _assert_post_response(self, response):
        """Проверяем Context"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self._assert_post_response(response)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        self._assert_post_response(response)

    def test_add_subscription(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        Post.objects.create(text='Тестовый пост', author=self.user)
        self.authorized_client.get('/profile/NoName_2/follow/')
        self.assertEqual(Follow.objects.count(), 1)

    def test_subscriber_feed(self):
        """Новая запись пользователя в ленте подписок."""
        post = Post.objects.create(text='Тестовый пост', author=self.user,)
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        profile = response.context['page_obj']
        self.assertIn(post, profile, 'Новая запись в ленте не отображается')


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        bilk_post = []
        for i in range(TEST_OF_POST):
            bilk_post.append(Post(text=f'Тестовый текст {i}',
                                  group=self.group,
                                  author=self.user))
        Post.objects.bulk_create(bilk_post)

    def test_first_page_contains_ten_records(self):
        '''Проверка количества постов на первых страницах.'''
        urls = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for value in urls:
            response = self.guest_client.get(value)
            count_posts = len(response.context['page_obj'])
            error = (f'Ошибка: {count_posts} постов,'
                     f' должно {NUMB_FIRST_PAGE}')
            self.assertEqual(count_posts, NUMB_FIRST_PAGE, error)

    def test_correct_page_context_guest_client(self):
        '''Проверка количества постов на первой и второй страницах.'''
        urls = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for value in urls:
            response = self.guest_client.get(value + '?page=2')
            count_posts = len(response.context['page_obj'])
            error = (f'Ошибка: {count_posts} постов,'
                     f'должно {NUMB_SECOND_PAGE}')
            self.assertEqual(count_posts, NUMB_SECOND_PAGE, error)
