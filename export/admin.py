from django.contrib import admin
from export.models import DebittTransactionExportLog, CreditTransactionExportLog

# Register your models here.
admin.site.register(DebittTransactionExportLog)
admin.site.register(CreditTransactionExportLog)