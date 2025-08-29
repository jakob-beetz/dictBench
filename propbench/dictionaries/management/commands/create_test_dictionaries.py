from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default test dictionary for import testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to assign as creator (defaults to first superuser or creates admin)',
            default=None
        )
    
    def handle(self, *args, **options):
        # Get or create a user for the dictionaries
        username = options.get('user')
        
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" not found')
                )
                return
        else:
            # Try to get first superuser
            user = User.objects.filter(is_superuser=True).first()
            
            if not user:
                # Create a default admin user
                user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created default admin user: {user.username} (password: admin123)')
                )
        
        # Create test dictionary
        dictionary, created = PropertyDictionary.objects.get_or_create(
            name='Test Dictionary',
            defaults={
                'description': 'Default test dictionary for CSV imports',
                'is_default': True,
                'created_by': user,
                'updated_by': user,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created default dictionary: {dictionary.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✓ Dictionary already exists: {dictionary.name}')
            )
        
        # Also create Heat Pumps dictionary for the ISO 16757 data
        hp_dictionary, hp_created = PropertyDictionary.objects.get_or_create(
            name='Heat Pumps',
            defaults={
                'description': 'ISO 16757 Heat Pump Properties Dictionary',
                'is_default': False,
                'created_by': user,
                'updated_by': user,
            }
        )
        
        if hp_created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Heat Pumps dictionary: {hp_dictionary.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✓ Heat Pumps dictionary already exists: {hp_dictionary.name}')
            )
        
        total_dicts = PropertyDictionary.objects.count()
        self.stdout.write(f'Total dictionaries: {total_dicts}')
        self.stdout.write(f'Using user: {user.username} (ID: {user.id})')
        
        if not options.get('user') and user.username == 'admin':
            self.stdout.write(
                self.style.WARNING(
                    'Note: Created default admin user with password "admin123". '
                    'Please change this password in production!'
                )
            )