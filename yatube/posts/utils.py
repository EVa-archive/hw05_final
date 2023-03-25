from django.core.paginator import Paginator

COUNTER_POSTS = 10


def paginator(post_list, request):
    pgntr = Paginator(post_list, COUNTER_POSTS)
    page_number = request.GET.get('page')
    page_obj = pgntr.get_page(page_number)
    return page_obj
