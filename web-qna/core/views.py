from django.shortcuts import render
from .forms import LoginForm, RegisterForm, ProfileEditForm
from .models import Profile
from django.http.response import HttpResponseRedirect, JsonResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.urls import reverse
# Create your views here.

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)


        if form.is_valid():
            print(f"{form.cleaned_data=}")

            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(request, username=username, password=password)

            if user is not None:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                form.add_error(None, 'Username or password is incorrect.')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', context={'form': form})

def signup(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            return HttpResponseRedirect(reverse('index'))
    else:
        form = RegisterForm()

    return render(request, 'core/signup.html', context={'form': form})

@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user) # по сути здесь его не должно быть

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('profile'))
    else:
        form = ProfileEditForm(instance=profile)
    return render(request, 'core/profile_edit.html', context={'form':form, 'profile' : profile})    