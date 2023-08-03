from django.urls import path
from .views import HomepageView

app_name = 'Frontpage'

urlpatterns = [
    path('', HomepageView.as_view(), name='index')
]
