from django.shortcuts import render, render_to_response
import django_ecommerce.settings as settings
from payments.views import soon, register, sign_in, sign_out
from django.test import TestCase, RequestFactory
from payments.models import User
from payments.forms import SigninForm, UserForm
from django.db import IntegrityError
from django.core.urlresolvers import resolve
from django import forms
import unittest
from unittest.mock import patch
import mock
import socket


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
    self.assertEqual(test_view.func, self.view_func)

  def test_returns_appropriate_respose_code(self):
    resp = self.view_func(self.request)
    self.assertEqual(resp.status_code, self.status_code)

  def test_returns_correct_html(self):
    resp = self.view_func(self.request)
    self.assertEqual(resp.content, self.expected_html)

class SignInPageTests(TestCase, ViewTesterMixin):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        html = render_to_response(
        	'payments/sign_in.html',
        	{
        		'form': SigninForm(),
        		'user':None
        	}
        )

        ViewTesterMixin.setupViewTester(
            '/sign_in',
            sign_in,
            html.content
        )


class SignOutPageTests(TestCase, ViewTesterMixin):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ViewTesterMixin.setupViewTester(
            '/sign_out',
            sign_out,
            b"",
            status_code=302,
            session={"user": "dummy"},
        )

    def setUp(self):
    	self.request.session = {"user": "dummy"}



class RegisterPageTests(TestCase, ViewTesterMixin):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		html = render_to_response(
			'payments/register.html',
			{
				'form': UserForm(),
				'months': list(range(1, 12)),
				'publishable': settings.STRIPE_PUBLISHABLE,
				'soon': soon(),
				'user': None,
				'years': list(range(2011, 2036)),
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

	def test_invalid_form_returns_registration_page(self):

		with mock.patch('payments.forms.UserForm.is_valid') as user_mock:

			user_mock.return_value = False
			
			self.request.method = 'POST'
			self.request.POST = None
			resp = register(self.request)
			self.assertEqual(resp.content, self.expected_html)

			self.assertEqual(user_mock.call_count, 1)

	def get_mock_cust():

		class mock_cust():

			@property
			def id(self):
				return 1234

		return mock_cust()

	@mock.patch('payments.views.Customer.create', return_value=get_mock_cust())
	def test_registering_new_user_returns_successfully(self, stripe_mock):

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

		resp = register(self.request)

		self.assertEqual(resp.content, b"")
		self.assertEqual(resp.status_code, 302)

		users = User.objects.filter(email="python@rocks.com")
		self.assertEqual(len(users), 1)
		self.assertEqual(users[0].stripe_id, '1234')

		def get_MockUserForm(self):

			from django import forms

			class MockUserForm(forms.Form):

				def is_valid(self):
					return True

				@property
				def cleaned_data(self):
					return{
						'email': 'python@rocks.com',
						'name': 'pyRock',
						'stripe_token': '...',
						'last_4_digits': '4242',
						'password': 'bad_password',
						'ver_password': 'bad_password',
					}

				def addError(self, error):
					pass

			return MockUserForm()



		# with mock.patch('stripe.Customer') as stripe_mock:

		# 	config = {'create.return_value': mock.Mock()}
		# 	stripe_mock.config_mock(**config)

  #     # customer_create.return_value.id = 'xyz'
		# 	resp = register(self.request)
		# 	self.assertEquals(resp.content, "")
		# 	self.assertEquals(resp.status_code, 302)
		# 	self.assertEquals(self.request.session['user'], 1)

		# 	User.objects.get(email='python@rocks.com')

	@mock.patch('payments.views.UserForm', get_MockUserForm)
	@mock.patch('payments.models.User.save', side_effect=IntegrityError)
	def test_registering_user_twice_cause_error_msg(self, save_mock):

		# user = User(name='pyRock', email='python@rocks.com')

		# user.save()

		self.request.session = {}
		self.request.method = 'POST'
		self.request.POST = {}

		html = render_to_response( 
			'payments/register.html',
			{
				'form': self.get_MockUserForm(),
				'months': list(range(1, 12)),
				'publishable': settings.STRIPE_PUBLISHABLE,
				'soon': soon(),
				'user': None,
				'years': list(range(2011, 2036)),
			}
		)

		# expected_form = UserForm(self.request.POST)
		# expected_form.is_valid()
		# expected_form.addError('python@rocks.com is already a member')

		# html = render_to_response(
		# 		'register.html',
		# 		{
		# 			'form': expected_form,
		# 			'months': range(1, 12),
		# 			'publishable': settings.STRIPE_PUBLISHABLE,
		# 			'soon': soon(),
		# 			'user': None,
		# 			'years': range(2011, 2036),
		# 		}
		# 	)

		with mock.patch('payments.views.Customer') as stripe_mock:

			config = {'create.return_value': mock.Mock()}
			stripe_mock.configure_mock(**config)

			resp = register(self.request)
			self.assertEqual(resp.content, html.content)
			self.assertEqual(resp.status_code, 200)
			self.assertEqual(self.request.session, {})

			users = User.objects.filter(email="python@rocks.com")
			self.assertEqual(len(users), 0)

			# self.assertEquals(resp.content, html.content)

	def test_registering_user_when_stripe_is_down(self):

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

		with mock.patch(
			'stripe.Customer.create',
			side_effect=socket.error("Can't connect to Stripe")
		) as stripe_mock:

			register(self.request)

			users = User.objects.filter(email="python@rocks.com")
			self.assertEqual(len(users), 1)
			self.assertEqual(user[0].stripe_id, '')

			
	


class UserModelTest(TestCase):

	@classmethod
	def setTestData(cls):
		cls.test_user = User(email="j@j.com", name='test user')
		cls.test_user.save()

	def test_user_to_string_print_email(self):
		self.assertEqual(User.get_by_id(self.test_user), "j@j.com")

	def test_get_by_id(self):
		self.assertEqual(User.get_by_id(self.test_user.id), self.test_user)

	def test_create_user_function_stores_in_database(self):
		user = User.create("test", "test@t.com", "tt", "1234", "22")
		self.assertEqual(User.objects.get(email="test@t.com"), user)

	def test_create_user_allready_exists_throws_IntegrityError(self):
		self.assertRaises(
			IntegrityError,
			User.create,
			"test user",
			"j@j.com",
			"jj",
			"1234",
			89
		)
		

class FormTesterMixin():

	def assertFormError(self, form_cls, expected_error_name, expected_error_msg, data):

		from pprint import pformat
		test_form = form_cls(data=data)

		self.assertFalse(test_form.is_valid())

		self.assertEqual(
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