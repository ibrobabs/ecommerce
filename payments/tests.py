from django.shortcuts import render, render_to_response
import django_ecommerce.settings as settings
from payments.views import soon, register
from django.test import TestCase, RequestFactory
from payments.models import User
from payments.forms import SigninForm, UserForm
from django.core.urlresolvers import resolve
from .views import sign_in, sign_out
from django import forms
import unittest
from unittest.mock import patch
import mock


class ViewTesterMixin(object):

  @classmethod
  def setupViewTester(cls, url, view_func, expected_html, status_code=200, session={}):
    # super(ViewTesterMixin, cls).setUpViewTester()

    request_factory = RequestFactory()
    cls.request = request_factory.get(url)
    cls.request.session = session
    cls.status_code = status_code
    cls.url = url
    cls.view_func = staticmethod(view_func)
    cls.expected_html = expected_html

  def test_resolves_to_correct_view(self):
    test_view = resolve(self.url)
    self.assertEquals(test_view.func, self.view_func)

  def test_returns_appropriate_respose_code(self):
    resp = self.view_func(self.request)
    self.assertEquals(resp.status_code, self.status_code)

  def test_returns_correct_html(self):
    resp = self.view_func(self.request)
    self.assertEquals(resp.content, self.expected_html)

class SignOutPageTests(TestCase, ViewTesterMixin):

    @classmethod
    def setUpClass(cls):
        super(SignOutPageTests, cls).setUpClass()
        ViewTesterMixin.setupViewTester(
            '/sign_out',
            sign_out,
            b"",
            status_code=302,
            session={"user": "dummy"},
        )

class UserModelTest(TestCase):

	@classmethod
	def setTestData(cls):
		cls.test_user = User(email="j@j.com", name='test user')
		cls.test_user.save()

	def test_user_to_string_print_email(self):
		self.assertEquals(str(self.test_user), "j@j.com")

	def test_get_by_id(self):
		self.assertEquals(User.get_by_id(1), self.test_user)

class FormTesterMixin():

	def assertFormError(self, form_cls, expected_error_name, expected_error_msg, data):

		from pprint import pformat
		test_form = form_cls(data=data)

		self.assertFalse(test_form.is_valid())

		self.assertEquals(
			test_form.errors[expected_error_name],
			expected_error_msg,
			msg="Expected {} : Actual {} : using data {}".format(

				test_form.errors[expected_error_name],
				expected_error_msg, pformat(data)
			)
		)


class FormTests(unittest.TestCase, FormTesterMixin):

	def test_signin_form_data_validation_for_invalid_data(self):
		invalid_data_list = [
			{'data': {'email': 'j@j.com'},
			 'error': ('password', [u'This field is required.'])},
			 {'data': {'password': '1234'},
			  'error': ('email', [u'This field is required.'])}
		]

		for invalid_data in invalid_data_list:
			self.assertFormError(SigninForm, invalid_data['error'][0],
				invalid_data['error'][1],
				invalid_data["data"])

	def test_user_form_password_match(self):
		form = UserForm(
			{
				'name': 'jj',
				'email': 'j@j.com',
				'password': '1234',
				'ver_password': '1234',
				'last_4_digits': '3333',
				'stripe_token': '1'}
		)

		self.assertTrue(form.is_valid(), form.errors)

		self.assertIsNotNone(form.clean())

	def test_user_form_passwords_dont_match_throws_error(self):
		form = UserForm(
			{
				'name': 'jj',
				'email': 'j@j.com',
				'password': '234',
				'ver_password': '1234',
				'last_4_digits': '3333',
				'stripe_token': '1'
			}
		)

		self.assertFalse(form.is_valid())


class RegisterPageTests(TestCase, ViewTesterMixin):

	@classmethod
	def setUpTestData(cls):
		html = render_to_response(
			'register.html',
			{
				'form': UserForm(),
				'months':range(1, 12),
				'publishable': settings.STRIPE_PUBLISHABLE,
				'soon': soon(),
				'user': None,
				'years': range(2011, 2036),
			}
		)
		ViewTesterMixin.setupViewTester(
			'/register',
			register,
			html.content,
		)

	def setUp(self):
		request_factory = RequestFactory()
		self.request = request_factory.get(self.url)

	def test_invalid_form_returns_registration_page(self, ):

		with mock.patch('payments.forms.UserForm.is_valid') as user_mock:
			user_mock.return_value = False
			self.request.method = 'POST'
			self.request.POST = None
			resp = register(self.request)
			self.assertEquals(resp.content, self.expected_html)

			self.assertEquals(user_mock.call_count, 1)

	def test_registering_new_user_returns_successfully(self):

		self.request.session = {}
		self.request.method = 'POST'
		self.request.POST = {
			'email': 'python@rocks.com',
			'name': 'pyRock',
			'stripe_token': '...',
			'last_4_digits': '4242',
			'password': 'bad_password',
			'ver_password': 'bad_password',
		}

		with mock.patch('stripe.Customer') as stripe_mock:

			config = {'create.return_value': mock.Mock()}
			stripe_mock.config_mock(**config)

      # customer_create.return_value.id = 'xyz'
			resp = register(self.request)
			self.assertEquals(resp.content, "")
			self.assertEquals(resp.status_code, 302)
			self.assertEquals(self.request.session['user'], 1)

			User.objects.get(email='python@rocks.com')


	def test_registering_user_twice_cause_error_msg(self):

		user = User(name='pyRock', email='python@rocks.com')

		user.save()

		self.request.session = {}
		self.request.method = 'POST'
		self.request.POST = {
			'email': 'python@rocks.com',
			'name': 'pyRock',
			'stripe_token': '...',
			'last_4_digits': '4242',
			'pssword': 'bad_password',
			'ver_password': 'bad_password',
		}

		expected_form = UserForm(self.request.POST)
		expected_form.is_valid()
		expected_form.addError('python@rocks.com is already a member')

		html = render_to_response(
				'register.html',
				{
					'form': expected_form,
					'months': range(1, 12),
					'publishable': settings.STRIPE_PUBLISHABLE,
					'soon': soon(),
					'user': None,
					'years': range(2011, 2036),
				}
			)

		with mock.patch('stripe.Customer') as stripe_mock:

			config = {'create.return_value': mock.Mock()}
			stripe_mock.configure_mock(**config)

			resp = register(self.request)
			self.assertEquals(resp.status_code, 200)
			self.assertEquals(self.request.session, {})

			users = User.objects.filter(email="python@rocks.com")
			# self.assertEquals(len(users), 1)

			self.assertEquals(resp.content, html.content)
