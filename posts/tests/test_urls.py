import datetime as dt

from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase

from posts.models import Group, Post


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        get_user_model().objects.create(username="test")
        get_user_model().objects.create(username="test2")
        Group.objects.create(
            title="Peck",
            slug="mafia-town",
            description="Revoluton"
        )
        Post.objects.create(
            text="test",
            pub_date=dt.date.today(),
            author=get_user_model().objects.get(id=1),
            group=Group.objects.get(id=1)
        )
        Site.objects.create(
            domain='localhost:8000',
            name='localhost:8000'
        )
        FlatPage.objects.create(
            url="/about-author/",
            title="test_author",
        ).sites.add(Site.objects.get(id=1))
        FlatPage.objects.create(
            url="/about-spec/",
            title="test_spec",
        ).sites.add(Site.objects.get(id=1))

    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = get_user_model().objects.get(id=1)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_exists(self):
        page_exists = [
            "/",
            "/group/mafia-town/",
            "/test/",
            "/test/1/",
            "/about-author/",
            "/about-spec/"
        ]
        for page in page_exists:
            with self.subTest():
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_authorized(self):
        page_auth = [
            "/new/",
            "/test/1/edit/",
        ]
        for page in page_auth:
            with self.subTest():
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_redirect_anonymus(self):
        page_auth = {
            "/new/": "/auth/login/?next=/new/",
            "/test/1/edit/": "/auth/login/?next=/test/1/edit/",
        }
        for page, expected in page_auth.items():
            with self.subTest(expected=expected):
                response = self.guest_client.get(page, follow=True)
                self.assertRedirects(response, expected)

    def test_redirect_authorized(self):
        self.user = get_user_model().objects.get(id=2)
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get("/test/1/edit/", follow=True)
        self.assertRedirects(response, "/test/1/")

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            "/": "index.html",
            "/group/mafia-town/": "group.html",
            "/new/": "new.html",
            "/test/1/edit/": "new.html",
        }
        for url, template in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
