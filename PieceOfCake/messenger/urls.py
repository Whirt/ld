from django.conf.urls import url
from . import views

urlpatterns = [
    # Ci devo pensare un attimo
    url(r'^$', views.messenger, name='messenger'),
    url(r'^search_user/$', views.SearchUserView.as_view(), name='search_user'),
]
