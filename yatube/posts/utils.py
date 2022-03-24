from django.core.paginator import Paginator


def paginator_method(request, posts, number_per_page):
    paginator = Paginator(posts, number_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
