import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreatFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
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
        cls.form = PostForm()
        cls.reverse_name = (
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk},
            )
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает пост."""

        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый пост_1',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.reverse_name[0],
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), (posts_count + 1))
        post_create = Post.objects.filter(
            text='Тестовый пост_1',
            group=self.group.pk,
            image='posts/small.gif',
        )
        self.assertTrue(post_create.exists())
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(
            group=self.group.pk,
            text='Тестовый пост_1',
        )
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')

    def test_post_edit(self):
        """Валидная форма редактирует пост"""

        post_count = Post.objects.count()
        form_data = {
            'group': self.group.pk,
            'text': 'редактируемый пост',
        }
        self.authorized_client.post(
            self.reverse_name[1],
            date=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count)
        post_is_edit = Post.objects.filter(pk=self.post.pk)
        self.assertTrue(post_is_edit.exists())
        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.pk, form_data['group'])
