from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import NUMBER_OF_POSTS

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import paginator_method

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_method(request, post_list, NUMBER_OF_POSTS)
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    posts = group.posts.all()
    page_obj = paginator_method(request, posts, NUMBER_OF_POSTS)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = paginator_method(request, posts, NUMBER_OF_POSTS)
    posts_count = posts.count()
    follower = author.following.all()
    follower_list = []
    for i in follower:
        follower_list.append(i.user)
    authenticated = request.user.is_authenticated
    following = (request.user in follower_list) and authenticated
    context = {
        'author': author,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form_comment = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post_id=post_id)
    post_count = author.posts.all().count()
    context = {
        'post': post,                  # Имена 'requrst_name' и 'post_name'
        'post_count': post_count,      # для ссылки на редоктирование поста
        'request_name': request.user,  # Если 'requret_name' == 'post_name'
        'post_author': author,         # то пользователь видит ссылку
        'form_comment': form_comment,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    form = PostForm()
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.username != post.author.username:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(instance=post)
    context = {'form': form, 'is_edit': True}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    follow = user.follower.all()
    author_list = []
    for i in follow:
        author_list.append(i.author)
    posts = Post.objects.filter(author__in=author_list)
    page_obj = paginator_method(request, posts, NUMBER_OF_POSTS)
    template = 'posts/follow.html'
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = author.following.all()
    user_list = []
    for i in following:
        user_list.append(i.user)
    if (request.user not in user_list) and (request.user != author):
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = get_object_or_404(
        Follow,
        user=request.user,
        author=author
    )
    following.delete()
    return redirect('posts:profile', username=username)
