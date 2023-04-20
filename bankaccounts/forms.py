from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import BankAccountApplications, BankAccountApplicationStatus, BankAccountType

CustomUser = get_user_model()

class MyBankAccountApplicationForm(forms.ModelForm):
    class Meta:
        model = BankAccountApplications
        fields = '__all__'
        widgets = {
            'status': forms.HiddenInput(),
            'user': forms.HiddenInput(),
            'created_at': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user') # Get the user from kwargs
        super().__init__(*args, **kwargs)
        self.initial['created_at'] = timezone.now()
        self.initial['user'] = user # Set the user field to the current logged in user

    def clean(self):
        cleaned_data = super().clean()
        # Add additional validation logic here if needed
        return cleaned_data
