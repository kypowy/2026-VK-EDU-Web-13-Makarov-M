from django.db import transaction
from django.db.models import Sum

from .models import Question, Answer, QuestionRate, AnswerRate


def _recalc(rate_model, target_model, fk_name, target_id):
    if target_id is None:
        return
    with transaction.atomic():
        # Блокируем строку цели — иначе два параллельных голоса
        # посчитают SUM по неполному срезу и «потеряют» один голос.
        locked = (
            target_model.objects
            .select_for_update()
            .filter(pk=target_id)
            .only("pk")
            .first()
        )
        if locked is None:
            return  # объект уже удалён (например, каскадом)
        total = (
            rate_model.objects
            .filter(**{fk_name: target_id})
            .aggregate(s=Sum("value"))["s"] or 0
        )
        target_model.objects.filter(pk=target_id).update(rating=total)


def recalc_question_rating(question_id):
    _recalc(QuestionRate, Question, "question_id", question_id)


def recalc_answer_rating(answer_id):
    _recalc(AnswerRate, Answer, "answer_id", answer_id)