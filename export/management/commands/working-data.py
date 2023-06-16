import time

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Complete environment setup'

    def add_arguments(self, parser):
        # Add any additional arguments here if needed
        pass

    def handle(self, *args, **options):
        # Your command logic goes here
        # You can call other management functions using `call_command`

        self.stdout.write('Starting working data setup...')

        # Reset the ELastic and DB contents
        call_command('clear-data')

        self.stdout.write('Clearing data handled')

        # create users
        call_command('generate-users', '1000')
        self.stdout.write('New users generated...')

        # create bank accounts
        call_command('generate-bankaccounts', '6')
        self.stdout.write('Bank accounts generated...')

        # create transactions
        call_command('generate-transactions', '3')
        self.stdout.write('Transactions generated...')

        # create activities
        call_command('generate-activities', '3')
        self.stdout.write('Activities generated...')

        # write the export file
        call_command('export-to-json')
        self.stdout.write('Records exported! We are done!')

        time.sleep(60)

        # start the real time generation of data
        call_command('real-time', '180')
        self.stdout.write('Running real time data generation - stand by....')