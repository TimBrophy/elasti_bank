from accounts.models import CustomUser, IncomeLevel
from django.core.management.base import BaseCommand
from mimesis import Person
from mimesis.locales import Locale
from mimesis.enums import Gender
import random
import string


class Command(BaseCommand):
    help = 'Generate random users'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):
        person = Person(Locale.EN)
        count = kwargs['count']

        for i in range(count):
            # define the users' income level
            income_level = random.randint(1, 8)
            if income_level >= 7:
                income_category = IncomeLevel.objects.get(id=3)
            elif 3 <= income_level <= 6:
                income_category = IncomeLevel.objects.get(id=2)
            else:
                income_category = IncomeLevel.objects.get(id=1)
            username = person.username() + "_" + str(random.randint(10, 20000))
            first_name = person.first_name()
            last_name = person.last_name()
            email = person.email()
            password = random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

            CustomUser.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email,
                                           password=password, income_level=income_category)
