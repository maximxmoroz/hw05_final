from .utils import page_context
from django.conf import settings

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, Follow
from django.core.paginator import Paginator


def pagination(request, posts):
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return(page_obj)


@cache_page(20)
def index(request):
    post_list = Post.objects.select_related().all()
    paginator = Paginator(post_list, settings.PAGINATOR_POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    index = True
    context = {
        'page_obj': page_obj,
        'index': index,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = page_context(request, group.posts.all())
    context.update(group=group)
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = pagination(request, posts)
    following = (request.user.is_authenticated
                 and request.user != author
                 and Follow.objects.filter(
                     user=request.user,
                     author=author).exists())
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('author')
    post_count = post.author.posts.count()
    following = (request.user.is_authenticated
                 and post.author.following.filter(user=request.user).exists())
    context = {
        'post': post,
        'post_count': post_count,
        'comments': comments,
        'following': following,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        author = request.user
        form = PostForm(request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = author
            new_post.save()
            return redirect('posts:profile', author.username)
        return render(request, 'posts/create_post.html',
                      {'is_edit': True, 'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html',
                  {'is_edit': True, 'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'post': post,
            'form': form,
            'is_edit': True,}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related('group').filter(
            author__following__user=request.user)
    context = page_context(request, posts)
    context.update(posts=posts)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author__username=username
    ).delete()
    return redirect('posts:profile', username)
