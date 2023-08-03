from django.views.generic import TemplateView
from django.utils.translation import gettext as _


class HomepageView(TemplateView):
    template_name = 'home-default.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Selamat Datang" 
        return context
