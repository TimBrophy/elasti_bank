from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import BankAccount, BankAccountApplications
from .forms import MyBankAccountApplicationForm
from accounts.models import CustomUser
from django.utils import timezone
from elasticsearch import Elasticsearch
from django.conf import settings
import uuid
import googlemaps

def bankaccounts_home(request):
    # Retrieve bank accounts and applications data from models
    account_list = BankAccount.objects.filter(user=request.user)
    application_list = BankAccountApplications.objects.filter(user=request.user)

    context = {
        'account_list': account_list,
        'application_list': application_list,
    }

    return render(request, 'bankaccounts/home.html', context)


@login_required
def bankaccount_application(request):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    if request.method == 'POST':
        form = MyBankAccountApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            # Save form data
            application_record = form.save(commit=False)
            # Redirect to success page
            print(request.method)  # Print request method to console
            es = Elasticsearch(
                cloud_id=settings.ES_CLOUD_ID,
                http_auth=(settings.ES_USER, settings.ES_PASS)

            )
            user_record = CustomUser.objects.get(id=application_record.user.id)
            record_id = uuid.uuid4()
            geocode_result = gmaps.geocode('{}, {}, {}, {}, {}'.format(application_record.streetaddress1, application_record.streetaddress2, application_record.suburb, application_record.province, application_record.country))
            lat = geocode_result[0]['geometry']['location']['lat']
            lon = geocode_result[0]['geometry']['location']['lng']
            document = {
                'id': record_id,
                'timestamp': application_record.created_at,
                'User id': application_record.user.id,
                'Username': user_record.username,
                'Full name': "{} {}".format(user_record.first_name, user_record.last_name),
                'Bank AccountType': application_record.bankaccounttype.typename,
                'Contact number': application_record.contactnumber,
                'Street Address 1': application_record.streetaddress1,
                'Street Address 2': application_record.streetaddress2,
                'Suburb': application_record.suburb,
                'Province': application_record.province,
                'Country': application_record.country,
                'Gross income': application_record.grossincome,
                'Expenses': application_record.expenses,
                'Status': application_record.status.statusname,
                'location': {
                    'lat': lat,
                    'lon': lon
                }
            }
            response = es.index(index="account-applications", id=record_id, document=document)
            print(response)
            application_record.save()
            return redirect('success')
    else:
        form = MyBankAccountApplicationForm(user=request.user)
    return render(request, 'bankaccounts/application.html', {'form': form})


def success_page_view(request):
    return render(request, 'bankaccounts/success_page.html')
