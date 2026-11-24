from django import forms
from django.contrib.auth.models import User
from .models import Question, Tag, QuestionTag, Answer
from django.utils.text import slugify
from core.models import Profile

class AnswerForm(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ('description',)
    def __init__(self, *args, user=None, question=None,**kwargs):
        self.user = user
        self.question = question
        super().__init__(*args, **kwargs)
    def save(self, commit=True):
        answer = super().save(commit=False)  
        if answer.pk is None:                    
            if answer.author_id is None:
                profile, _ = Profile.objects.get_or_create(user=self.user)
                answer.author = profile
            if answer.question_id is None:
                answer.question = self.question      
        if commit:
            answer.save()    
        return answer    
class QuestionForm(forms.ModelForm):
    tags = forms.CharField()

    def clean_tags(self):
        raw = self.cleaned_data.get("tags", "")
        for name in raw.split():
            if len(name) > Tag._meta.get_field("name").max_length:
                raise forms.ValidationError(
                    f"Тег «{name}» длиннее "
                    f"{Tag._meta.get_field('name').max_length} символов"
                )
        return raw
    class Meta:
        model = Question
        fields = ("title","description")

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        question = super().save(commit=False)  
        if question.author_id is None:
            profile, _ = Profile.objects.get_or_create(user=self.user)
            question.author = profile
            question.author = self.user.profile  
        if commit:
            question.save()
            self._save_tags(question)
        return question        

    def _save_tags(self, question):
        raw = self.cleaned_data.get("tags", "")

        names, seen = [], set()
        for name in raw.split():
            if name not in seen:
                seen.add(name)
                names.append(name)

        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={"slug": _make_slug(name)},
            )
            tags.append(tag)

        QuestionTag.objects.filter(question=question).delete()
        QuestionTag.objects.bulk_create(
            [QuestionTag(question=question, tag=t) for t in tags],
            ignore_conflicts=True,
        )

def _make_slug(name):
    base = slugify(name) or "tag"
    slug, i = base, 1
    while Tag.objects.filter(slug=slug).exists():
        i += 1
        slug = f"{base}-{i}"
    return slug