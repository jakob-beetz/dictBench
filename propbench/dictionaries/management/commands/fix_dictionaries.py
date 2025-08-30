from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix PropertyDictionary model issues and create test data'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Fixing PropertyDictionary Issues')
        self.stdout.write('=' * 50)
        
        # Check the model structure
        try:
            model_meta = PropertyDictionary._meta
            self.stdout.write(f'Model: {model_meta.model_name}')
            self.stdout.write(f'Primary Key Field: {model_meta.pk.name} (type: {model_meta.pk.__class__.__name__})')
            
            # Check if model uses UUID
            if hasattr(model_meta.pk, 'default'):
                self.stdout.write(f'PK Default: {model_meta.pk.default}')
            
            # List all fields
            self.stdout.write('\nModel Fields:')
            for field in model_meta.fields:
                self.stdout.write(f'  - {field.name}: {field.__class__.__name__}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error inspecting model: {e}'))
            return
        
        # Check existing dictionaries
        self.stdout.write('\nExisting Dictionaries:')
        try:
            dictionaries = PropertyDictionary.objects.all()
            self.stdout.write(f'Count: {dictionaries.count()}')
            
            for d in dictionaries:
                try:
                    pk_value = d.pk
                    self.stdout.write(f'  - Name: "{d.name}" | PK: {pk_value} (type: {type(pk_value)})')
                    
                    # Try to access .id attribute
                    try:
                        id_value = d.id
                        self.stdout.write(f'    .id = {id_value}')
                    except AttributeError:
                        self.stdout.write(self.style.WARNING('    .id attribute does not exist'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error accessing dictionary: {e}'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error querying dictionaries: {e}'))
        
        # Get or create admin user
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
                self.stdout.write('✓ Created admin user')
            else:
                self.stdout.write(f'✓ Using admin user: {admin_user.username}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error with admin user: {e}'))
            return
        
        # Clean up and recreate dictionaries
        self.stdout.write('\n🧹 Cleaning up existing dictionaries...')
        try:
            deleted_count, _ = PropertyDictionary.objects.all().delete()
            self.stdout.write(f'Deleted {deleted_count} existing dictionaries')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error deleting dictionaries: {e}'))
        
        # Create new dictionaries
        self.stdout.write('\n🆕 Creating new dictionaries...')
        test_dictionaries = [
            {
                'name': 'ISO 16757 Heat Pumps',
                'description': 'Heat pump properties from ISO 16757 standard'
            },
            {
                'name': 'Wärmepumpen',
                'description': 'German heat pump properties'
            },
            {
                'name': 'Test Dictionary',
                'description': 'Test dictionary for import testing'
            }
        ]
        
        created_count = 0
        for dict_data in test_dictionaries:
            try:
                dictionary = PropertyDictionary.objects.create(
                    name=dict_data['name'],
                    description=dict_data['description'],
                    created_by=admin_user,
                    updated_by=admin_user
                )
                
                self.stdout.write(f'✓ Created: "{dictionary.name}" (PK: {dictionary.pk})')
                created_count += 1
                
                # Verify the dictionary can be accessed properly
                try:
                    retrieved = PropertyDictionary.objects.get(pk=dictionary.pk)
                    self.stdout.write(f'  ✓ Verified: Can retrieve by PK')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Cannot retrieve by PK: {e}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to create "{dict_data["name"]}": {e}'))
        
        self.stdout.write(f'\n🎉 Summary:')
        self.stdout.write(f'  Created: {created_count} dictionaries')
        self.stdout.write(f'  Total: {PropertyDictionary.objects.count()} dictionaries')
        
        self.stdout.write(f'\n✅ PropertyDictionary fix completed!')
        self.stdout.write(f'   Now try the import again at: /admin/properties/property/import-iso16757/')
        
        # Final verification
        self.stdout.write(f'\n🔍 Final Verification:')
        for d in PropertyDictionary.objects.all():
            self.stdout.write(f'  Dictionary: "{d.name}" | PK: {d.pk} | Type: {type(d.pk)}')