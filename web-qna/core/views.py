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

from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme

def login(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user)

                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect('index')

            form.add_error(None, 'Username or password is incorrect.')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', context={
        'form': form,
        'next': next_url,
    })

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