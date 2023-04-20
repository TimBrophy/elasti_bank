from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from bankaccounts.models import BankAccount
from accounts.models import CustomUser


# Create your models here.
class CreditTransactionType(models.Model):
    name = models.CharField(null=False, max_length=52)

    def __str__(self):
        return self.name


class CreditTransactions(models.Model):
    source_account = models.CharField(null=False, max_length=256)
    source_bank = models.CharField(null=True, max_length=256)
    from_name = models.CharField(null=True, max_length=256)
    destination_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=False)
    value = models.IntegerField(null=False, validators=[MinValueValidator(1)])
    description = models.CharField(null=False, max_length=256)
    reference = models.CharField(null=False, max_length=256)
    transaction_type = models.ForeignKey(CreditTransactionType, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.source_bank} - {self.source_account} - {self.created_at}'


class DebitTransactionType(models.Model):
    name = models.CharField(null=False, max_length=52)

    def __str__(self):
        return self.name


class DebitTransactions(models.Model):
    source_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    destination_bank = models.CharField(null=True, max_length=256)
    recipient_name = models.CharField(null=True, max_length=256)
    destination_account = models.CharField(null=False, max_length=256)
    created_at = models.DateTimeField(auto_now_add=False)
    value = models.IntegerField(null=False, validators=[MinValueValidator(1)])
    description = models.CharField(null=False, max_length=256)
    reference = models.CharField(null=False, max_length=256)
    transaction_type = models.ForeignKey(DebitTransactionType, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.destination_bank} - {self.destination_account} - {self.created_at}'
