from accessibility.views import (
    AccesibilityStatisticResource,
)
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(AccesibilityStatisticResource())

urlpatterns = [
    url(r'', include(geoapi.urls)),
    url(r'^getOverviewMaps/accessibilityinfo$', 'accessibility.views.getAccesibilityInfoVillages', name='getAccesibilityInfoVillages'),
]
