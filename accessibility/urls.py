from accessibility.views import (
    AccesibilityStatisticResource,
    AccesibilityInfoVillages,
)
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(AccesibilityStatisticResource())

GETOVERVIEWMAPS_APIOBJ = [
    AccesibilityInfoVillages(),
]

urlpatterns = [
    url(r'', include(geoapi.urls)),
    # url(r'^getOverviewMaps/accessibilityinfo$', 'accessibility.views.getAccesibilityInfoVillages', name='getAccesibilityInfoVillages'),
]
