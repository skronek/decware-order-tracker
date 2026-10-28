"""Tests for the production HTTPS enforcement (middleware and settings wiring)."""
import importlib.util
import os
from pathlib import Path
from unittest import mock

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from decware_order_tracker.middleware import HSTS_HEADER_VALUE, HerokuHttpsMiddleware

MIDDLEWARE_PATH = 'decware_order_tracker.middleware.HerokuHttpsMiddleware'
SETTINGS_FILE = Path(__file__).resolve().parent / 'settings.py'


@override_settings(ALLOWED_HOSTS=['decware-orders.info'])
class HerokuHttpsMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory(HTTP_HOST='decware-orders.info')
        self.inner_calls = 0

        def get_response(request):
            self.inner_calls += 1
            return HttpResponse('ok')

        self.middleware = HerokuHttpsMiddleware(get_response)

    def test_plain_http_redirects_to_https_keeping_path_and_query(self):
        request = self.factory.get('/admin/login/?next=/admin/', HTTP_X_FORWARDED_PROTO='http')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 308)
        self.assertEqual(response['Location'], 'https://decware-orders.info/admin/login/?next=/admin/')
        self.assertEqual(self.inner_calls, 0)

    def test_plain_http_post_redirect_keeps_method(self):
        request = self.factory.post('/admin/login/', HTTP_X_FORWARDED_PROTO='http')
        response = self.middleware(request)
        # 308, unlike 301, tells the browser to repeat the POST rather than switch to GET.
        self.assertEqual(response.status_code, 308)
        self.assertEqual(self.inner_calls, 0)

    def test_redirect_stays_on_host_for_scheme_relative_path(self):
        request = self.factory.get('//evil.example/x', HTTP_X_FORWARDED_PROTO='http')
        response = self.middleware(request)
        self.assertTrue(response['Location'].startswith('https://decware-orders.info/'))

    def test_https_response_carries_hsts(self):
        request = self.factory.get('/', HTTP_X_FORWARDED_PROTO='https')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Strict-Transport-Security'], HSTS_HEADER_VALUE)
        self.assertEqual(HSTS_HEADER_VALUE, 'max-age=31536000')

    def test_existing_hsts_header_is_not_overwritten(self):
        def get_response(request):
            response = HttpResponse('ok')
            response['Strict-Transport-Security'] = 'max-age=60'
            return response

        request = self.factory.get('/', HTTP_X_FORWARDED_PROTO='https')
        response = HerokuHttpsMiddleware(get_response)(request)
        self.assertEqual(response['Strict-Transport-Security'], 'max-age=60')

    def test_no_forwarded_header_passes_through(self):
        response = self.middleware(self.factory.get('/'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Strict-Transport-Security', response)
        self.assertEqual(self.inner_calls, 1)

    def test_unrecognised_forwarded_value_passes_through(self):
        request = self.factory.get('/', HTTP_X_FORWARDED_PROTO='https, http')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Strict-Transport-Security', response)


def _load_settings(debug):
    """Execute settings.py fresh, as a separate module, with DEBUG set in the environment."""
    env = {'DEBUG': debug}
    with mock.patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location('_settings_under_test', SETTINGS_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class HttpsSettingsWiringTests(SimpleTestCase):
    def test_production_enables_https_protections(self):
        settings = _load_settings('False')
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)
        self.assertEqual(list(settings.MIDDLEWARE)[0], MIDDLEWARE_PATH)
        # is_secure() must stay untouched; see middleware.py.
        self.assertFalse(hasattr(settings, 'SECURE_PROXY_SSL_HEADER'))
        self.assertNotIn('*', settings.ALLOWED_HOSTS)

    def test_debug_leaves_https_protections_off(self):
        settings = _load_settings('True')
        self.assertFalse(getattr(settings, 'SESSION_COOKIE_SECURE', False))
        self.assertFalse(getattr(settings, 'CSRF_COOKIE_SECURE', False))
        self.assertNotIn(MIDDLEWARE_PATH, settings.MIDDLEWARE)
