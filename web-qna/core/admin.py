from django.contrib import admin
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
# Register your models here.
class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    max_num = 1

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "avatar")
    search_fields = ("user__username", "user__email")
    list_filter = ("user__is_staff", "user__is_active")
    list_select_related = ("user",)
    autocomplete_fields = ("user",)


admin.site.unregister(User)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    list_select_related = ("profile",)
