from django.conf import settings
from django.utils import translation
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.validators import URLValidator
from django.http import JsonResponse
from fincapes.variables import aplikasi


class AjaxFormMixin(object):
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data."
            }
            return JsonResponse(data)
        else:
            return response


class RequestFormAttachMixin(object):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class NextUrlMixin(object):
    default_next = '/'

    def get_next_url(self):
        request = self.request
        next_ = request.GET.get('next')
        next_post = request.POST.get('next')
        redirect_path = next_ or next_post or None
        if url_has_allowed_host_and_scheme(redirect_path, request.get_host()):
            return redirect_path
        return self.default_next


class PrevUrlMixin(object):
    default_prev = '/'

    def get_prev_url(self):
        request = self.request
        self.default_prev = request.path
        request.session['balik'] = self.default_prev
        return self.default_prev


class JsonResponseMixin(object):
    def form_valid(self, form):
        response = super().form_valid(form)
        data = {
            'response': 'success'
        }
        return JsonResponse(data, status=200)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        request = self.request
        if request.is_ajax():
            data = {
                'response': form.errors
            }
            return JsonResponse(data, status=400)
        return response


class OptionalURLValidator(URLValidator):
    def __call__(self, value):
        if '://' not in value:
            value = "http://" + value
            super().__call__(value)


class CsrfExemptMixin(object):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class DefaultLanguageMixin(object):
    def dispatch(self, request, *args, **kwargs):
        language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        return super().dispatch(request, *args, **kwargs)


class ContextDataMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_name'] = aplikasi
        context['page_title'] = aplikasi.get('portal_app')
        context['navbar_needed'] = True
        context['show_footer'] = True
        return context