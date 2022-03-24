from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Post

User = get_user_model()


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username='auth')
        cls.user_2 = User.objects.create(username='ben')
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user_1
        )
        cls.follow_index = ('posts:follow_index')
        cls.follow = (
            'posts:profile_follow',
            {'username': cls.user_1.username}
        )
        cls.unfollow = (
            'posts:profile_unfollow',
            {'username': cls.user_1.username}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)

    def test_user_follow(self):
        """Авторизованный пользователь может
        подписываться на других пользователей"""

        url, args = self.follow
        self.authorized_client.get(reverse(url, kwargs=args))
        user_follow = Follow.objects.filter(
            user=self.user_2,
            author=self.user_1
        )
        self.assertTrue(user_follow.exists())

    def test_user_unfollow(self):
        """Авторизованный пользователь может
        отписываться от других пользователей"""

        url, args = self.unfollow
        Follow.objects.create(
            user=self.user_2,
            author=self.user_1
        )
        self.authorized_client.get(reverse(url, kwargs=args))
        user_unfollow = Follow.objects.filter(
            user=self.user_2,
            author=self.user_1
        )
        self.assertFalse(user_unfollow.exists())

    def test_follow_in_pages_users(self):
        """Новая запись пользователя появляется в
        ленте тех, кто на него подписан"""

        expected_post = self.post
        url, args = self.follow
        self.authorized_client.get(reverse(url, kwargs=args))
        response = self.authorized_client.get(reverse(self.follow_index))
        self.assertContains(response, expected_post)

    def test_follow_not_in_pages_users(self):
        """Новая запись пользователя не появляется в
        ленте тех, кто на него не подписан"""

        user_3 = User.objects.create(username='user')
        self.client_user_3 = Client()
        self.client_user_3.force_login(user_3)
        expected_post = self.post
        response = self.client_user_3.get(reverse(self.follow_index))
        self.assertNotContains(response, expected_post)
