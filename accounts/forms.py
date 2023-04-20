from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from django.forms.widgets import DateInput

class CustomUserCreationForm(UserCreationForm):
    birthdate = forms.DateInput(format='%d/%m/%Y')
    class Meta:
        model = CustomUser
        exclude = ['password', 'last_login', 'groups', 'user_permissions', 'date_joined', 'is_superuser', 'is_staff', 'is_active']

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
