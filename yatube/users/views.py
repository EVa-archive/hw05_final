from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'

    def get_context_data(self):
        context = {
            'title': 'Зарегистрироваться'
        }
        return context


class PasswordChange(PasswordChangeView):
    success_url = 'done/'
    template_name = 'user/password_change_done.html'

    def get_context_data(self):
        context = {
            'title': 'Сброс пароля'
        }
        return context
