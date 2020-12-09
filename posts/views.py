from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .settings import PAGINATOR_PAGE_SIZE


def index(request):
    post_list = Post.objects.select_related("group").order_by("-pub_date")
    paginator = Paginator(post_list, PAGINATOR_PAGE_SIZE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "index.html", {
        "page": page,
        "paginator": paginator
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related("group").order_by("-pub_date")
    paginator = Paginator(post_list, PAGINATOR_PAGE_SIZE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "group.html", {
        "group": group,
        "page": page,
        "paginator": paginator
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_form = form.save(commit=False)
        new_form.author = request.user
        new_form.save()
        return redirect("index")
    form = PostForm()
    return render(request, "new.html", {"form": form})


def profile(request, username):
    user_profile = User.objects.get(username=username)
    post_list = Post.objects.filter(
        author=user_profile
    ).select_related("group").order_by("-pub_date")
    paginator = Paginator(post_list, PAGINATOR_PAGE_SIZE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    user = request.user
    return render(request, "profile.html", {
        "page": page,
        "user": user,
        "user_profile": user_profile,
        "paginator": paginator
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author.username != username:
        return redirect("post", username=post.author.username, post_id=post_id)
    user_profile = User.objects.get(username=username)
    post_count = Post.objects.filter(
        author=user_profile
    ).select_related("group").count()
    user = request.user
    return render(request, "post.html", {
        "post": post,
        "user": user,
        "post_id": post_id,
        "post_count": post_count,
        "user_profile": user_profile
    })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if post.author != request.user:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(data=request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, "new.html", {"form": form, "post": post})
