#!/usr/bin/env python
"""
Quick test script to verify the import form is working
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propbench.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary

User = get_user_model()

def test_import_views():
    """Test that the import views are accessible and form data is processed correctly."""
    print("🧪 Testing Import Views")
    print("=" * 40)
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@test.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create test dictionary
    dictionary, created = PropertyDictionary.objects.get_or_create(
        name='Test Dictionary',
        defaults={
            'description': 'Test dictionary for import testing',
            'created_by': user,
            'updated_by': user
        }
    )
    
    # Create test client and login
    client = Client()
    login_success = client.login(username='testuser', password='testpass123')
    
    print(f"✓ Login successful: {login_success}")
    print(f"✓ Test dictionary: {dictionary.name} (ID: {dictionary.id})")
    
    # Test GET requests
    print("\n📄 Testing GET requests:")
    
    # Test basic CSV import view
    response = client.get('/admin/properties/property/import-csv/')
    print(f"Basic CSV Import: {response.status_code} ({'OK' if response.status_code == 200 else 'FAIL'})")
    
    # Test ISO 16757 import view  
    response = client.get('/admin/properties/property/import-iso16757/')
    print(f"ISO 16757 Import: {response.status_code} ({'OK' if response.status_code == 200 else 'FAIL'})")
    
    # Test property list view
    response = client.get('/admin/properties/property/')
    print(f"Property List: {response.status_code} ({'OK' if response.status_code == 200 else 'FAIL'})")
    
    # Test form submission validation
    print("\n📝 Testing form validation:")
    
    # Test POST without data
    response = client.post('/admin/properties/property/import-iso16757/', {})
    print(f"Empty POST: {response.status_code} (Should redirect: 302)")
    
    # Test POST with missing CSV
    response = client.post('/admin/properties/property/import-iso16757/', {
        'dictionary_id': dictionary.id
    })
    print(f"Missing CSV: {response.status_code} (Should redirect: 302)")
    
    # Test POST with missing dictionary
    response = client.post('/admin/properties/property/import-iso16757/', {
        'csv_file': 'test.csv'  # This won't work without actual file, but tests validation
    })
    print(f"Missing Dictionary: {response.status_code} (Should redirect: 302)")
    
    print(f"\n📊 Database State:")
    print(f"   Users: {User.objects.count()}")
    print(f"   Dictionaries: {PropertyDictionary.objects.count()}")
    
    print("\n✅ Basic tests completed!")
    print("\n🔧 Next steps:")
    print("   1. Start the development server: python manage.py runserver")
    print("   2. Go to: http://localhost:8000/admin/properties/property/")
    print("   3. Click 'Import ISO 16757' button")
    print("   4. Select a dictionary and upload your CSV file")

if __name__ == '__main__':
    test_import_views()