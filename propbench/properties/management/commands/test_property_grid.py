from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary
from properties.models import Property, PropertyName

User = get_user_model()

class Command(BaseCommand):
    help = 'Quick test to check property grid data'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Property Grid Diagnostic')
        self.stdout.write('=' * 50)
        
        # Check users
        user_count = User.objects.count()
        admin_count = User.objects.filter(is_superuser=True).count()
        self.stdout.write(f'Users: {user_count} (Admins: {admin_count})')
        
        # Check dictionaries
        dict_count = PropertyDictionary.objects.count()
        self.stdout.write(f'Dictionaries: {dict_count}')
        
        if dict_count > 0:
            for d in PropertyDictionary.objects.all()[:3]:
                self.stdout.write(f'  - {d.name} (ID: {d.pk})')
        
        # Check properties
        prop_count = Property.objects.count()
        self.stdout.write(f'Properties: {prop_count}')
        
        if prop_count > 0:
            for p in Property.objects.all()[:3]:
                names = p.names.all()
                name_str = names.first().name if names.exists() else f'Property {p.pk}'
                self.stdout.write(f'  - {name_str} ({p.data_type})')
        
        # Check URLs
        self.stdout.write('\n🌐 URL Test:')
        try:
            from django.urls import reverse
            grid_url = reverse('admin:properties_property_grid_manager')
            self.stdout.write(f'Grid Manager URL: {grid_url}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'URL Error: {e}'))
        
        # Create minimal test data if none exists
        if dict_count == 0:
            self.stdout.write('\n🆕 Creating minimal test data...')
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
                self.stdout.write('✓ Created admin user')
            
            # Create test dictionary
            test_dict = PropertyDictionary.objects.create(
                name='Test Dictionary',
                description='Test dictionary for grid',
                created_by=admin_user,
                updated_by=admin_user
            )
            self.stdout.write('✓ Created test dictionary')
            
            # Create test property
            test_prop = Property.objects.create(
                dictionary=test_dict,
                data_type='string',
                unit_of_measurement='',
                status='active',
                created_by=admin_user,
                updated_by=admin_user
            )
            
            PropertyName.objects.create(
                property=test_prop,
                name='Test Property',
                language='en',
                created_by=admin_user,
                updated_by=admin_user
            )
            self.stdout.write('✓ Created test property')
        
        self.stdout.write(f'\n✅ Diagnostic complete!')
        self.stdout.write('Now try the grid at: /admin/properties/property/grid-manager/')