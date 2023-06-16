from django import forms
from django.contrib.auth import get_user_model
from bankaccounts.models import BankAccount
from transactions.models import DebitTransactions, DebitTransactionType
from .models import DebitTransactions
from datetime import datetime

CustomUser = get_user_model()

class DebitTransactionForm(forms.ModelForm):
    created_at = forms.DateTimeField(initial=datetime.now(), widget=forms.HiddenInput)
    transaction_type = forms.ModelChoiceField(queryset=DebitTransactionType.objects.filter(name='EFT'))

    class Meta:
        model = DebitTransactions
        fields = ['source_account', 'destination_bank', 'recipient_name', 'destination_account', 'created_at', 'value', 'description', 'reference', 'transaction_type']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_account'].queryset = BankAccount.objects.filter(user=user)


class TransferForm(forms.ModelForm):
    created_at = forms.DateTimeField(initial=datetime.now(), widget=forms.HiddenInput)
    transaction_type = forms.ModelChoiceField(queryset=DebitTransactionType.objects.filter(name='Transfer'))
    destination_account = forms.ModelChoiceField(queryset=None)
    destination_bank = forms.CharField(initial='elasti_bank', widget=forms.HiddenInput())
    recipient_name = forms.CharField(initial=None, widget=forms.HiddenInput())

    class Meta:
        model = DebitTransactions
        fields = ['source_account', 'destination_account', 'created_at', 'value', 'description', 'reference', 'transaction_type']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_account'].queryset = BankAccount.objects.filter(user=user)
        self.fields['destination_account'].queryset = BankAccount.objects.filter(user=user).exclude(id=self.fields['source_account'].initial)
        self.fields['destination_account'].widget = forms.Select(choices=[(acc.id, f'{acc.bankaccounttype} - {acc.account_number}') for acc in self.fields['destination_account'].queryset])
        self.fields['recipient_name'].initial = user.get_full_name()

    def clean(self):
        cleaned_data = super().clean()
        source_account = cleaned_data.get('source_account')
        destination_account = cleaned_data.get('destination_account')
        if source_account == destination_account:
            raise forms.ValidationError("Source and destination account must not be the same.")
        return cleaned_data