from django.db import models
from django.conf import settings
# Create your models here.



class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="пользователь",
    )
    avatar = models.ImageField(
        "аватар", upload_to="avatars/", blank=True
    )
    #nickname = models.CharField(unique=True, max_length=30)
    description = models.TextField(verbose_name="Описание профиля", default="", blank=True)
    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        return self.user.get_username()