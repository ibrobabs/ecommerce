from django.test import TestCase,SimpleTestCase
from contact.forms import contactView
from contact.models import contactForm
from datetime import datetime, timedelta


class UserModelTest(TestCase):

	@classmethod
	def setUpTestData(cls):
		contactForm(email="test@dummy.com", name="test").save()
		contactForm(email="j@j.com", name="jj").save()
		cls.firstUser = contactForm(
			email="first@first.com",
			name="first",
			timestamp=datetime.today() + timedelta(days=2)
		)
		cls.firstUser.save()

	def test_contactform_str_returns_email(self):
		self.assertEqual("first@first.com", str(self.firstUser))

	def test_ordering(self):
		contacts = contactForm.objects.all()
		self.assertEqual(self.firstUser, contacts[0])

class ContactViewTests(SimpleTestCase):

	def test_displayed_fields(self):
		expected_fields = ['name', 'email', 'topic', 'message']
		self.assertEqual(contactView.Meta.fields, expected_fields)