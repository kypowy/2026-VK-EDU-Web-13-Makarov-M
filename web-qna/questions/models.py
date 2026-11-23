from django.db import models
from django.db.models import Count
from django.urls import reverse
from django.db.models import Count, Subquery, OuterRef, IntegerField

class QuestionManager(models.Manager):
    def _for_cards(self):
        # Создаем подзапрос для подсчета ответов
        answer_count_subquery = Answer.objects.filter(
            question=OuterRef('pk')
        ).values('question').annotate(
            c=Count('id')
        ).values('c')

        return (
            self
            .select_related("author__user")
            .prefetch_related("questiontag__tag")
            .annotate(ans_count=Subquery(answer_count_subquery, output_field=IntegerField()))
        )

    def popular(self):
        return self._for_cards().order_by("-rating", "-created_at")

    def latest(self):
        return self._for_cards().order_by("-created_at")

    def detail(self):
        return self._for_cards()

    def tag(self, tag_obj):
        return (
            self._for_cards()
            .filter(questiontag__tag=tag_obj)
            .order_by("-created_at")
        )

class TagManager(models.Manager):
    def popular(self):
        return (
            self
            .annotate(num_questions=Count("questiontag"))
            .filter(num_questions__gt=0)
            .order_by("-num_questions", "name")
        )


class AnswerManager(models.Manager):
    def for_question(self, question):
        return (
            self.filter(question=question)
            .select_related("author__user")
            .order_by("-is_correct", "-rating", "created_at")
        )


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField("адресное имя", max_length=100, unique=True)
    objects = TagManager()
    class Meta:
        verbose_name_plural = "Тэги"
        verbose_name = "Тэг"
    def __str__(self):
        return self.name
  

class Question(models.Model):
    title = models.CharField(max_length=50, verbose_name="Заголовок вопроса")
    description = models.TextField(verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    author = models.ForeignKey(
        "core.Profile",
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    rating = models.IntegerField(default=0, editable=False, verbose_name="рейтинг")

    objects = QuestionManager()

    class Meta:
        verbose_name_plural = "Вопросы"
        verbose_name = "Вопрос"
        indexes = [
            models.Index(fields=["-rating", "-created_at"], name="question_pop_idx"),
            models.Index(fields=["-created_at"], name="question_latest_idx"),
            models.Index(fields=["author"], name="question_author_idx"),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("question", kwargs={"question_id": self.pk})


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="question_answer",
        verbose_name="Вопрос",
    )
    description = models.CharField(max_length=256, verbose_name="Описание ответа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    author = models.ForeignKey(
        "core.Profile",
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    is_correct = models.BooleanField("правильный ответ", default=False)
    rating = models.IntegerField(default=0, editable=False, verbose_name="рейтинг")

    objects = AnswerManager()

    class Meta:
        verbose_name_plural = "Ответы"
        verbose_name = "Ответ"
        indexes = [
            models.Index(
                fields=["question", "-is_correct", "-rating", "created_at"],
                name="answer_q_order_idx",
            ),
            models.Index(fields=["author"], name="answer_author_idx"),
        ]

    def __str__(self):
        return f"Ответ {self.pk} на вопрос {self.question_id}"


class QuestionRate(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="question_like",
        verbose_name="Вопрос",
    )
    author = models.ForeignKey(
        "core.Profile",
        on_delete=models.CASCADE,
        related_name="question_author",
        verbose_name="Пользователь",
    )
    value = models.SmallIntegerField(
        "оценка",
        choices=[(1, "Плюс"), (-1, "Минус"), (0, "Ноль")],
        default=1,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "author"],
                name="question_author_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["author"], name="qrate_author_idx"),
        ]
        verbose_name = "Оценка вопроса"
        verbose_name_plural = "Оценки вопросов"

    def __str__(self):
        return f"Оценка {self.value}: вопрос {self.question}, пользователь {self.author}"


class AnswerRate(models.Model):
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="answer_like",
    )
    author = models.ForeignKey(
        "core.Profile",
        on_delete=models.CASCADE,
        related_name="answer_author",
    )
    value = models.SmallIntegerField(
        "оценка",
        choices=[(1, "Плюс"), (-1, "Минус"), (0, "Ноль")],
        default=1,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["answer", "author"],
                name="answer_author_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["author"], name="arate_author_idx"),
        ]
        verbose_name = "Оценка ответа"
        verbose_name_plural = "Оценки ответов"

    def __str__(self):
        return f"Оценка {self.value}: ответ {self.answer_id}, пользователь {self.author_id}"


class QuestionTag(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="questiontag",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="questiontag",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question", "tag"],
                name="questiontag_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["tag", "question"], name="qtag_tag_q_idx"),
        ]