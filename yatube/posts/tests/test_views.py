import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username='ben')
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.index_page = (
            'posts:index',
            None,
            'posts/index.html',
        )
        cls.group_page = (
            'posts:group_list',
            {'slug': cls.group.slug},
            'posts/group_list.html',
        )
        cls.profile_page = (
            'posts:profile',
            {'username': cls.user.username},
            'posts/profile.html',
        )
        cls.detail_page = (
            'posts:post_detail',
            {'post_id': cls.post.pk},
            'posts/post_detail.html',
        )
        cls.create_page = (
            'posts:post_create',
            None,
            'posts/create_post.html',
        )
        cls.edit_page = (
            'posts:post_edit',
            {'post_id': cls.post.pk},
            'posts/create_post.html',
        )
        cls.add_comment = (
            'posts:add_comment',
            {'post_id': cls.post.pk},
            'posts/post_detail.html',
        )
        cls.follow_index = ('posts:follow_index')
        cls.follow = (
            'posts:profile_follow',
            {'username': cls.user.username}
        )
        cls.unfollow = (
            'posts:profile_unfollow',
            {'username': cls.user.username}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client = Client()
        self.client.force_login(self.user_1)

    def method_test_context(self, expected, actual, reverse_name):
        response = self.authorized_client.get(reverse_name)
        if actual == 'page_obj':
            actual_post = response.context[actual][0]
        else:
            actual_post = response.context[actual]
        self.assertEqual(actual_post, expected)

    def method_test_page_list(self, list_pages, pages):
        for page in pages:
            url, args, _ = page
            reverse_name = reverse(url, kwargs=args)
            list_pages.append(reverse_name)
        return list_pages

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        pages = (
            self.index_page,
            self.group_page,
            self.profile_page,
            self.detail_page,
            self.create_page,
            self.edit_page,
        )
        for url, args, html in pages:
            with self.subTest(reverse_name=reverse(url, kwargs=args)):
                response = self.authorized_client.get(
                    reverse(url, kwargs=args)
                )
                self.assertTemplateUsed(response, html)

    def test_index_profile_show_correct_context(self):
        """Шаблоны index, profile, detail
        сформированы с правильным контекстом."""

        pages = (self.index_page, self.profile_page, self.detail_page)
        context = ('page_obj', 'page_obj', 'post')
        pages_addresses_context = {}
        for i in range(len(pages)):
            url, args, _ = pages[i]
            pages_addresses_context[reverse(url, kwargs=args)] = context[i]
        for reverse_name, context in pages_addresses_context.items():
            with self.subTest(reverse_name=reverse_name):
                self.method_test_context(self.post, context, reverse_name)

    def test_page_group_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        url, args, _ = self.group_page
        reverse_name = reverse(url, kwargs=args)
        self.method_test_context(self.group, 'group', reverse_name)

    def test_page_post_create_edit_show_correct_context(self):
        """Шаблоны create, edit сформированы с правильным контекстом."""

        pages = (self.create_page, self.edit_page)
        pages_addresses = []
        self.method_test_page_list(pages_addresses, pages)
        form_fields = {
            'group': forms.ChoiceField,
            'text': forms.CharField,
            'image': forms.ImageField,
        }
        for reverse_name in pages_addresses:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    response = self.authorized_client.get(reverse_name)
                    actual = response.context.get('form').fields.get(value)
                    self.assertIsInstance(actual, expected)

    def test_post_apper_in_pages(self):
        """Пост появился на главной странице,
        на странице выбранной группы, в профайле пользователя"""

        expected_post = self.post
        pages = (self.index_page, self.group_page, self.profile_page,)
        pages_addresses = []
        self.method_test_page_list(pages_addresses, pages)
        for reverse_name in pages_addresses:
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertContains(response, expected_post)

    def test_post_not_in_other_group(self):
        """Пост не попал в группу, для которой не был предназначен"""

        post = self.post
        self.group1 = Group.objects.create(
            title='Тестовое описание второе',
            slug='test-slug_2',
            description='Тестовое описание второе',
        )
        url, _, _ = self.group_page
        revers_name = reverse(url, kwargs={'slug': self.group1.slug})
        response = self.authorized_client.get(revers_name)
        self.assertNotContains(response, post)

    def test_pages_paginator(self):
        """Paginator test"""

        posts = []
        for i in range(1, 13):
            posts.append(Post(
                author=self.user,
                text=f'Тестовый пост_{i}',
                group=self.group,
            ))
        Post.objects.bulk_create(posts, 13)
        pages = (self.index_page, self.group_page, self.profile_page)
        pages_addresses = []
        self.method_test_page_list(pages_addresses, pages)
        for reverse_name in pages_addresses:
            page_list = {reverse_name: 10, reverse_name + '?page=2': 3}
            for page, number_post in page_list.items():
                with self.subTest(reverse_name=reverse_name):
                    response = self.client.get(page)
                    self.assertEqual(len(
                        response.context['page_obj']),
                        number_post
                    )

    def test_authorized_client_comment(self):
        """Авторизированный пользователь может
        остовлять комментарий под постом."""

        url, args, _ = self.add_comment
        response = self.authorized_client.post(
            reverse(url, kwargs=args),
            data={'text': 'комментарий'},
        )
        comment_creat = Comment.objects.filter(
            post=self.post
        )
        self.assertTrue(comment_creat.exists())
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(comment.text, 'комментарий')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_guest_client_comment(self):
        """Неавторизированный пользователь не может
        остовлять комментарий под постом"""

        url, args, _ = self.add_comment
        count_comments = Comment.objects.count()
        self.guest_client.post(
            reverse(url, kwargs=args),
            data={'text': 'комментарий'}
        )
        self.assertEqual(count_comments, Comment.objects.count())

    def test_comment_in_post_detail(self):
        """Комментарий появляется на странице поста"""

        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='комментарий'
        )
        url, args, _ = self.detail_page
        response = self.authorized_client.get(
            reverse(url, kwargs=args),
        )
        self.assertContains(response, comment.text)
        self.assertContains(response, comment.author)

    def test_user_follow(self):
        """Авторизованный пользователь может
        подписываться на других пользователей"""

        url, args = self.follow
        self.client.get(reverse(url, kwargs=args))
        user_follow = Follow.objects.filter(
            user=self.user_1,
            author=self.user
        )
        self.assertTrue(user_follow.exists())

    def test_user_unfollow(self):
        """Авторизованный пользователь может
        отписываться от других пользователей"""

        url, args = self.unfollow
        Follow.objects.create(
            user=self.user_1,
            author=self.user
        )
        self.client.get(reverse(url, kwargs=args))
        user_unfollow = Follow.objects.filter(
            user=self.user_1,
            author=self.user
        )
        self.assertFalse(user_unfollow.exists())

    def test_follow_in_pages_users(self):
        """Новая запись пользователя появляется в
        ленте тех, кто на него подписан"""

        expected_post = self.post
        url, args = self.follow
        self.client.get(reverse(url, kwargs=args))
        response = self.client.get(reverse(self.follow_index))
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

    def test_cache_index_page(self):
        """Проверка работы кэша на главной странице"""

        url, _, _ = self.index_page
        response_1 = self.guest_client.get(reverse(url))
        Post.objects.create(author=self.user, text='text_1')
        response_2 = self.guest_client.get(reverse(url))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_2 = self.guest_client.get(reverse(url))
        self.assertNotEqual(response_1.content, response_2.content)
