from django.contrib import admin
from .models import DebitTransactions, CreditTransactions, CreditTransactionType, DebitTransactionType
# Register your models here.
admin.site.register(DebitTransactions)
admin.site.register(CreditTransactions)
admin.site.register(CreditTransactionType)
admin.site.register(DebitTransactionType)
