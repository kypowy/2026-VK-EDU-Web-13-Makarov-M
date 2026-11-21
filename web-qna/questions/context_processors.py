from django.core.cache import cache
from .models import Tag

POPULAR_TAGS_CACHE_KEY = "popular_tags_v1"
POPULAR_TAGS_TTL = 10  # секунды, можно поставить больше потому что популярные тэги не часто меняются


def popular_tags(request):
    tags = cache.get(POPULAR_TAGS_CACHE_KEY)
    if tags is None:
        tags = list(Tag.objects.popular()[:5])
        cache.set(POPULAR_TAGS_CACHE_KEY, tags, POPULAR_TAGS_TTL)
    return {"popular_tags": tags}