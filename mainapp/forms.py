import re

from django import forms

from .constants import PHONE_REGEX_PATTERN
from .models import User, Project
from .mixins import GitHubURLMixin


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput, label='Пароль'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, label='Подтверждение пароля'
    )

    class Meta:
        model = User
        fields = ['name', 'surname', 'email', 'phone']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(PHONE_REGEX_PATTERN, phone):
            raise forms.ValidationError('Неверный формат номера')

        if phone.startswith('8'):
            phone = '+7' + phone[1:]

        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                'Этот номер уже зарегистрирован'
            )

        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже зарегистрирован')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')

        return cleaned_data


class UserLoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class UserProfileForm(GitHubURLMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'surname', 'avatar', 'about', 'phone', 'github_url']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not re.match(PHONE_REGEX_PATTERN, phone):
                raise forms.ValidationError('Неверный формат номера')

            if phone.startswith('8'):
                phone = '+7' + phone[1:]

            if User.objects.filter(phone=phone).exclude(
                id=self.instance.id
            ).exists():
                raise forms.ValidationError(
                    'Этот номер уже используется'
                )

        return phone


class ProjectForm(GitHubURLMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'github_url', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
