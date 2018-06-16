# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^webauction/', include('webauction.urls', namespace='webauction')),
    url(r'^logout/$', views.logout_view, name='logout_view'),
    url(r'^messenger/', include('messenger.urls', namespace='messenger')),
    # logout deve stare sopra, così segue prima quello personalizzato prima
    url(r'^', include('django.contrib.auth.urls')),
        url(r'^sign_up/$', views.sign_up, name='sign_up'),
  # senza questa riga le immagini non caricano
] +static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
