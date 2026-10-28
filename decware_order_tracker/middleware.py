"""
HTTPS enforcement for the Heroku deployment.

Heroku terminates TLS at its router and forwards requests to the dyno over
plain HTTP, recording the scheme the client used in X-Forwarded-Proto. This
middleware uses that header to redirect plain-HTTP requests to HTTPS and to
send Strict-Transport-Security on HTTPS responses.

It deliberately does not rely on SECURE_PROXY_SSL_HEADER, so
request.is_secure() -- and with it Django's CSRF Referer checking and the
scheme of absolute URLs the app builds -- is left unchanged. Requests without
the header (local development, the test client) pass through untouched.
"""
from django.http import HttpResponsePermanentRedirect

# Short max-age, no includeSubDomains or preload. Raising it is a decision
# for the site owner once HTTPS is confirmed working on every hostname.
HSTS_HEADER_VALUE = 'max-age=3600'


class HerokuHttpsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO')
        if forwarded_proto == 'http':
            # get_host() validates the Host header against ALLOWED_HOSTS.
            return HttpResponsePermanentRedirect(
                'https://%s%s' % (request.get_host(), request.get_full_path())
            )
        response = self.get_response(request)
        if forwarded_proto == 'https':
            response.setdefault('Strict-Transport-Security', HSTS_HEADER_VALUE)
        return response
