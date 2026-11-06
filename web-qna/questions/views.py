from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404

ANSWERS_BY_QUESTION = {
    i: [
        {
            'id': j,
            'text': f'Text ans {i}-{j} ' * 10,
            'rating': 3 * j,
        }
        for j in range(i + 1)
    ]
    for i in range(30)
}

TAGS_POOL = ['demo', 'tags', 'lists', 'some', 'dota2', 'another', 'parts']


def _tags_for(i):
    tags = {TAGS_POOL[i % len(TAGS_POOL)]}
    if i % 2 == 0:
        tags.add(TAGS_POOL[(i + 3) % len(TAGS_POOL)])
    if i % 5 == 0:
        tags.add(TAGS_POOL[(i + 5) % len(TAGS_POOL)])
    return sorted(tags)


QUESTION_LIST = [
    {
        'id': i,
        'title': f'Title {i}',
        'text': f'Text {i}' * 10,
        'rating': 5 * i,
        'ans_count': len(ANSWERS_BY_QUESTION[i]),
        'tags': _tags_for(i),
    }
    for i in range(30)
]


def paginate(objects_list, request, per_page=10):
    """
    ?page= (не число) -> первая страница.
    ?page= вне диапазона (0, отрицательное, больше последней) -> последняя страница.
    Пустой список -> безопасно отдаёт пустую первую страницу.
    """
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page


def index(request):
    page_obj = paginate(QUESTION_LIST, request, per_page=5)
    return render(request, 'questions/index.html', context={
        'questions': page_obj.object_list,
        'page_obj': page_obj,
    })


def hot(request):
    hot_questions = sorted(QUESTION_LIST, key=lambda q: q['rating'], reverse=True)
    page_obj = paginate(hot_questions, request, per_page=5)
    return render(request, 'questions/hot.html', context={
        'questions': page_obj.object_list,
        'page_obj': page_obj,
    })


def post(request, question_id):
    question = next((q for q in QUESTION_LIST if q['id'] == question_id), None)
    if question is None:
        raise Http404("Question not found")

    answers = ANSWERS_BY_QUESTION[question_id]
    page_obj = paginate(answers, request, per_page=5)

    return render(request, 'questions/postinfo.html', context={
        'question': question,
        'answers': page_obj.object_list,
        'page_obj': page_obj,
    })


def tag(request, tag_name):
    questions = [q for q in QUESTION_LIST if tag_name in q['tags']]
    if not questions:
        raise Http404("Tag not found")

    page_obj = paginate(questions, request, per_page=5)

    return render(request, 'questions/tag.html', context={
        'tag_name': tag_name,
        'questions': page_obj.object_list,
        'page_obj': page_obj,
    })


def ask(request):
    return render(request, 'questions/ask_question.html')
