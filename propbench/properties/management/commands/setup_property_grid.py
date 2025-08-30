from django.core.management.base import BaseCommand
from django.core.management import call_command
import subprocess
import sys

class Command(BaseCommand):
    help = 'Setup property grid dependencies and requirements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--install-deps',
            action='store_true',
            help='Install required Python packages',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔧 Setting up Property Grid Manager')
        self.stdout.write('=' * 50)
        
        if options['install_deps']:
            self.install_dependencies()
        
        self.check_dependencies()
        self.setup_demo_data()
        self.create_sample_physical_quantities()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Property Grid setup completed!'))
        self.stdout.write('')
        self.stdout.write('🎯 Next steps:')
        self.stdout.write('1. Go to /admin/properties/property/')
        self.stdout.write('2. Click "Grid Manager" button')
        self.stdout.write('3. Enjoy the advanced property management interface!')

    def install_dependencies(self):
        """Install required Python packages."""
        self.stdout.write('📦 Installing Python dependencies...')
        
        packages = [
            'fuzzywuzzy[speedup]',  # For fuzzy search
            'python-levenshtein',   # For faster fuzzy matching
        ]
        
        for package in packages:
            try:
                self.stdout.write(f'Installing {package}...')
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ])
                self.stdout.write(self.style.SUCCESS(f'✓ {package} installed'))
            except subprocess.CalledProcessError:
                self.stdout.write(self.style.WARNING(f'⚠ Failed to install {package}'))
                self.stdout.write('You may need to install manually:')
                self.stdout.write(f'pip install {package}')

    def check_dependencies(self):
        """Check if required dependencies are available."""
        self.stdout.write('🔍 Checking dependencies...')
        
        dependencies = {
            'fuzzywuzzy': 'Fuzzy string matching',
            'Levenshtein': 'Fast string comparison (optional but recommended)',
        }
        
        for package, description in dependencies.items():
            try:
                __import__(package)
                self.stdout.write(self.style.SUCCESS(f'✓ {package} - {description}'))
            except ImportError:
                self.stdout.write(self.style.WARNING(f'⚠ {package} missing - {description}'))
                if package == 'fuzzywuzzy':
                    self.stdout.write('  Run: pip install fuzzywuzzy[speedup]')
                elif package == 'Levenshtein':
                    self.stdout.write('  Run: pip install python-levenshtein')

    def setup_demo_data(self):
        """Create demo data for testing the grid."""
        self.stdout.write('🎭 Setting up demo data...')
        
        from accounts.models import User
        from dictionaries.models import PropertyDictionary
        from properties.models import Property, PropertyName, PhysicalQuantity
        
        # Get or create admin user
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    'admin', 'admin@propbench.com', 'admin123'
                )
                self.stdout.write('✓ Created admin user')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {e}'))
            return

        # Create demo dictionary
        demo_dict, created = PropertyDictionary.objects.get_or_create(
            name='Demo Grid Dictionary',
            defaults={
                'description': 'Demo dictionary for testing the property grid',
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        
        if created:
            self.stdout.write('✓ Created demo dictionary')

        # Create demo properties if none exist
        if Property.objects.count() < 5:
            demo_properties = [
                {
                    'data_type': 'real',
                    'unit': 'kW',
                    'status': 'active',
                    'names': [
                        {'name': 'Heat Output', 'language': 'en'},
                        {'name': 'Wärmeabgabe', 'language': 'de'},
                    ]
                },
                {
                    'data_type': 'real',
                    'unit': 'bar',
                    'status': 'active',
                    'names': [
                        {'name': 'Maximum Pressure', 'language': 'en'},
                        {'name': 'Maximaler Druck', 'language': 'de'},
                    ]
                },
                {
                    'data_type': 'string',
                    'unit': '',
                    'status': 'active',
                    'names': [
                        {'name': 'Manufacturer', 'language': 'en'},
                        {'name': 'Hersteller', 'language': 'de'},
                    ]
                },
                {
                    'data_type': 'integer',
                    'unit': 'years',
                    'status': 'draft',
                    'names': [
                        {'name': 'Warranty Period', 'language': 'en'},
                        {'name': 'Garantiezeit', 'language': 'de'},
                    ]
                },
                {
                    'data_type': 'boolean',
                    'unit': '',
                    'status': 'deprecated',
                    'names': [
                        {'name': 'Energy Star Certified', 'language': 'en'},
                        {'name': 'Energy Star Zertifiziert', 'language': 'de'},
                    ]
                },
            ]
            
            for prop_data in demo_properties:
                try:
                    # Create property
                    property_obj = Property.objects.create(
                        dictionary=demo_dict,
                        data_type=prop_data['data_type'],
                        unit_of_measurement=prop_data['unit'],
                        status=prop_data['status'],
                        created_by=admin_user,
                        updated_by=admin_user,
                    )
                    
                    # Create property names
                    for name_data in prop_data['names']:
                        PropertyName.objects.create(
                            property=property_obj,
                            name=name_data['name'],
                            language=name_data['language'],
                            created_by=admin_user,
                            updated_by=admin_user,
                        )
                    
                    self.stdout.write(f'✓ Created demo property: {prop_data["names"][0]["name"]}')
                    
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠ Error creating demo property: {e}'))

    def create_sample_physical_quantities(self):
        """Create sample physical quantities for fuzzy search testing."""
        self.stdout.write('⚡ Creating sample physical quantities...')
        
        from properties.models import PhysicalQuantity
        from accounts.models import User
        
        admin_user = User.objects.filter(is_superuser=True).first()
        
        sample_quantities = [
            {'name': 'Power', 'description': 'Rate of energy transfer'},
            {'name': 'Pressure', 'description': 'Force per unit area'},
            {'name': 'Temperature', 'description': 'Measure of thermal energy'},
            {'name': 'Flow Rate', 'description': 'Volume per unit time'},
            {'name': 'Efficiency', 'description': 'Ratio of useful output to input'},
            {'name': 'Voltage', 'description': 'Electric potential difference'},
            {'name': 'Current', 'description': 'Electric charge flow rate'},
            {'name': 'Frequency', 'description': 'Oscillations per unit time'},
        ]
        
        created_count = 0
        for qty_data in sample_quantities:
            qty, created = PhysicalQuantity.objects.get_or_create(
                name=qty_data['name'],
                defaults={
                    'description': qty_data['description'],
                    'created_by': admin_user,
                    'updated_by': admin_user,
                }
            )
            
            if created:
                created_count += 1
        
        self.stdout.write(f'✓ Created {created_count} physical quantities')

    def create_sample_urls(self):
        """Display sample URLs for testing."""
        self.stdout.write('')
        self.stdout.write('🔗 Available URLs:')
        self.stdout.write('Grid Manager: /admin/properties/property/grid-manager/')
        self.stdout.write('API Endpoints:')
        self.stdout.write('  - Grid Data: /admin/properties/property/api/grid-data/')
        self.stdout.write('  - Search Units: /admin/properties/property/api/search/units/')
        self.stdout.write('  - Search Quantities: /admin/properties/property/api/search/quantities/')
        self.stdout.write('  - Bulk Edit: /admin/properties/property/api/bulk-edit/')