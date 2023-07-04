"""config URL Configuration

The `urlpatterns` list routes URLs to views.py. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views.py
    1. Add an import:  from my_app import views.py
    2. Add a URL to urlpatterns:  path('', views.py.home, name='home')
Class-based views.py
    1. Add an import:  from other_app.views.py import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from activity.views import activity_home
from bankaccounts.views import bankaccounts_home,bankaccount_application, success_page_view
from transactions.views import debit_transaction, debit_success, transaction_detail, money_transfer, transaction_history
from uxtools.views import transactions_map, symantec_search, chat_interface, reset_data_view, gen_ai_search
from public.views import home
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('my-activity/', activity_home, name='my-activity'),
    path('my-bank-accounts/', bankaccounts_home, name='my-bank-accounts'),
    path('my-transactions/<id>', transaction_history, name='my-transactions'),
    path('bank-account-application/', bankaccount_application, name='bank-account-application'),
    path('bank-account-application/success/', success_page_view, name='success'),
    path('transfer-money/', money_transfer, name='transfer-money'),
    path('transfer-money/debit-success/<id>', debit_success, name='debit-success'),
    path('send-money/', debit_transaction, name='send-money'),
    path('send-money/debit-success/<id>', debit_success, name='debit-success'),
    path('my-transactions/transaction-detail/<id>/<value>', transaction_detail, name='transaction-detail'),
    path('uxtools/search', symantec_search, name='search-transactions'),
    path('uxtools/genai-search', gen_ai_search, name='genai-search-transactions'),
    path('transactions-map/', transactions_map, name='transactions-map'),
    path('chat/', chat_interface, name='chat'),
    path('reset-data/', reset_data_view, name='reset_data'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)