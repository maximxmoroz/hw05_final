import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from posts.models import Post, Group
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.author = User.objects.create_user(username='test_author')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

        cls.group = Group.objects.create(
           title='test_group_title',
            slug='test_group_slug',
            description='test_group_description',
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.author,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        text = 'Test post'
        form_data = {
            'text': text,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        posts_by_id = Post.objects.order_by('-id')
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(posts_by_id[0].text, text) 

    def test_edit_post(self):
        form_data = {
            'post_id': self.post.id,
            'text': 'editted_text',
            'group': self.group.id,
            'author': self.author,
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.id])
        )
        edit_post = Post.objects.latest('id')
        self.assertEqual(edit_post.text, 'editted_text')
        self.assertEqual(edit_post.author, self.author)
        self.assertEqual(edit_post.group, self.group) 

    def test_anonymous_edit_post(self):
        text = self.post.text
        form_data = {
            'text': 'I cant create and edit posts',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response,
            reverse('users:login') + f'?next=/posts/{self.post.id}/edit/'
        )
        self.assertEqual(post.text, text)

    def test_anonymous_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'I cant create and edit posts',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/create/'
        )
        self.assertEqual(post_count, Post.objects.count())


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestImageUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
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
        text = 'test post with image'
        Post.objects.create(
            text=text,
            author=self.user,
            image=uploaded,
        )
        posts_by_id = Post.objects.order_by('-id')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(posts_by_id[0].text, text)
        self.assertEqual(posts_by_id[0].author, self.user)
        self.assertEqual(posts_by_id[0].image, f'posts/{uploaded.name}')
