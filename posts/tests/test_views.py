import datetime as dt

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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
        Site.objects.create(
            domain='localhost:8000',
            name='localhost:8000'
        )
        FlatPage.objects.create(
            url="/about-author/",
            title="test_author",
            content="test",
        ).sites.add(Site.objects.first())
        FlatPage.objects.create(
            url="/about-spec/",
            title="test_spec",
            content="test",
        ).sites.add(Site.objects.first())
        cls.post = Post.objects.first()
        cls.user = user

    def setUp(self) -> None:
        user = ViewsTest.user
        self.user = user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            "index.html": reverse("index"),
            "group.html": reverse("group", kwargs={"slug": "mafia-town"}),
            "new.html": reverse("new_post"),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def post_context_is_correct(self, url, context_field, kwargs):
        post = Post.objects.first()
        response = self.authorized_client.get(reverse(url, kwargs=kwargs))
        post_text = response.context.get(context_field)[0].text
        post_date = response.context.get(context_field)[0].pub_date
        post_author = response.context.get(context_field)[0].author
        post_group = response.context.get(context_field)[0].group.title
        self.assertEqual(post_text, "test")
        self.assertEqual(post_date, post.pub_date)
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_group, "Peck")
        return response

    def test_index_page_show_correct_context(self):
        self.post_context_is_correct("index", "page", {})

    def test_group_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            "group", kwargs={"slug": "mafia-town"}
            ))
        group_title = response.context.get("page")[0].group.title
        group_slug = response.context.get("page")[0].group.slug
        group_description = response.context.get(
            "page"
            )[0].group.description
        self.assertEqual(group_title, "Peck")
        self.assertEqual(group_slug, "mafia-town")
        self.assertEqual(group_description, "Revoluton")

    def test_new_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse("new_post"))
        form_fields = {
            "group": forms.fields.ChoiceField,
            "text": forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            "post_edit", kwargs={"username": "test", "post_id": 1}
            ))
        form_fields = {
            "group": forms.fields.ChoiceField,
            "text": forms.fields.CharField
        }
        post = response.context.get("post").id
        self.assertEqual(post, 1)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_profile_page_show_correct_context(self):
        response = self.post_context_is_correct(
            "profile",
            "page",
            {"username": "test"}
        )
        user_request = response.context.get("user").username
        user_profile = response.context.get("user_profile").username
        paginator = len(response.context.get("paginator").object_list)
        self.assertEqual(user_request, "test")
        self.assertEqual(user_profile, self.user.username)
        self.assertEqual(paginator, 1)

    def test_post_page_show_correct_context(self):
        # Часть кода похожа на код в index и profile,
        # но он различается количеством постов, сюда передается только один
        # поэтому я не могу использовать его повторно
        post = ViewsTest.post
        response = self.authorized_client.get(reverse(
            "post", kwargs={"username": "test", "post_id": 1}
            ))
        post_text = response.context.get("post").text
        post_date = response.context.get("post").pub_date
        post_author = response.context.get("post").author
        post_group = response.context.get("post").group.title
        user_request = response.context.get("user").username
        post_id = response.context.get("post_id")
        post_count = response.context.get("post_count")
        user_profile = response.context.get("user_profile").username
        self.assertEqual(post_text, "test")
        self.assertEqual(post_date, post.pub_date)
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_group, "Peck")
        self.assertEqual(user_request, "test")
        self.assertEqual(post_id, 1)
        self.assertEqual(post_count, 1)
        self.assertEqual(user_profile, self.user.username)

    def test_flatpages_show_correct_context(self):
        flatpages = {
            "author": "test_author",
            "spec": "test_spec",
        }
        for reversed_name, expected in flatpages.items():
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_client.get(reverse(reversed_name))
                flatpage = response.context.get("flatpage").title
                self.assertEqual(flatpage, expected)

    def test_new_post_appears_right(self):
        Group.objects.create(
            title="test",
            slug="test-slug",
            description="test"
        )
        Post.objects.create(
            text="test2",
            pub_date=dt.date.today(),
            author=get_user_model().objects.get(id=1),
            group=Group.objects.get(id=2)
        )
        response_index = self.authorized_client.get(reverse("index"))
        post_text_0 = response_index.context.get("page")[0].text
        self.assertEqual(post_text_0, "test2")
        groups_name = {
            "mafia-town": "test",
            "test-slug": "test2"
        }
        for value, expected in groups_name.items():
            with self.subTest(value=value):
                response_group = self.authorized_client.get(reverse(
                    "group", kwargs={"slug": value}
                    ))
                post_text_0 = response_group.context.get("page")[0].text
                self.assertEqual(post_text_0, expected)
