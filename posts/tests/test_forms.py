import datetime as dt

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = get_user_model().objects.create(username="test")
        Group.objects.create(
            title="Peck",
            slug="mafia-town",
            description="Revoluton"
        )
        Post.objects.create(
            text="test",
            pub_date=dt.date.today(),
            author=user,
            group=Group.objects.first()
        )
        cls.group = Group.objects.first()
        cls.post = Post.objects.first()
        cls.user = user

    def setUp(self):
        user = PostCreateFormTests.user
        self.user = user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        group = PostCreateFormTests.group
        posts_count = Post.objects.count()
        form_data = {
            "group": group.id,
            "text": "test"
        }
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        group = PostCreateFormTests.group
        form_data = {
            "group": group.id,
            "text": "test_edit"
        }
        response = self.authorized_client.post(
            reverse("post_edit", kwargs={"username": "test", "post_id": 1}),
            data=form_data,
        )
        self.assertRedirects(response, reverse("post", kwargs={
            "username": "test",
            "post_id": 1
        }))
        self.assertEqual(Post.objects.first().text, "test_edit")
