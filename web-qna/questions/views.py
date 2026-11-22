from django.shortcuts import render , get_object_or_404, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.contrib.auth.decorators import login_required
from .forms import QuestionForm, AnswerForm
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
    if request.method == 'POST':
        form = AnswerForm(request.POST, user=request.user, question=question)
        if form.is_valid():
            question = form.save()
    else:
        form = AnswerForm(user=request.user, question=question)

    return render(request, "questions/postinfo.html", context={
        "question": question,
        "answers": page_obj.object_list,
        "page_obj": page_obj,
        "form" : form,
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

@login_required
def ask(request):
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, user=request.user)
        if form.is_valid():
            question = form.save()
            return redirect(question.get_absolute_url())
    else:
        form = QuestionForm(user=request.user)        
    return render(request, 'questions/ask_question.html', context={'form' : form})


