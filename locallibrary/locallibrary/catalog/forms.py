
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import datetime #for checking renewal date range.
from django import forms
from .models import Profile
from django.contrib.auth.models import User

class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3).")

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        #Проверка того, что дата не выходит за "нижнюю" границу (не в прошлом).
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        #Проверка того, то дата не выходит за "верхнюю" границу (+4 недели).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Помните, что всегда надо возвращать "очищенные" данные.
        return data

class SecretQuestionForm(forms.Form):
    answer = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'autofocus': 'autofocus'}))

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'secret_question', 'secret_answer')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['secret_question', 'secret_answer']

class ResetPasswordForm(forms.Form):
    username = forms.CharField(max_length=254)
    secret_answer = forms.CharField(max_length=255, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        secret_answer = cleaned_data.get("secret_answer")

        if username and secret_answer:
            try:
                # Получаем пользователя и его профиль
                user = User.objects.get(username=username)
                profile = user.profile
                if profile.secret_answer != secret_answer:
                    raise forms.ValidationError("Неверный ответ на секретный вопрос.")
            except User.DoesNotExist:
                raise forms.ValidationError("Пользователь с таким именем не найден.")
        return cleaned_data