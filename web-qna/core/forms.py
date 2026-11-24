from django import forms
from django.contrib.auth.models import User
from .models import Profile

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['description', 'avatar']



class LoginForm(forms.Form):
    username = forms.CharField(max_length=10)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username == password:
            raise forms.ValidationError('Username and password same')

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data['username']
        if username == 'test':
            raise forms.ValidationError('Test user error')

        return username

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Repeat Password")

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("User with this username alreadey exists")
        if username.startswith('admin'):
            raise forms.ValidationError('Admin user error')
        return username

    def clean(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError('Passwords do not match')
        return self.cleaned_data

    def save(self, commit=True):
        self.cleaned_data.pop('password2')
        
        user = User.objects.create_user(**self.cleaned_data)
        Profile.objects.create(user=user)
        return user

