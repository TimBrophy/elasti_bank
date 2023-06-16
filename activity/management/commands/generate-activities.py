from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from activity.models import Activity, ActivityType
import random
import random_address
import pytz
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from mimesis import Address, Person, Finance, Text, Code
from mimesis.locales import Locale

text = Text(locale=Locale.EN)


def generate_coordinates():
    address = random_address.real_random_address()
    latitude = address['coordinates']['lat']
    longitude = address['coordinates']['lng']
    coordinates_string = "{'longitude' :" + str(longitude) + ", 'latitude' :" + str(latitude) + "}"
    return coordinates_string


def random_created_at(number_of_months):
    utc = pytz.utc
    working_month = datetime.now(tz=timezone.utc) - relativedelta(months=number_of_months)
    year = working_month.year
    month = working_month.month

    last_day = datetime(year, month, 1) + relativedelta(months=1) - timedelta(days=1)

    random_datetime = datetime(year, month, 1) + timedelta(
        days=random.randint(0, (last_day - datetime(year, month, 1)).days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59))
    random_datetime_tz = utc.localize(random_datetime)
    return random_datetime_tz


class Command(BaseCommand):
    help = 'Generate random bank accounts and account applications'

    def add_arguments(self, parser):
        parser.add_argument('number-of-months', type=int,
                            help='Indicates the number of months to build activities for')

    def handle(self, *args, **kwargs):
        account_users = CustomUser.objects.exclude(id=1)
        total_months = kwargs['number-of-months']

        for i in range(1, total_months):
            for a in account_users:
                number_of_activities = random.randrange(1, 50)
                counter = 0
                while counter < number_of_activities:
                    description = text.quote()
                    created_at = random_created_at(i)
                    rand_location = generate_coordinates()

                    random_activity_type = random.randrange(1, 1000)
                    if random_activity_type < 50:
                        activity_type = ActivityType.objects.filter(name="Retail bank").first()

                    elif 50 <= random_activity_type <= 250:
                        activity_type = ActivityType.objects.filter(name="ATM").first()

                    elif 250 <= random_activity_type <= 500:
                        activity_type = ActivityType.objects.filter(name="Call center").first()

                    else:
                        activity_type = ActivityType.objects.filter(name="Website").first()

                    Activity.objects.create(activitytype=activity_type, user=a, created_at=created_at,
                                            activity_log_message=description, location=rand_location)

                    counter = counter + 1
