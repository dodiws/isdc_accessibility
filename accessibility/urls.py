from accessibility.views import (
    getAccessibilities,
)
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(getAccessibilities())

urlpatterns = [
    # api
    url(r'', include(geoapi.urls)),

    url(r'^getOverviewMaps/accessibilityinfo$', 'accessibility.views.getAccesibilityInfoVillages', name='getAccesibilityInfoVillages'),
]
