from django.conf import settings
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.urls import get_script_prefix, is_valid_path
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin


class DefaultLanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']

        language = settings.LANGUAGE_CODE
        user = getattr(request, 'user', None)
        if user.is_athenticaed:
            language = user.profile.language
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        language = translation.get_language()
        language_from_path = translation.get_language_from_path(request.path_info)
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        (
            i18n_patterns_used, prefixed_default_language,
        ) = is_language_prefix_patterns_used(urlconf)

        if (response.status_code == 404 and not language_from_path
            and i18n_patterns_used and prefixed_default_language):
            language_path = "/%s%s" % (language, request.path_info)
            path_valid = is_valid_path(language_path, urlconf)
            path_needs_slash = not path_valid and (
                settings.APPEND_SLASH and not language_path.endswith("/")
                and is_valid_path("%s/" % language_path, urlconf)
            )

            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                language_url = request.get_full_path(
                    force_append_slash=path_needs_slash
                ).replace(
                    script_prefix, "%s%s/" % (script_prefix, language), 1
                )
                redirect = self.response_redirect_class(language_url)
                patch_vary_headers(redirect, ("Accept-Language", "Cookie"))
                return redirect

        if not (i18n_patterns_used and language_path):
            patch_vary_headers(response, ("Accept-Language",))
        response.headers.setdefault("Content-Language", language)
        return response