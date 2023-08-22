import itertools
import json
import os
import re
from django.conf import settings
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.http import HttpResponseRedirect
from django.urls import get_script_prefix, is_valid_path
from django.utils import translation
from django.utils.cache import patch_vary_headers

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


class DefaultLanguageMiddleware(MiddlewareMixin):
    response_redirect_class = HttpResponseRedirect

    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user.is_authenticated:
            language = user.profile.language
            translation.activate(language)

        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        user = getattr(request, 'user', None)
        if not user:
            return response
        if not user.is_authenticated:
            return response

        user_language = getattr(user.profile, 'language', None)
        if not user_language:
            return response

        current_language = translation.get_language()
        if user_language == current_language:
            return response

        translation.activate(user_language)
        language = translation.get_language()
        language_from_path = translation.get_language_from_path(request.path_info)
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = is_language_prefix_patterns_used(urlconf)

        if (response.status_code == 404 and not language_from_path and
                i18n_patterns_used and prefixed_default_language):
            language_path = '/%s%s' % (language, request.path_info)
            path_valid = is_valid_path(language_path, urlconf)
            path_needs_slash = (
                    not path_valid and (
                    settings.APPEND_SLASH and not language_path.endswith('/') and
                    is_valid_path('%s/' % language_path, urlconf)
            )
            )

            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                language_url = request.get_full_path(force_append_slash=path_needs_slash).replace(
                    script_prefix,
                    '%s%s/' % (script_prefix, language), 1
                )
                return self.response_redirect_class(language_url)

        if not (i18n_patterns_used and language_from_path):
            patch_vary_headers(response, ('Accept-Language',))
        response.headers.setdefault('Content-Language', language)
        return response