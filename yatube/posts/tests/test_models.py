from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    CHARACTERS = 15
    FIELD_VERBOSES = {
        'text': 'Текст поста',
        'pub_date': 'Дата публикации',
        'author': 'Автор',
        'group': 'Группа',
    }
    FIELD_HELP_TEXTS = {
        'text': 'Введите текст поста',
        'group': 'Группа, к которой будет относиться пост',
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_post = post.text[:self.CHARACTERS]
        self.assertEquals(expected_object_post, str(post))
        expected_object_group = group.title
        self.assertEquals(expected_object_group, str(group))

    def test_verbose_name(self):
        post = PostModelTest.post
        for field, expected_value in self.FIELD_VERBOSES.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        post = PostModelTest.post
        for field, expected_value in self.FIELD_HELP_TEXTS.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
