from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test dictionaries for import testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to assign as creator (default: admin)',
            default='admin'
        )

    def handle(self, *args, **options):
        username = options['user']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Create the user if it doesn't exist
            user = User.objects.create_superuser(
                username=username,
                email=f'{username}@test.com',
                password='admin123'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created superuser: {username}')
            )

        # Create test dictionaries
        dictionaries_data = [
            {
                'name': 'Heat Pumps ISO 16757',
                'description': 'ISO 16757 Heat Pump Properties Dictionary for testing import functionality'
            },
            {
                'name': 'General Properties',
                'description': 'General property dictionary for basic property data'
            },
            {
                'name': 'Building Components',
                'description': 'Dictionary for building component properties and specifications'
            }
        ]

        created_count = 0
        existing_count = 0

        for dict_data in dictionaries_data:
            dictionary, created = PropertyDictionary.objects.get_or_create(
                name=dict_data['name'],
                defaults={
                    'description': dict_data['description'],
                    'created_by': user,
                    'updated_by': user
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created dictionary: {dictionary.name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'• Dictionary already exists: {dictionary.name}')
                )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Dictionary creation completed!\n'
                f'  • Created: {created_count}\n'
                f'  • Already existed: {existing_count}\n'
                f'  • Total available: {PropertyDictionary.objects.count()}'
            )
        )
        
        # List all available dictionaries
        self.stdout.write('\n📚 Available Dictionaries:')
        for dictionary in PropertyDictionary.objects.all():
            self.stdout.write(f'  • ID {dictionary.id}: {dictionary.name}')
            
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🚀 Ready for import testing!\n'
                f'   • Go to: /admin/properties/property/\n'
                f'   • Click "Import ISO 16757"\n'
                f'   • Select a dictionary and upload CSV file'
            )
        )