"""
Unit tests for the PropertyGroup API views.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from groups.models import PropertyGroup, PropertyGroupMembership
from properties.models import Property
from dictionaries.models import PropertyDictionary

User = get_user_model()


class PropertyGroupAPITests(APITestCase):
    """Test case for the PropertyGroup API"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a test dictionary
        self.dictionary = PropertyDictionary.objects.create(
            name='Test Dictionary',
            registration_authority='Test Authority',
            version='1.0',
            status='active',
            is_default=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a test property
        self.property = Property.objects.create(
            data_type='string',
            dictionary=self.dictionary,
            created_by=self.user,
            updated_by=self.user
        )
        self.property.names.create(
            name='Test Property',
            language='en-EN'
        )
        
        # Create a test group
        self.group = PropertyGroup.objects.create(
            name='Test Group',
            type='class',
            dictionary=self.dictionary,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Add the property to the group
        PropertyGroupMembership.objects.create(
            group=self.group,
            property=self.property,
            order=0,
            is_required=True
        )
    
    def test_list_groups(self):
        """Test retrieving a list of groups"""
        url = reverse('api-group-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_group(self):
        """Test retrieving a single group"""
        url = reverse('api-group-detail', args=[self.group.guid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['guid'], str(self.group.guid))
    
    def test_create_group(self):
        """Test creating a new group"""
        url = reverse('api-group-list')
        data = {
            'name': 'New Group',
            'type': 'domain',
            'description': 'This is a test group',
            'dictionary': str(self.dictionary.guid),
            'names': [
                {
                    'name': 'New Group',
                    'language': 'en-EN'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PropertyGroup.objects.count(), 2)
        self.assertEqual(PropertyGroup.objects.last().name, 'New Group')
    
    def test_update_group(self):
        """Test updating an existing group"""
        url = reverse('api-group-detail', args=[self.group.guid])
        data = {
            'name': 'Updated Group',
            'type': 'template'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Updated Group')
        self.assertEqual(self.group.type, 'template')
    
    def test_delete_group(self):
        """Test deleting a group"""
        url = reverse('api-group-detail', args=[self.group.guid])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PropertyGroup.objects.count(), 0)
    
    def test_group_with_default_dictionary(self):
        """Test creating a group without specifying dictionary uses default"""
        url = reverse('api-group-list')
        data = {
            'name': 'Auto Dictionary Group',
            'type': 'class'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PropertyGroup.objects.last().dictionary, self.dictionary)
    
    def test_add_properties_to_group(self):
        """Test adding properties to a group"""
        # Create a second property
        second_property = Property.objects.create(
            data_type='integer',
            dictionary=self.dictionary,
            created_by=self.user,
            updated_by=self.user
        )
        second_property.names.create(
            name='Second Property',
            language='en-EN'
        )
        
        url = reverse('api-group-add-properties', args=[self.group.guid])
        data = {
            'property_ids': [str(second_property.guid)],
            'is_required': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.group.properties.count(), 2)
        self.assertTrue(self.group.properties.filter(guid=second_property.guid).exists())
    
    def test_remove_properties_from_group(self):
        """Test removing properties from a group"""
        url = reverse('api-group-remove-properties', args=[self.group.guid])
        data = {
            'property_ids': [str(self.property.guid)]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.group.properties.count(), 0)
    
    def test_filter_groups_by_dictionary(self):
        """Test filtering groups by dictionary"""
        # Create a second dictionary
        second_dict = PropertyDictionary.objects.create(
            name='Second Dictionary',
            registration_authority='Test Authority',
            version='1.0',
            status='active',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a group in the second dictionary
        second_group = PropertyGroup.objects.create(
            name='Second Dict Group',
            type='domain',
            dictionary=second_dict,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Filter by first dictionary
        url = reverse('api-group-list')
        response = self.client.get(url, {'dictionary': str(self.dictionary.guid)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['guid'], str(self.group.guid))
        
        # Filter by second dictionary
        response = self.client.get(url, {'dictionary': str(second_dict.guid)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['guid'], str(second_group.guid))
        
    def test_properties_from_different_dictionary(self):
        """Test cannot add properties from a different dictionary to a group"""
        # Create a second dictionary
        second_dict = PropertyDictionary.objects.create(
            name='Second Dictionary',
            registration_authority='Test Authority',
            version='1.0',
            status='active',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a property in the second dictionary
        second_property = Property.objects.create(
            data_type='integer',
            dictionary=second_dict,
            created_by=self.user,
            updated_by=self.user
        )
        
        url = reverse('api-group-add-properties', args=[self.group.guid])
        data = {
            'property_ids': [str(second_property.guid)],
            'is_required': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not in the same dictionary', response.data['detail'])
