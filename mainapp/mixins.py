from django import forms

from .constants import GITHUB_VALIDATION_MESSAGE


class GitHubURLMixin:
    """Миксин для валидации GitHub URL"""

    def clean_github_url(self):
        url = self.cleaned_data.get('github_url')
        if url and 'github.com' not in url:
            raise forms.ValidationError(GITHUB_VALIDATION_MESSAGE)
        return url
