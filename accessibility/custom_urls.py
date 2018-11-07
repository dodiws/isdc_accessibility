from django.conf.urls import patterns, url

urlpatterns = patterns(
    'accessibility.views',
    # url(r'^$', 'exportdata', name='exportdata'),
    # url(r'^$', 'getOverviewMaps', name='getOverviewMaps'),
    # url(r'^generalinfo$', 'getGeneralInfoVillages', name='getGeneralInfoVillages'),
    # url(r'^snowinfo$', 'getSnowVillage', name='getSnowVillage'),
    url(r'^accessibilityinfo$', 'getAccesibilityInfoVillages', name='getAccesibilityInfoVillages'),
    # url(r'^floodinfo$', 'getFloodInfoVillages', name='getFloodInfoVillages'),
    # url(r'^earthquakeinfo$', 'getEarthquakeInfoVillages', name='getEarthquakeInfoVillages'),
    # url(r'^getWMS$', 'getWMS', name='getWMS'),
    # url(r'^getGlofasChart$', 'getGlofasChart', name='getGlofasChart'),
    # url(r'^getGlofasPointsJSON$', 'getGlofasPointsJSON', name='getGlofasPointsJSON'),
    # url(r'^weatherinfo$', 'getWeatherInfoVillages', name='getWeatherInfoVillages'),
    # url(r'^demographic$', 'getDemographicInfo', name='getDemographicInfo'),
    # url(r'^landslideinfo$', 'getLandSlideInfoVillages', name='getLandSlideInfoVillages'),
    # url(r'^climateinfo$', 'getClimateVillage', name='getClimateVillage'),
    
)
