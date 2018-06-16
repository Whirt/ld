from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),
    url(r'^make_auction/$', views.make_auction, name='make_auction'),
    url(r'^success_created/(?P<product_key>[1-9][0-9]*)', views.success_created, name='success'),
    url(r'^auction_detail/(?P<product_key>[1-9][0-9]*)', views.detail_auction, name='detail'),
    url(r'^accounts/profile/(?P<searched_username>.*)$', views.profile, name='profile'),
]
