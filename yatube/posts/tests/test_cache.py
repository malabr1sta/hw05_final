from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class TestCacheIndex(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='text',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index_page(self):
        """Проверка работы кэша на главной странице"""

        response_1 = self.guest_client.get(reverse('posts:index'))
        Post.objects.create(author=self.user, text='text_1')
        response_2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_2 = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_2.content)
