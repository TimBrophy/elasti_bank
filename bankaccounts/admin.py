from django.contrib import admin
from bankaccounts.models import BankAccountType, BankAccount, BankAccountApplications, BankAccountApplicationStatus

# Register your models here.
admin.site.register(BankAccount)
admin.site.register(BankAccountType)
admin.site.register(BankAccountApplications)
admin.site.register(BankAccountApplicationStatus)