from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .models import QuestionRate, AnswerRate
from .ratings import recalc_question_rating, recalc_answer_rating


# --- QuestionRate ---
@receiver(pre_save, sender=QuestionRate)
def _remember_old_question(sender, instance, **kwargs):
    instance._old_question_id = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list("question_id", flat=True)
        .first()
        if instance.pk else None
    )


@receiver(post_save, sender=QuestionRate)
def _sync_question_rate(sender, instance, **kwargs):
    recalc_question_rating(instance.question_id)
    old = getattr(instance, "_old_question_id", None)
    if old and old != instance.question_id:
        recalc_question_rating(old)


@receiver(post_delete, sender=QuestionRate)
def _sync_question_rate_deleted(sender, instance, **kwargs):
    recalc_question_rating(instance.question_id)


# --- AnswerRate (аналогично) ---
@receiver(pre_save, sender=AnswerRate)
def _remember_old_answer(sender, instance, **kwargs):
    instance._old_answer_id = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list("answer_id", flat=True)
        .first()
        if instance.pk else None
    )


@receiver(post_save, sender=AnswerRate)
def _sync_answer_rate(sender, instance, **kwargs):
    recalc_answer_rating(instance.answer_id)
    old = getattr(instance, "_old_answer_id", None)
    if old and old != instance.answer_id:
        recalc_answer_rating(old)


@receiver(post_delete, sender=AnswerRate)
def _sync_answer_rate_deleted(sender, instance, **kwargs):
    recalc_answer_rating(instance.answer_id)