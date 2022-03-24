from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_1 = User.objects.create_user(username='auth_1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.PAGES_ADRESSES = (
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.pk}/',
            '/create/',
            f'/posts/{cls.post.pk}/edit/',
        )
        TEMPLATES = (
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        )
        cls.TEMPLATES_URL_NAMSE = {
            cls.PAGES_ADRESSES[i]: TEMPLATES[i] for i in range(len(TEMPLATES))
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user_1)

    def test_pages_anonymous_user(self):
        """Страницы доступны неавторизованному пользователю"""

        for url in self.PAGES_ADRESSES[0: 4]:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_pages_authorized_user(self):
        """Страницы доступны авторизованному пользователю,
        и страница для редоктировыния поста доступна автору поста"""

        for url in self.PAGES_ADRESSES:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблоны."""

        for address, template in self.TEMPLATES_URL_NAMSE.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_code_404_returns(self):
        """Cервер возвращает код 404, если страница не найдена."""

        response = self.guest_client.get('unexisting_page')
        self.assertEqual(response.status_code, 404)

    def test_url_redirect_anonymous(self):
        """Страницы /create/, /<post_id>/edit/
        перенаправляет анонимного пользователя."""

        url_redirect = [
            self.PAGES_ADRESSES[4],
            self.PAGES_ADRESSES[5],
        ]
        for url in url_redirect:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_url_redirect_authorized_client(self):
        """Страница  /<post_id>/edit/ перенаправляет
        авторизовонного пользователя, не автора поста."""

        response = self.authorized_client_1.get(self.PAGES_ADRESSES[5])
        self.assertEqual(response.status_code, 302)
