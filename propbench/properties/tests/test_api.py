"""
Unit tests for the Property API views.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from properties.models import Property
from dictionaries.models import PropertyDictionary

User = get_user_model()


class PropertyAPITests(APITestCase):
    """Test case for the Property API"""
    
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
        
        # Add a name to the property
        self.property.names.create(
            name='Test Property',
            language='en-EN'
        )
    
    def test_list_properties(self):
        """Test retrieving a list of properties"""
        url = reverse('api-property-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_property(self):
        """Test retrieving a single property"""
        url = reverse('api-property-detail', args=[self.property.guid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['guid'], str(self.property.guid))
    
    def test_create_property(self):
        """Test creating a new property"""
        url = reverse('api-property-list')
        data = {
            'data_type': 'integer',
            'dictionary': str(self.dictionary.guid),
            'names': [
                {
                    'name': 'New Property',
                    'language': 'en-EN'
                }
            ],
            'definitions': [
                {
                    'definition': 'This is a test property',
                    'language': 'en-EN'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 2)
        self.assertEqual(Property.objects.last().names.first().name, 'New Property')
    
    def test_update_property(self):
        """Test updating an existing property"""
        url = reverse('api-property-detail', args=[self.property.guid])
        data = {
            'data_type': 'boolean',
            'names': [
                {
                    'name': 'Updated Property',
                    'language': 'en-EN'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.data_type, 'boolean')
        self.assertEqual(self.property.names.first().name, 'Updated Property')
    
    def test_delete_property(self):
        """Test deleting a property"""
        url = reverse('api-property-detail', args=[self.property.guid])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Property.objects.count(), 0)
    
    def test_property_with_default_dictionary(self):
        """Test creating a property without specifying dictionary uses default"""
        url = reverse('api-property-list')
        data = {
            'data_type': 'string',
            'names': [
                {
                    'name': 'Auto Dictionary Property',
                    'language': 'en-EN'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.last().dictionary, self.dictionary)
    
    def test_filter_properties_by_dictionary(self):
        """Test filtering properties by dictionary"""
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
        second_prop = Property.objects.create(
            data_type='integer',
            dictionary=second_dict,
            created_by=self.user,
            updated_by=self.user
        )
        second_prop.names.create(
            name='Second Dict Property',
            language='en-EN'
        )
        
        # Filter by first dictionary
        url = reverse('api-property-list')
        response = self.client.get(url, {'dictionary': str(self.dictionary.guid)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['guid'], str(self.property.guid))
        
        # Filter by second dictionary
        response = self.client.get(url, {'dictionary': str(second_dict.guid)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['guid'], str(second_prop.guid))
