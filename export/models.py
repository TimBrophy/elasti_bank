from django.db import models
from transactions.models import CreditTransactions, DebitTransactions


# Create your models here.
class CreditTransactionExportLog(models.Model):
    transaction_id = models.ForeignKey(CreditTransactions, on_delete=models.CASCADE),
    exported_at = models.DateTimeField(null=False)


class DebittTransactionExportLog(models.Model):
    transaction_id = models.ForeignKey(DebitTransactions, on_delete=models.CASCADE),
    exported_at = models.DateTimeField(null=False)
