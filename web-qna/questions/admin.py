from django.contrib import admin, messages
from .models import *

from .ratings import recalc_question_rating, recalc_answer_rating


@admin.action(description="Пересчитать рейтинг выбранных вопросов")
def recalc_question_ratings(modeladmin, request, queryset):
    for qid in queryset.values_list("pk", flat=True):
        recalc_question_rating(qid)
    messages.success(request, f"Пересчитано вопросов: {queryset.count()}")

@admin.action(description="Пересчитать рейтинг выбранных ответов")
def recalc_answer_ratings(modeladmin, request, queryset):
    ids = list(queryset.values_list("pk", flat=True))
    for aid in ids:
        recalc_answer_rating(aid)
    messages.success(request, f"Пересчитано ответов: {len(ids)}")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    ordering = ("name", "pk")
    search_fields = ("name", "slug")

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    show_change_link = True
    fields = ("author", "description", "is_correct", "rating", "created_at")
    readonly_fields = ("created_at", "rating")
    autocomplete_fields = ("author",)
    ordering = ("created_at", "pk")

class QuestionTagInline(admin.TabularInline):
    model = QuestionTag
    extra = 1                      
    autocomplete_fields = ("tag",) 
    verbose_name = "тэг"
    verbose_name_plural = "тэги"

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "rating", "answers_count", "created_at")
    search_fields = ("title", "text")
    list_filter = ("created_at",)
    autocomplete_fields = ("author",)
    list_select_related = ("author",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("author")
            .annotate(_answers_count=Count("question_answer", distinct=True))
        )

    @admin.display(ordering="_answers_count", description="ответов")
    def answers_count(self, obj):
        return obj._answers_count
    inlines = (AnswerInline, QuestionTagInline)
    actions = (recalc_question_ratings,)
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "author",
        "is_correct",
        "rating",
        "created_at",
    )
    search_fields = ("text", "question__title", "author__username")
    list_filter = ("is_correct", "created_at")
    date_hierarchy = "created_at"
    autocomplete_fields = ("question", "author")
    list_select_related = ("question", "author")
    actions = (recalc_answer_ratings,)
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("question", "author")

    
@admin.register(QuestionRate)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "question", "value")
    ##search_fields = ("user__username", "question__title")
    list_filter = ("value",)
    autocomplete_fields = ("author", "question")
    list_select_related = ("author", "question")


@admin.register(AnswerRate)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "answer", "value")
    ##search_fields = ("user__username", "answer__text")
    list_filter = ("value",)
    autocomplete_fields = ("author", "answer")
    list_select_related = ("author", "answer")






