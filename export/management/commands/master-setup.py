from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import os
import shutil
import subprocess
from django.conf import settings
from django.db import connection

def delete_migrations(directory):
    for root, dirs, files in os.walk(directory):
        if 'migrations' in dirs:
            migrations_dir = os.path.join(root, 'migrations')
            migration_files = os.listdir(migrations_dir)

            for file in migration_files:
                if file != '__init__.py' and not file.startswith('0001_initial'):
                    file_path = os.path.join(migrations_dir, file)
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")

class Command(BaseCommand):
    help = 'Complete environment setup'

    def add_arguments(self, parser):
        # Add any additional arguments here if needed
        pass

    def handle(self, *args, **options):
        # Your command logic goes here
        # You can call other management functions using `call_command`

        self.stdout.write('Starting environment setup...')

        # Reset the ELastic and DB contents
        call_command('clear-data')
        # Remove migrations files

        # Specify the directory of your Django project
        django_project_directory = '/timb/Dev/elasti_bank'

        # Call the function to delete the migrations
        delete_migrations(django_project_directory)

        # Rebuild the database structure migrations
        call_command('makemigrations')
        # Perform the rebuild
        call_command('migrate')
        # Populate the database with master data
        call_command('populate-retailers')
        call_command('master-data')

        self.stdout.write('Finished environment setup...')
