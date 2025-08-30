#!/usr/bin/env python
"""
Quick dictionary creation script - Run this first!
"""
import os
import sys
import django
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propbench.settings')
django.setup()

from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary

User = get_user_model()

def create_dictionaries():
    print("🔧 Quick Dictionary Setup")
    print("=" * 30)
    
    # Get or create admin user
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
            print("✓ Created admin user")
        else:
            print(f"✓ Using existing admin: {user.username}")
    except Exception as e:
        print(f"❌ Error with user: {e}")
        return
    
    # Create dictionaries
    dict_names = [
        "Heat Pumps ISO 16757",
        "General Properties", 
        "Building Components"
    ]
    
    created = 0
    for name in dict_names:
        dictionary, was_created = PropertyDictionary.objects.get_or_create(
            name=name,
            defaults={
                'description': f'Test dictionary: {name}',
                'created_by': user,
                'updated_by': user
            }
        )
        if was_created:
            created += 1
            print(f"✓ Created: {name} (ID: {dictionary.id})")
        else:
            print(f"• Exists: {name} (ID: {dictionary.id})")
    
    total = PropertyDictionary.objects.count()
    print(f"\n📊 Summary: {total} total dictionaries ({created} created)")
    
    print(f"\n🎯 All available dictionaries:")
    for d in PropertyDictionary.objects.all():
        print(f"   ID {d.id}: {d.name}")
    
    print(f"\n✅ Ready! Go to: /admin/properties/property/import-iso16757/")

if __name__ == '__main__':
    create_dictionaries()