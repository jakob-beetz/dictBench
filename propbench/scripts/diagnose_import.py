#!/usr/bin/env python
"""
Diagnostic script to check dictionary and import status
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

from django.contrib.auth import get_user_model
from dictionaries.models import PropertyDictionary

User = get_user_model()

def diagnose_import_issue():
    """Diagnose why the import form is showing 'please select a dictionary'."""
    print("🔍 PropBench Import Diagnostic")
    print("=" * 50)
    
    # Check users
    user_count = User.objects.count()
    admin_users = User.objects.filter(is_superuser=True)
    print(f"👤 Users: {user_count} total, {admin_users.count()} admins")
    
    if admin_users.exists():
        print(f"   • Admin users: {', '.join([u.username for u in admin_users])}")
    
    # Check dictionaries
    dict_count = PropertyDictionary.objects.count()
    print(f"📚 Dictionaries: {dict_count}")
    
    if dict_count == 0:
        print("   ❌ NO DICTIONARIES FOUND!")
        print("   📝 This is likely why you're getting 'please select a dictionary'")
        print("   🔧 Fix: Run 'python manage.py create_test_dictionaries'")
    else:
        print("   ✓ Available dictionaries:")
        for d in PropertyDictionary.objects.all():
            print(f"      • ID {d.id}: {d.name} ({d.description})")
    
    # Check if we can create a test dictionary
    print(f"\n🧪 Testing dictionary creation...")
    try:
        if admin_users.exists():
            test_user = admin_users.first()
            test_dict, created = PropertyDictionary.objects.get_or_create(
                name='Test Dictionary - Diagnostic',
                defaults={
                    'description': 'Created by diagnostic script',
                    'created_by': test_user,
                    'updated_by': test_user
                }
            )
            if created:
                print(f"   ✓ Successfully created test dictionary: {test_dict.name}")
            else:
                print(f"   • Test dictionary already exists: {test_dict.name}")
        else:
            print("   ❌ No admin users found - cannot create test dictionary")
    except Exception as e:
        print(f"   ❌ Error creating test dictionary: {e}")
    
    # Final recommendations
    print(f"\n🎯 Recommendations:")
    if dict_count == 0:
        print("   1. Run: python manage.py create_test_dictionaries")
        print("   2. Restart your Django server")
        print("   3. Try the import again")
    else:
        print("   1. Check browser console for JavaScript errors")
        print("   2. Check Django server console for debug output")
        print("   3. Try clearing browser cache")
    
    print(f"\n📊 Current Status:")
    print(f"   • Total dictionaries: {PropertyDictionary.objects.count()}")
    print(f"   • Total users: {User.objects.count()}")
    
    # Test the form context
    print(f"\n🔧 Testing form context (similar to admin view)...")
    try:
        context_dicts = PropertyDictionary.objects.all()
        print(f"   • Dictionaries in context: {context_dicts.count()}")
        print(f"   • Context dict list: {list(context_dicts.values('id', 'name'))}")
    except Exception as e:
        print(f"   ❌ Error getting context dictionaries: {e}")

if __name__ == '__main__':
    diagnose_import_issue()