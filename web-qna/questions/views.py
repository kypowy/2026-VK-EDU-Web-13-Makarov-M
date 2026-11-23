from django.shortcuts import render , get_object_or_404, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum
import json
from .forms import QuestionForm, AnswerForm
from .models import *

from django.db.models import Subquery, OuterRef, IntegerField

def _profile(request):
    return request.user.profile if request.user.is_authenticated else None

def _with_user_vote(qs, rate_model, fk, profile):
    if profile is None:
        return qs
    sub = (rate_model.objects
           .filter(**{fk: OuterRef('pk')}, author=profile)
           .values('value')[:1])
    return qs.annotate(user_value=Subquery(sub, output_field=IntegerField()))



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


@ensure_csrf_cookie
def index(request):
    profile = _profile(request)
    qs = _with_user_vote(Question.objects.latest(), QuestionRate, 'question', profile)
    page_obj = paginate(qs, request, per_page=5)
    return render(request, 'questions/index.html', {
        'page_obj': page_obj,
        'questions': page_obj.object_list,
    })

@ensure_csrf_cookie
def hot(request):
    profile = _profile(request)
    qs = _with_user_vote(Question.objects.popular(), QuestionRate, 'question', profile)
    page_obj = paginate(qs, request, per_page=5)
    return render(request, 'questions/hot.html', {
        'page_obj': page_obj,
        'questions': page_obj.object_list,
    })

@ensure_csrf_cookie
def tag(request, tag_name):
    profile = _profile(request)
    tag_obj = get_object_or_404(Tag, slug=tag_name)
    qs = _with_user_vote(Question.objects.tag(tag_obj), QuestionRate, 'question', profile)
    page_obj = paginate(qs, request, per_page=5)
    return render(request, "questions/tag.html", {
        "tag": tag_obj, "tag_name": tag_obj.name,
        "questions": page_obj.object_list, "page_obj": page_obj,
    })

@ensure_csrf_cookie
def post(request, question_id):
    profile = _profile(request)
    question = get_object_or_404(
        _with_user_vote(Question.objects.detail(), QuestionRate, 'question', profile),
        pk=question_id,
    )
    answers_qs = _with_user_vote(
        Answer.objects.for_question(question), AnswerRate, 'answer', profile
    )
    page_obj = paginate(answers_qs, request, per_page=5)

    if request.method == 'POST':
        form = AnswerForm(request.POST, user=request.user, question=question)
        if form.is_valid():
            form.save()
            return redirect(question.get_absolute_url())
    else:
        form = AnswerForm(user=request.user, question=question)

    return render(request, "questions/postinfo.html", {
        "question": question,
        "answers": page_obj.object_list,
        "page_obj": page_obj,
        "form": form,
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


@require_POST
@login_required
def rateQuestion(request, question_id):
    question = get_object_or_404(Question.objects.detail(), pk=question_id)
    try:
        value = int(json.loads(request.body)['value'])
    except (ValueError, KeyError, json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'bad value'}, status=400)
    if value not in (1, -1):
        return JsonResponse({'error': 'bad value'}, status=400)

    profile = request.user.profile

    rate = QuestionRate.objects.filter(question=question, author=profile).first()
    if rate is None:
        rate = QuestionRate.objects.create(
            question=question, author=profile, value=value,
        )
        new_value = value
    elif rate.value == value:
        rate.value = 0
        rate.save(update_fields=['value'])
        new_value = 0
    else:
        rate.value = value
        rate.save(update_fields=['value'])
        new_value = value


    total = (QuestionRate.objects
             .filter(question=question)
             .aggregate(s=Sum('value'))['s'] or 0)
    
    return JsonResponse({'rating' : total,
                         'user_value' : new_value})

@require_POST
@login_required
def rateAnswer(request, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    try:
        value = int(json.loads(request.body)['value'])
    except (ValueError, KeyError, json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'bad value'}, status=400)
    if value not in (1, -1):
        return JsonResponse({'error': 'bad value'}, status=400)



    profile = request.user.profile

    rate = AnswerRate.objects.filter(answer=answer, author=profile).first()
    if rate is None:
        rate = AnswerRate.objects.create(
            answer=answer, author=profile, value=value,
        )
        new_value = value
    elif rate.value == value:
        rate.value = 0
        rate.save(update_fields=['value'])
        new_value = 0
    else:
        rate.value = value
        rate.save(update_fields=['value'])
        new_value = value


    total = (AnswerRate.objects
             .filter(answer=answer)
             .aggregate(s=Sum('value'))['s'] or 0)
    
    return JsonResponse({'rating' : total,
                         'user_value': new_value})

@require_POST
@login_required
def markCorrectAnswer(request, answer_id, question_id):
    question = get_object_or_404(Question.objects.detail(), pk=question_id)
    answer = get_object_or_404(Answer, pk=answer_id)
    profile = request.user.profile
    
    if question.author != profile or answer.question != question:
        return JsonResponse({'error': 'no rights'}, status=403)
    
    data = json.loads(request.body)
    answer.is_correct = bool(data.get('is_correct', False))
    answer.save()
    
    return JsonResponse({'status': 'ok', 'is_correct': answer.is_correct}, status=200)