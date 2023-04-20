from django.db import models
from accounts.models import CustomUser
import uuid


class BankAccountType(models.Model):
    typename = models.CharField(max_length=15, verbose_name='Bank account type')
    description = models.CharField(max_length=300, verbose_name='Description')
    image = models.ImageField(blank=True, upload_to='images')

    def __str__(self):
        return self.typename

class BankAccountApplicationStatus(models.Model):
    statusname = models.CharField(max_length=56, verbose_name="Bank account application status")

    def __str__(self):
        return self.statusname


class BankAccount(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=False)
    bankaccounttype = models.ForeignKey(BankAccountType, on_delete=models.CASCADE)
    balance = models.FloatField(max_length=250, verbose_name="account balance", null=False)
    account_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name_plural = "Bank Accounts"

    def __str__(self):
        return f'{self.bankaccounttype} - {self.account_number}'


class BankAccountApplications(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=False)
    bankaccounttype = models.ForeignKey(BankAccountType, on_delete=models.CASCADE, verbose_name='Bank account type')
    contactnumber = models.CharField(max_length=56, verbose_name='Contact number')
    streetaddress1 = models.CharField(max_length=256, null=False, verbose_name='Street address 1')
    streetaddress2 = models.CharField(max_length=256, null=True, verbose_name='Street address 2')
    suburb = models.CharField(max_length=256, null=False, verbose_name='Suburb')
    province = models.CharField(max_length=256, null=False, verbose_name='Province')
    country = models.CharField(max_length=256, null=False, verbose_name='Country')
    grossincome = models.IntegerField(verbose_name='Gross monthly income')
    expenses = models.IntegerField(verbose_name='Total monthly expenses')
    status = models.ForeignKey(BankAccountApplicationStatus, on_delete=models.CASCADE, default=1)

    class Meta:
        verbose_name_plural = "Bank Account Applications"

    def __str__(self):
        return f'{self.user} - {self.bankaccounttype} - {self.created_at}'
