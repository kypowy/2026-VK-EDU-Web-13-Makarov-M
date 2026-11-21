from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db.models.functions import Coalesce

from questions.models import Question, Answer


class Command(BaseCommand):
    help = "Пересчитать денормализованные рейтинги"

    def handle(self, *args, **options):
        fixed_q = fixed_a = 0

        qs = Question.objects.annotate(_s=Coalesce(Sum("question_like__value"), 0))
        for q in qs.only("pk", "rating").iterator():
            if q.rating != q._s:
                Question.objects.filter(pk=q.pk).update(rating=q._s)
                fixed_q += 1

        qs = Answer.objects.annotate(_s=Coalesce(Sum("answer_like__value"), 0))
        for a in qs.only("pk", "rating").iterator():
            if a.rating != a._s:
                Answer.objects.filter(pk=a.pk).update(rating=a._s)
                fixed_a += 1

        self.stdout.write(self.style.SUCCESS(
            f"Исправлено вопросов: {fixed_q}, ответов: {fixed_a}"
        ))