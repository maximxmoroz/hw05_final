from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from posts.models import Post, Group
from http import HTTPStatus
from django.core.cache import cache
from django.urls import reverse

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='test_author')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.another_user = User.objects.create_user(username='another_user')
        cls.another_client = Client()
        cls.another_client.force_login(cls.another_user)

        cls.group = Group.objects.create(
            title='test_group_title',
            slug='test_group_slug',
            description='test_group_descrioption'
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.author
        )

        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        for adress, template in PostURLTests.templates_url_names.items():
            with self.subTest(adress=adress):
                response = PostURLTests.authorized_author.get(
                    adress
                )
                self.assertTemplateUsed(response, template)

    def test_urls(self):
        """Проверка работы страниц"""
        for adress in self.templates_url_names:
            with self.subTest(adress=adress):
                response = PostURLTests.authorized_author.get(
                    adress, follow=True
                )
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_redirect_if_not_logged_in(self):
        """Адрес "/create" перенаправляет
        неавторизованного пользователя"""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(response, '/accounts/login/')

    def test_authorized_client(self):
        """Проверка авторизованного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_unexisting_page_404(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_post_redirect_guest(self):
        '''Проверка создания поста для неавторизованного юзера'''
        response = self.guest_client.get(
            reverse('posts:post_create'),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/create/'
        )

    # Проверяем редирект для не-автора
    def test_post_edit_redirect_not_author(self):
        '''Проверка, что для не автора при попытке
         редактировании поста будет редирект на пост'''
        post_id = PostURLTests.post.pk
        response = self.another_client.get(
            reverse('posts:post_edit', args=[post_id]),
            follow=True
        )
        self.assertRedirects(
            response, (reverse('posts:post_detail', args=[post_id]))
        )
