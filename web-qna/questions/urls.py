# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('question/<int:question_id>/', views.post, name='question'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('ask/', views.ask, name='ask'),
    path('questions/<int:question_id>/rate/',views.rateQuestion, name="rateQuestion" ),
    path('answers/<int:answer_id>/rate/',views.rateAnswer, name="rateQuestion" ),
    path('questions/<int:question_id>/<int:answer_id>/correct/', views.markCorrectAnswer, name="markCorrectAnswer")
]