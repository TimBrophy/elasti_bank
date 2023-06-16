from django.db import models
from bankaccounts.models import BankAccountType
from transactions.models import DebitTransactionType

# Create your models here.
class SpecialOffer(models.Model):
    name = models.CharField(max_length=256, verbose_name='Special offer name')
    description = models.CharField(max_length=512, verbose_name='Special offer description')
    search_terms = models.CharField(max_length=512, verbose_name='Special offer search terms')
    bankaccounttype = models.ForeignKey(BankAccountType, on_delete=models.CASCADE, verbose_name='Bank account type')
    transactiontype = models.ForeignKey(DebitTransactionType, on_delete=models.CASCADE, verbose_name='Transaction type')


    def __str__(self):
        return self.name
