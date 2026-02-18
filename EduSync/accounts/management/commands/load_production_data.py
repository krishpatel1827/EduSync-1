"""
Management command to load production data from fixtures.
Only loads if the database is empty (no institutions exist).
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from institution.models import Institution
import os


class Command(BaseCommand):
    help = 'Load production data from fixtures if database is empty'

    def handle(self, *args, **options):
        # Check if data already exists
        if Institution.objects.exists():
            self.stdout.write(self.style.SUCCESS(
                'Data already exists in database. Skipping fixture load.'
            ))
            return

        # Find the fixture file using Django's BASE_DIR
        fixture_path = os.path.join(settings.BASE_DIR, 'fixtures', 'production_data.json')
        
        self.stdout.write(f'Looking for fixture at: {fixture_path}')

        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.WARNING(
                f'Fixture file not found: {fixture_path}'
            ))
            return

        self.stdout.write('Loading production data from fixtures...')
        
        try:
            call_command('loaddata', fixture_path, verbosity=2)
            self.stdout.write(self.style.SUCCESS(
                'Production data loaded successfully!'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading fixture: {e}'))
