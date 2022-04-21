import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from posts.models import Post, Group
from django.contrib.auth import get_user_model
from django.urls import reverse
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.guest_client = Client()

        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

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
        cls.form_data = {
            'text': cls.post.text,
            'group': cls.group.id,
            }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

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
            content_type='image/gif'
        )
        form_data = {
            'text': 'new_text',
            'group': self.group.id,
            'username': self.author.username,
            'image': uploaded
        }

        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )        
        self.assertRedirects(
            response, reverse('posts:profile', args=[self.author])
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post_last[0].text, form_data['text'])  

        self.assertTrue(
            Post.objects.filter(
                group=self.group, 
                text='new_text',
                author=self.author,
                ).exists()
        )

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

    def test_anonim_client_create_post(self):
        post_count = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_create'),
            data=PostFormsTests.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response,
                             reverse('users:login') + '?next=' + reverse(
                                 'posts:post_create'))
        self.assertEqual(Post.objects.count(), post_count)
