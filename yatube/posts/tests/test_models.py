from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
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
            text='Тестовый текст',
        )

    def test_models_have_correct_object_names_group(self):
        """Проверяем корректную работу __str__ в модели Group."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_models_have_correct_object_names_post(self):
        """Проверяем корректную работу __str__ в модели Post."""
        post = PostModelTest.post
        expected_object_name_text = post.text[:15]
        self.assertEqual(expected_object_name_text, str(post))

        expected_object_name_author = post.author.username
        self.assertEqual(expected_object_name_author, self.user.username)

        expected_object_name_pub_date = post.pub_date
        self.assertEqual(expected_object_name_pub_date, post.pub_date)
