from django.conf.urls import include, url

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.core import urls as wagtail_urls

urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    url('^sitemap\.xml$', sitemap),

    url(r'', include(wagtail_urls)),
]
