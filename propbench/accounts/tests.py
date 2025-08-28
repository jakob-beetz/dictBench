from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """
    Tests for the custom User model.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            organization='Test Organization',
            job_title='Test Engineer',
            preferred_language='en-EN'
        )
    
    def test_user_creation(self):
        """
        Test that a user can be created with all the custom fields.
        """
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.organization, 'Test Organization')
        self.assertEqual(self.user.job_title, 'Test Engineer')
        self.assertEqual(self.user.preferred_language, 'en-EN')
        self.assertFalse(self.user.is_expert)
        self.assertIsNone(self.user.last_active)
        
    def test_expert_flag(self):
        """
        Test that a user can be assigned expert privileges.
        """
        self.user.is_expert = True
        self.user.save()
        
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertTrue(updated_user.is_expert)
