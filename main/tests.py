from django.test import TestCase
from django.core.urlresolvers import resolve
from main.views import index, market_items
from django.shortcuts import render, render_to_response
from payments.models import User
from django.test import RequestFactory
import mock


class MainPageTests(TestCase):

	# Set Up
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		request_factory = RequestFactory()
		cls.request = request_factory.get('/')
		cls.request.session = {}

	# Testing Route

	def test_root_resolves_to_main_view(self):
		main_page = resolve('/')
		self.assertEqual(main_page.func, index)

	def test_returns_appropriate_html_response_code(self):
		resp = index(self.request)
		self.assertEquals(resp.status_code, 200)

	# Testing Templates and Views

	def test_returns_exact_html(self):
		resp = index(self.request)
		self.assertEqual(
			resp.content,
			render_to_response(index, "index.html").content
		)

	def test_index_handles_logged_in_user(self):

		# user = User(
		# 	name='jj',
		# 	email='j@j.com',
		# )
		# user.save()

		self.request.session = {"user": "1"}

		with mock.patch('main.views.User') as user_mock:

			config = {'get_by_id.return_value': mock.Mock()}
			user_mock.configure_mock(**config)

			resp = index(self.request)

			self.request.session = {}

			expected_html = render_to_response('main/user.html', {'user': user_mock.get_by_id(1)})

			self.assertEquals(resp.content, expected_html.content)
