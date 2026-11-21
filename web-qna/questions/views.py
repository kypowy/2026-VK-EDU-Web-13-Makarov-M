from django.shortcuts import render , get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from .models import *

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
    latest = Question.objects.latest()
    page_obj = paginate(latest, request, per_page=5)
    return render(request, 'questions/index.html',context={
        'page_obj': page_obj,
        'questions' : page_obj.object_list,
    } )


def hot(request):
    hot = Question.objects.popular()
    page_obj = paginate(hot, request, per_page=5)
    return render(request, 'questions/hot.html',context={
        'page_obj': page_obj,
        'questions' : page_obj.object_list,
    } )


def post(request, question_id):
    question = get_object_or_404(Question.objects.detail(), pk=question_id)
    answers = Answer.objects.for_question(question)
    page_obj = paginate(answers, request, per_page=5)

    return render(request, "questions/postinfo.html", {
        "question": question,
        "answers": page_obj.object_list,
        "page_obj": page_obj,
    })


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, slug=tag_name)

    questions = Question.objects.tag(tag_obj)
    page_obj = paginate(questions, request, per_page=5)

    return render(request, "questions/tag.html", {
        "tag": tag_obj,
        "tag_name": tag_obj.name,                          
        "questions": page_obj.object_list,
        "page_obj": page_obj,
    })

def ask(request):
    return render(request, 'questions/ask_question.html')
