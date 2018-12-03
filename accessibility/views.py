from geodb.models import (
	# AfgAdmbndaAdm1,
	# AfgAdmbndaAdm2,
	AfgAirdrmp,
	# AfgAvsa,
	AfgCapaGsmcvr,
	AfgCaptAdm1ItsProvcImmap,
	AfgCaptAdm1NearestProvcImmap,
	AfgCaptAdm2NearestDistrictcImmap,
	AfgCaptAirdrmImmap,
	AfgCaptGmscvr,
	AfgCaptHltfacTier1Immap,
	AfgCaptHltfacTier2Immap,
	AfgCaptHltfacTier3Immap,
	AfgCaptHltfacTierallImmap,
	AfgCaptPpl,
	# AfgFldzonea100KRiskLandcoverPop, 
	AfgHltfac,
	# AfgIncidentOasis,
	AfgLndcrva,
	AfgPplp,
	# AfgRdsl,
	# districtsummary,
	# earthquake_events,
	# earthquake_shakemap,
	# FloodRiskExposure, 
	# forecastedLastUpdate, 
	# LandcoverDescription,
	# provincesummary,
	# tempCurrentSC,
	# villagesummaryEQ,
	)
from geodb.geo_calc import (
	getBaseline,
	getCommonUse,
	# getFloodForecastBySource,
	# getFloodForecastMatrix,
	getGeoJson,
	# getProvinceSummary_glofas,
	getProvinceSummary,
	# getRawBaseLine,
	# getRawFloodRisk,
	# getSettlementAtFloodRisk,
	getShortCutData,
	getTotalArea,
	getTotalBuildings,
	getTotalPop,
	getTotalSettlement,
	getRiskNumber,
	)
from geodb.views import (
	getCommonVillageData,
	getAngle,
	getConvertedTime,
	getConvertedDistance,
	getDirectionLabel,
)
import json
import time, datetime
from tastypie.resources import ModelResource, Resource
from tastypie.serializers import Serializer
# from tastypie import fields
# from tastypie.constants import ALL
from django.db.models import Count, Sum, F, When, Case
# from django.core.serializers.json import DjangoJSONEncoder
# from tastypie.authorization import DjangoAuthorization
# from urlparse import urlparse
# from geonode.maps.models import Map
# from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW
# from django.db import connection, connections
# from itertools import *

# addded by boedy
from matrix.models import matrix
from tastypie.cache import SimpleCache
# from pytz import timezone, all_timezones
# from django.http import HttpResponse

from djgeojson.serializers import Serializer as GeoJSONSerializer

# from geodb.geoapi import getRiskNumber, getAccessibilities, getEarthQuakeExecuteExternal, getYearRangeFromWeek, getClosestDroughtWOY

# from graphos.sources.model import ModelDataSource
from graphos.renderers import flot, gchart
from graphos.sources.simple import SimpleDataSource
# from django.test import RequestFactory
# import urllib2, urllib
# import pygal
# from geodb.radarchart import RadarChart
# from geodb.riverflood import getFloodForecastBySource

from django.utils.translation import ugettext as _
# from securitydb.models import SecureFeature
import pprint

# #added by razinal
# import pickle
# import visvalingamwyatt as vw
# from shapely.wkt import loads as load_wkt
# from vectorformats.Formats import Django, GeoJSON
# from vectorformats.Feature import Feature
# from vectorformats.Formats.Format import Format

# import pandas as pd

# ISDC
from geonode.utils import include_section, none_to_zero, query_to_dicts, RawSQL_nogroupby, div_by_zero_is_zero, dict_ext
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from geodb.enumerations import TIME_DISTANCE_TYPES, TIME_DISTANCE_TITLES
from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW
from urlparse import urlparse

def get_dashboard_meta(*args,**kwargs):
	# if page_name == 'accessibility':
	#     return {'function':dashboard_accessibility, 'template':'dash_accessibility.html'}
	# return None
	response = {
		'pages': [
			{
				'name': 'accessibility',
				'function': dashboard_accessibility, 
				'template': 'dash_accessibility.html',
				'menutitle': 'Accesibility',
			},
		],
		'menutitle': 'Accesibility',
	}
	return response

def getQuickOverview(request, filterLock, flag, code, includes=[], excludes=[]):
	response = {}
	response.update(GetAccesibilityData(filterLock, flag, code, includes=['AfgCaptAirdrmImmap', 'AfgCaptHltfacTier1Immap', 'AfgCaptHltfacTier2Immap', 'AfgCaptAdm1ItsProvcImmap', 'AfgCapaGsmcvr']))
	response['pop_coverage_percent'] = int(round((response['pop_on_gsm_coverage']/response['baseline']['pop_total'])*100,0))
	return response

# moved from geodb.geoapi

class getAccessibilities(ModelResource):
	class Meta:
		resource_name = 'getaccessibilities'
		allowed_methods = ['post']
		detail_allowed_methods = ['post']
		cache = SimpleCache() 
		object_class=None

	def post_list(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		response = self.getData(request)
		return self.create_response(request, response)   

	def getData(self, request):
		# AfgCaptAdm1ItsProvcImmap, AfgCaptAdm1NearestProvcImmap, AfgCaptAdm2NearestDistrictcImmap, AfgCaptAirdrmImmap, AfgCaptHltfacTier1Immap, AfgCaptHltfacTier2Immap
		# px = provincesummary.objects.aggregate(Sum('high_ava_population')
		boundaryFilter = json.loads(request.body)

		temp1 = []
		for i in boundaryFilter['spatialfilter']:
			temp1.append('ST_GeomFromText(\''+i+'\',4326)')

		temp2 = 'ARRAY['
		first=True
		for i in temp1:
			if first:
				 temp2 = temp2 + i
				 first=False
			else :
				 temp2 = temp2 + ', ' + i  

		temp2 = temp2+']'
		
		filterLock = 'ST_Union('+temp2+')'
		flag = boundaryFilter['flag']
		code = boundaryFilter['code']

		response = {}
		if flag=='entireAfg':
			q1 = AfgCaptAdm1ItsProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q2 = AfgCaptAdm1NearestProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q3 = AfgCaptAdm2NearestDistrictcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q4 = AfgCaptAirdrmImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
			q5 = AfgCaptHltfacTier1Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q6 = AfgCaptHltfacTier2Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q7 = AfgCaptHltfacTier3Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q8 = AfgCaptHltfacTierallImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			gsm = AfgCapaGsmcvr.objects.all().aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))

		elif flag =='currentProvince':
			if len(str(boundaryFilter['code'])) > 2:
				ff0001 =  "dist_code  = '"+str(boundaryFilter['code'])+"'"
			else :
				ff0001 =  "left(cast(dist_code as text), "+str(len(str(boundaryFilter['code'])))+") = '"+str(boundaryFilter['code'])+"' and length(cast(dist_code as text))="+ str(len(str(boundaryFilter['code']))+2)   
			q1 = AfgCaptAdm1ItsProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings')).extra(
				where = {
					ff0001       
				})
			q2 = AfgCaptAdm1NearestProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings')).extra(
				where = {
					ff0001       
				})
			q3 = AfgCaptAdm2NearestDistrictcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings')).extra(
				where = {
					ff0001       
				})
			q4 = AfgCaptAirdrmImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
				where = {
					ff0001       
				})
			q5 = AfgCaptHltfacTier1Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings')).extra(
				where = {
					ff0001       
				})
			q6 = AfgCaptHltfacTier2Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings')).extra(
				where = {
					ff0001       
				})
			q7 = AfgCaptHltfacTier3Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings')).extra(
				where = {
					ff0001       
				})
			q8 = AfgCaptHltfacTierallImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings')).extra(
				where = {
					ff0001       
				})
			if len(str(boundaryFilter['code'])) > 2:
				gsm = AfgCapaGsmcvr.objects.filter(dist_code=boundaryFilter['code']).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
			else :
				gsm = AfgCapaGsmcvr.objects.filter(prov_code=boundaryFilter['code']).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))    

		elif flag =='drawArea':
			tt = AfgPplp.objects.filter(wkb_geometry__intersects=boundaryFilter['spatialfilter'][0]).values('vuid')
			q1 = AfgCaptAdm1ItsProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q2 = AfgCaptAdm1NearestProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q3 = AfgCaptAdm2NearestDistrictcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q4 = AfgCaptAirdrmImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
			q5 = AfgCaptHltfacTier1Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q6 = AfgCaptHltfacTier2Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q7 = AfgCaptHltfacTier3Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q8 = AfgCaptHltfacTierallImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			gsm = AfgCapaGsmcvr.objects.filter(vuid__in=tt).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
		else:
			tt = AfgPplp.objects.filter(wkb_geometry__intersects=boundaryFilter['spatialfilter'][0]).values('vuid')
			q1 = AfgCaptAdm1ItsProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q2 = AfgCaptAdm1NearestProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q3 = AfgCaptAdm2NearestDistrictcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q4 = AfgCaptAirdrmImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
			q5 = AfgCaptHltfacTier1Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q6 = AfgCaptHltfacTier2Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q7 = AfgCaptHltfacTier3Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			q8 = AfgCaptHltfacTierallImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
			gsm = AfgCapaGsmcvr.objects.filter(vuid__in=tt).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))

		for i in q1: 
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__itsx_prov']=round(i['pop'] or 0)   
			response[timelabel+'__itsx_prov_building']=round(i['buildings'] or 0)    
		for i in q2:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_prov']=round(i['pop'] or 0)   
			response[timelabel+'__near_prov_building']=round(i['buildings'] or 0)     
		for i in q3:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_dist']=round(i['pop'] or 0)  
			response[timelabel+'__near_dist_building']=round(i['buildings'] or 0)      
		for i in q4:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_airp']=round(i['pop'] or 0)     
		for i in q5:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hlt1']=round(i['pop'] or 0) 
			response[timelabel+'__near_hlt1_building']=round(i['buildings'] or 0)     
		for i in q6:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hlt2']=round(i['pop'] or 0) 
			response[timelabel+'__near_hlt2_building']=round(i['buildings'] or 0)      
		for i in q7:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hlt3']=round(i['pop'] or 0) 
			response[timelabel+'__near_hlt3_building']=round(i['buildings'] or 0)   
		for i in q8:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hltall']=round(i['pop'] or 0)  
			response[timelabel+'__near_hltall_building']=round(i['buildings'] or 0)    

		response['pop_on_gsm_coverage'] = round((gsm['pop'] or 0),0)
		response['area_on_gsm_coverage'] = round((gsm['area'] or 0)/1000000,0)
		response['buildings_on_gsm_coverage'] = gsm['buildings'] or 0

		return response

def getAccesibilityInfoVillages(request):
	template = './accessInfo.html'
	village = request.GET["v"]
	context_dict = getCommonVillageData(village)

	px = get_object_or_404(AfgCaptPpl, vil_uid=village)
	context_dict['cl_road_time']=getConvertedTime(px.time_to_road)
	context_dict['cl_road_distance']=getConvertedDistance(px.distance_to_road)

	# airport
	try:
		ptemp = get_object_or_404(AfgAirdrmp, geonameid=px.airdrm_id)
		angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
		context_dict['cl_airport_name']=ptemp.namelong
		context_dict['cl_airport_time']=getConvertedTime(px.airdrm_time)
		context_dict['cl_airport_distance']=getConvertedDistance(px.airdrm_dist)
		context_dict['cl_airport_angle']=angle['angle']
		context_dict['cl_airport_direction_label']=getDirectionLabel(angle['angle'])
	except:
		print 'not found'

	# closest prov capital
	try:
		ptemp = get_object_or_404(AfgPplp, vil_uid=px.ppl_provc_vuid)
		angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
		context_dict['cl_prov_cap_name']=ptemp.name_en
		context_dict['cl_prov_cap_time']=getConvertedTime(px.ppl_provc_time)
		context_dict['cl_prov_cap_distance']=getConvertedDistance(px.ppl_provc_dist)
		context_dict['cl_prov_cap_angle']=angle['angle']
		context_dict['cl_prov_cap_direction_label']=getDirectionLabel(angle['angle'])
		context_dict['cl_prov_cap_parent'] = ptemp.prov_na_en
	except:
		print 'not found'

	# Its prov capital
	try:
		ptemp = get_object_or_404(AfgPplp, vil_uid=px.ppl_provc_its_vuid)
		angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
		context_dict['it_prov_cap_name']=ptemp.name_en
		context_dict['it_prov_cap_time']=getConvertedTime(px.ppl_provc_its_time)
		context_dict['it_prov_cap_distance']=getConvertedDistance(px.ppl_provc_its_dist)
		context_dict['it_prov_cap_angle']=angle['angle']
		context_dict['it_prov_cap_direction_label']=getDirectionLabel(angle['angle'])
	except:
		print 'not found'

	# closest district capital
	try:
		ptemp = get_object_or_404(AfgPplp, vil_uid=px.ppl_distc_vuid)
		angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
		context_dict['cl_dist_cap_name']=ptemp.name_en
		context_dict['cl_dist_cap_time']=getConvertedTime(px.ppl_distc_time)
		context_dict['cl_dist_cap_distance']=getConvertedDistance(px.ppl_distc_dist)
		context_dict['cl_dist_cap_angle']=angle['angle']
		context_dict['cl_dist_cap_direction_label']=getDirectionLabel(angle['angle'])
		context_dict['cl_dist_cap_parent'] = ptemp.prov_na_en
	except:
		print 'not found'

	# Its district capital
	try:
		ptemp = get_object_or_404(AfgPplp, vil_uid=px.ppl_distc_its_vuid)
		angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
		context_dict['it_dist_cap_name']=ptemp.name_en
		context_dict['it_dist_cap_time']=getConvertedTime(px.ppl_distc_its_time)
		context_dict['it_dist_cap_distance']=getConvertedDistance(px.ppl_distc_its_dist)
		context_dict['it_dist_cap_angle']=angle['angle']
		context_dict['it_dist_cap_direction_label']=getDirectionLabel(angle['angle'])
	except:
		print 'not found'

	# Closest HF tier 1
	try:
		ptemp = get_object_or_404(AfgHltfac, facility_id=px.hltfac_tier1_id)
	except:
		ptemp = AfgHltfac.objects.all().filter(facility_id=px.hltfac_tier1_id)[0]
	angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
	context_dict['t1_hf_name']=ptemp.facility_name
	context_dict['t1_hf_time']=getConvertedTime(px.hltfac_tier1_time)
	context_dict['t1_hf_distance']=getConvertedDistance(px.hltfac_tier1_dist)
	context_dict['t1_hf_angle']=angle['angle']
	context_dict['t1_hf_direction_label']=getDirectionLabel(angle['angle'])
	context_dict['t1_hf_prov_parent'] = ptemp.prov_na_en
	context_dict['t1_hf_dist_parent'] = ptemp.dist_na_en

	# Closest HF tier 2
	try:
		ptemp = get_object_or_404(AfgHltfac, facility_id=px.hltfac_tier2_id)
	except:
		ptemp = AfgHltfac.objects.all().filter(facility_id=px.hltfac_tier2_id)[0]
	angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
	context_dict['t2_hf_name']=ptemp.facility_name
	context_dict['t2_hf_time']=getConvertedTime(px.hltfac_tier2_time)
	context_dict['t2_hf_distance']=getConvertedDistance(px.hltfac_tier2_dist)
	context_dict['t2_hf_angle']=angle['angle']
	context_dict['t2_hf_direction_label']=getDirectionLabel(angle['angle'])
	context_dict['t2_hf_prov_parent'] = ptemp.prov_na_en
	context_dict['t2_hf_dist_parent'] = ptemp.dist_na_en

	# Closest HF tier 3
	try:
		ptemp = get_object_or_404(AfgHltfac, facility_id=px.hltfac_tier3_id)
	except:
		ptemp = AfgHltfac.objects.all().filter(facility_id=px.hltfac_tier3_id)[0]
	angle = getAngle(ptemp.wkb_geometry.x, ptemp.wkb_geometry.y, context_dict['position'].x, context_dict['position'].y)
	context_dict['t3_hf_name']=ptemp.facility_name
	context_dict['t3_hf_time']=getConvertedTime(px.hltfac_tier3_time)
	context_dict['t3_hf_distance']=getConvertedDistance(px.hltfac_tier3_dist)
	context_dict['t3_hf_angle']=angle['angle']
	context_dict['t3_hf_direction_label']=getDirectionLabel(angle['angle'])
	context_dict['t3_hf_prov_parent'] = ptemp.prov_na_en
	context_dict['t3_hf_dist_parent'] = ptemp.dist_na_en

	# GSM Coverages
	try:
		ptemp = get_object_or_404(AfgCaptGmscvr, vuid=village)
		if ptemp:
			context_dict['gsm_covered'] = 'Yes'
		else:
			context_dict['gsm_covered'] = 'No coverage'
	except:
		ptemp = AfgCaptGmscvr.objects.all().filter(vuid=village)
		if len(ptemp)>0:
			context_dict['gsm_covered'] = 'Yes'
		else:
			context_dict['gsm_covered'] = 'No coverage'

	context_dict.pop('position')
	return render_to_response(template,
								  RequestContext(request, context_dict))

# moved from geodb.geo_calc

def GetAccesibilityData(filterLock, flag, code, includes=[], excludes=[]):
	response = {}
	gsm_child = {}
	if flag=='entireAfg':
		q1 = AfgCaptAdm1ItsProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
		q2 = AfgCaptAdm1NearestProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
		q3 = AfgCaptAdm2NearestDistrictcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
		q4 = AfgCaptAirdrmImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'))
		q5 = AfgCaptHltfacTier1Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
		q6 = AfgCaptHltfacTier2Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
		q7 = AfgCaptHltfacTier3Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
		q8 = AfgCaptHltfacTierallImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population'),buildings=Sum('area_buildings'))
		gsm = AfgCapaGsmcvr.objects.all().aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
		gsm_child = AfgCapaGsmcvr.objects.all().extra(select={'na_en': 'SELECT prov_na_en FROM afg_admbnda_adm1 WHERE afg_admbnda_adm1.prov_code = afg_capa_gsmcvr.prov_code'}).\
		values('prov_code', 'na_en').annotate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))

	elif flag =='currentProvince':
		if len(str(code)) > 2:
			ff0001 =  "dist_code  = '"+str(code)+"'"
		else :
			ff0001 =  "left(cast(dist_code as text), "+str(len(str(code)))+") = '"+str(code)+"' and length(cast(dist_code as text))="+ str(len(str(code))+2)
		q1 = AfgCaptAdm1ItsProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		q2 = AfgCaptAdm1NearestProvcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		q3 = AfgCaptAdm2NearestDistrictcImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		q4 = AfgCaptAirdrmImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		q5 = AfgCaptHltfacTier1Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		q6 = AfgCaptHltfacTier2Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		q7 = AfgCaptHltfacTier3Immap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		q8 = AfgCaptHltfacTierallImmap.objects.all().values('time').annotate(pop=Sum('sum_area_population')).extra(
			where = {
				ff0001
			})
		if len(str(code)) > 2:
			gsm = AfgCapaGsmcvr.objects.filter(dist_code=code).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
			gsm_child = AfgCapaGsmcvr.objects.filter(dist_code=code).extra(select={'na_en': 'SELECT dist_na_en FROM afg_admbnda_adm2 WHERE afg_admbnda_adm2.dist_code = afg_capa_gsmcvr.dist_code'}).\
			values('dist_code', 'na_en').annotate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
		else :
			gsm = AfgCapaGsmcvr.objects.filter(prov_code=code).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
			gsm_child = AfgCapaGsmcvr.objects.filter(dist_code=code).extra(select={'na_en': 'SELECT dist_na_en FROM afg_admbnda_adm2 WHERE afg_admbnda_adm2.dist_code = afg_capa_gsmcvr.dist_code'}).\
			values('dist_code', 'na_en').annotate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))

	elif flag =='drawArea':
		tt = AfgPplp.objects.filter(wkb_geometry__intersects=filterLock).values('vuid')
		q1 = AfgCaptAdm1ItsProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q2 = AfgCaptAdm1NearestProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q3 = AfgCaptAdm2NearestDistrictcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q4 = AfgCaptAirdrmImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q5 = AfgCaptHltfacTier1Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q6 = AfgCaptHltfacTier2Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q7 = AfgCaptHltfacTier3Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q8 = AfgCaptHltfacTierallImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		gsm = AfgCapaGsmcvr.objects.filter(vuid__in=tt).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
		gsm_child = {}
	else:
		tt = AfgPplp.objects.filter(wkb_geometry__intersects=filterLock).values('vuid')
		q1 = AfgCaptAdm1ItsProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q2 = AfgCaptAdm1NearestProvcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q3 = AfgCaptAdm2NearestDistrictcImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q4 = AfgCaptAirdrmImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q5 = AfgCaptHltfacTier1Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q6 = AfgCaptHltfacTier2Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q7 = AfgCaptHltfacTier3Immap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		q8 = AfgCaptHltfacTierallImmap.objects.filter(vuid__in=tt).values('time').annotate(pop=Sum('sum_area_population'))
		gsm = AfgCapaGsmcvr.objects.filter(vuid__in=tt).aggregate(pop=Sum('gsm_coverage_population'),area=Sum('gsm_coverage_area_sqm'),buildings=Sum('area_buildings'))
		gsm_child = {}

	if include_section('AfgPplp', includes, excludes):
		for i in q1:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__itsx_prov']=round(i['pop'] or 0)
	if include_section('AfgCaptAdm1ItsProvcImmap', includes, excludes):
		for i in q2:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_prov']=round(i['pop'] or 0)
	if include_section('AfgCaptAdm1NearestProvcImmap', includes, excludes):
		for i in q3:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_dist']=round(i['pop'] or 0)
	if include_section('AfgCaptAirdrmImmap', includes, excludes):
		for i in q4:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_airp']=round(i['pop'] or 0)
	if include_section('AfgCaptHltfacTier1Immap', includes, excludes):
		for i in q5:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hlt1']=round(i['pop'] or 0)
	if include_section('AfgCaptHltfacTier2Immap', includes, excludes):
		for i in q6:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hlt2']=round(i['pop'] or 0)
	if include_section('AfgCaptHltfacTier3Immap', includes, excludes):
		for i in q7:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hlt3']=round(i['pop'] or 0)
	if include_section('AfgCaptHltfacTierallImmap', includes, excludes):
		for i in q8:
			timelabel = i['time'].replace(' ','_')
			timelabel = timelabel.replace('<','l')
			timelabel = timelabel.replace('>','g')
			response[timelabel+'__near_hltall']=round(i['pop'] or 0)

	if include_section('AfgCapaGsmcvr', includes, excludes):
		# pprint.pprint(list(gsm_child))
		response['pop_on_gsm_coverage'] = round((gsm['pop'] or 0),0)
		response['area_on_gsm_coverage'] = round((gsm['area'] or 0)/1000000,0)
		response['buildings_on_gsm_coverage'] = round((gsm['buildings'] or 0),0)

	if include_section('AfgCapaGsmcvr_child', includes, excludes):
		list_gsm_child = []
		for i in gsm_child:
			i['area'] = round((i['area'] or 0)/1000000,0)
			list_gsm_child.append(i)
		response['gsm_child'] = list_gsm_child

	return response

def getAccessibility(request, filterLock, flag, code, includes=[], excludes=[]):
	rawFilterLock = None
	if 'flag' in request.GET:
		rawFilterLock = filterLock
		filterLock = 'ST_GeomFromText(\''+filterLock+'\',4326)'

	# targetBase = AfgLndcrva.objects.all()
	response = dict_ext()
	# response = getCommonUse(request, flag, code)

	response['baseline'] = getBaseline(request, filterLock, flag, code, includes=['pop_lc','building_lc'])

	# if flag not in ['entireAfg','currentProvince']:
	#     response['Population']=getTotalPop(filterLock, flag, code, targetBase)
	#     response['Area']=getTotalArea(filterLock, flag, code, targetBase)
	#     response['Buildings']=getTotalBuildings(filterLock, flag, code, targetBase)
	#     response['settlement']=getTotalSettlement(filterLock, flag, code, targetBase)
	# else :
	#     tempData = getShortCutData(flag,code)
	#     response['Population']= tempData['Population']
	#     response['Area']= tempData['Area']
	#     response['Buildings']= tempData['total_buildings']
	#     response['settlement']= tempData['settlements']

	accesibilitydata = GetAccesibilityData(rawFilterLock, flag, code, includes, excludes)

	# print rawAccesibility

	# for i in rawAccesibility:
	#     response[i]=rawAccesibility[i]
	
	response.update({k:accesibilitydata[k] for k in ['pop_on_gsm_coverage','area_on_gsm_coverage','buildings_on_gsm_coverage']})

	response['pop_coverage_percent'] = int(round(((response['pop_on_gsm_coverage'] or 0)/(response['baseline']['pop_total'] or 1))*100,0))
	response['area_coverage_percent'] = int(round(((response['area_on_gsm_coverage'] or 0)/(response['baseline']['area_total'] or 1))*100,0))
	response['buildings_coverage_percent'] = int(round(((response['buildings_on_gsm_coverage'] or 0)/(response['baseline']['building_total'] or 1))*100,0))

	# response['pop_coverage_percent'] = int(round(((response['pop_on_gsm_coverage'] or 0)/(response['Population'] or 1))*100,0))
	# response['area_coverage_percent'] = int(round(((response['area_on_gsm_coverage'] or 0)/(response['Area'] or 1))*100,0))
	# response['buildings_coverage_percent'] = int(round(((response['buildings_on_gsm_coverage'] or 0)/(response['Buildings'] or 1))*100,0))

	for i in ['near_airp','near_hlt1','near_hlt2','near_hlt3','near_hltall','itsx_prov','near_prov','near_dist']:
		response[i] = {k:accesibilitydata.get('%s_h__%s'%(k,i)) or 0 for k in TIME_DISTANCE_TYPES}
		response[i+'_percent'] = {k:round(div_by_zero_is_zero(v, response['baseline']['pop_total'])*100, 0) or 0 for k,v in response[i].items()}

	# response['l1_h__near_airp_percent'] = int(round((response['l1_h__near_airp']/response['Population'])*100,0)) if 'l1_h__near_airp' in response else 0
	# response['l2_h__near_airp_percent'] = int(round((response['l2_h__near_airp']/response['Population'])*100,0)) if 'l2_h__near_airp' in response else 0
	# response['l3_h__near_airp_percent'] = int(round((response['l3_h__near_airp']/response['Population'])*100,0)) if 'l3_h__near_airp' in response else 0
	# response['l4_h__near_airp_percent'] = int(round((response['l4_h__near_airp']/response['Population'])*100,0)) if 'l4_h__near_airp' in response else 0
	# response['l5_h__near_airp_percent'] = int(round((response['l5_h__near_airp']/response['Population'])*100,0)) if 'l5_h__near_airp' in response else 0
	# response['l6_h__near_airp_percent'] = int(round((response['l6_h__near_airp']/response['Population'])*100,0)) if 'l6_h__near_airp' in response else 0
	# response['l7_h__near_airp_percent'] = int(round((response['l7_h__near_airp']/response['Population'])*100,0)) if 'l7_h__near_airp' in response else 0
	# response['l8_h__near_airp_percent'] = int(round((response['l8_h__near_airp']/response['Population'])*100,0)) if 'l8_h__near_airp' in response else 0
	# response['g8_h__near_airp_percent'] = int(round((response['g8_h__near_airp']/response['Population'])*100,0)) if 'g8_h__near_airp' in response else 0

	# response['l1_h__near_hlt1_percent'] = int(round((response['l1_h__near_hlt1']/response['Population'])*100,0)) if 'l1_h__near_hlt1' in response else 0
	# response['l2_h__near_hlt1_percent'] = int(round((response['l2_h__near_hlt1']/response['Population'])*100,0)) if 'l2_h__near_hlt1' in response else 0
	# response['l3_h__near_hlt1_percent'] = int(round((response['l3_h__near_hlt1']/response['Population'])*100,0)) if 'l3_h__near_hlt1' in response else 0
	# response['l4_h__near_hlt1_percent'] = int(round((response['l4_h__near_hlt1']/response['Population'])*100,0)) if 'l4_h__near_hlt1' in response else 0
	# response['l5_h__near_hlt1_percent'] = int(round((response['l5_h__near_hlt1']/response['Population'])*100,0)) if 'l5_h__near_hlt1' in response else 0
	# response['l6_h__near_hlt1_percent'] = int(round((response['l6_h__near_hlt1']/response['Population'])*100,0)) if 'l6_h__near_hlt1' in response else 0
	# response['l7_h__near_hlt1_percent'] = int(round((response['l7_h__near_hlt1']/response['Population'])*100,0)) if 'l7_h__near_hlt1' in response else 0
	# response['l8_h__near_hlt1_percent'] = int(round((response['l8_h__near_hlt1']/response['Population'])*100,0)) if 'l8_h__near_hlt1' in response else 0
	# response['g8_h__near_hlt1_percent'] = int(round((response['g8_h__near_hlt1']/response['Population'])*100,0)) if 'g8_h__near_hlt1' in response else 0

	# response['l1_h__near_hlt2_percent'] = int(round((response['l1_h__near_hlt2']/response['Population'])*100,0)) if 'l1_h__near_hlt2' in response else 0
	# response['l2_h__near_hlt2_percent'] = int(round((response['l2_h__near_hlt2']/response['Population'])*100,0)) if 'l2_h__near_hlt2' in response else 0
	# response['l3_h__near_hlt2_percent'] = int(round((response['l3_h__near_hlt2']/response['Population'])*100,0)) if 'l3_h__near_hlt2' in response else 0
	# response['l4_h__near_hlt2_percent'] = int(round((response['l4_h__near_hlt2']/response['Population'])*100,0)) if 'l4_h__near_hlt2' in response else 0
	# response['l5_h__near_hlt2_percent'] = int(round((response['l5_h__near_hlt2']/response['Population'])*100,0)) if 'l5_h__near_hlt2' in response else 0
	# response['l6_h__near_hlt2_percent'] = int(round((response['l6_h__near_hlt2']/response['Population'])*100,0)) if 'l6_h__near_hlt2' in response else 0
	# response['l7_h__near_hlt2_percent'] = int(round((response['l7_h__near_hlt2']/response['Population'])*100,0)) if 'l7_h__near_hlt2' in response else 0
	# response['l8_h__near_hlt2_percent'] = int(round((response['l8_h__near_hlt2']/response['Population'])*100,0)) if 'l8_h__near_hlt2' in response else 0
	# response['g8_h__near_hlt2_percent'] = int(round((response['g8_h__near_hlt2']/response['Population'])*100,0)) if 'g8_h__near_hlt2' in response else 0

	# response['l1_h__near_hlt3_percent'] = int(round((response['l1_h__near_hlt3']/response['Population'])*100,0)) if 'l1_h__near_hlt3' in response else 0
	# response['l2_h__near_hlt3_percent'] = int(round((response['l2_h__near_hlt3']/response['Population'])*100,0)) if 'l2_h__near_hlt3' in response else 0
	# response['l3_h__near_hlt3_percent'] = int(round((response['l3_h__near_hlt3']/response['Population'])*100,0)) if 'l3_h__near_hlt3' in response else 0
	# response['l4_h__near_hlt3_percent'] = int(round((response['l4_h__near_hlt3']/response['Population'])*100,0)) if 'l4_h__near_hlt3' in response else 0
	# response['l5_h__near_hlt3_percent'] = int(round((response['l5_h__near_hlt3']/response['Population'])*100,0)) if 'l5_h__near_hlt3' in response else 0
	# response['l6_h__near_hlt3_percent'] = int(round((response['l6_h__near_hlt3']/response['Population'])*100,0)) if 'l6_h__near_hlt3' in response else 0
	# response['l7_h__near_hlt3_percent'] = int(round((response['l7_h__near_hlt3']/response['Population'])*100,0)) if 'l7_h__near_hlt3' in response else 0
	# response['l8_h__near_hlt3_percent'] = int(round((response['l8_h__near_hlt3']/response['Population'])*100,0)) if 'l8_h__near_hlt3' in response else 0
	# response['g8_h__near_hlt3_percent'] = int(round((response['g8_h__near_hlt3']/response['Population'])*100,0)) if 'g8_h__near_hlt3' in response else 0

	# response['l1_h__near_hltall_percent'] = int(round((response['l1_h__near_hltall']/response['Population'])*100,0)) if 'l1_h__near_hltall' in response else 0
	# response['l2_h__near_hltall_percent'] = int(round((response['l2_h__near_hltall']/response['Population'])*100,0)) if 'l2_h__near_hltall' in response else 0
	# response['l3_h__near_hltall_percent'] = int(round((response['l3_h__near_hltall']/response['Population'])*100,0)) if 'l3_h__near_hltall' in response else 0
	# response['l4_h__near_hltall_percent'] = int(round((response['l4_h__near_hltall']/response['Population'])*100,0)) if 'l4_h__near_hltall' in response else 0
	# response['l5_h__near_hltall_percent'] = int(round((response['l5_h__near_hltall']/response['Population'])*100,0)) if 'l5_h__near_hltall' in response else 0
	# response['l6_h__near_hltall_percent'] = int(round((response['l6_h__near_hltall']/response['Population'])*100,0)) if 'l6_h__near_hltall' in response else 0
	# response['l7_h__near_hltall_percent'] = int(round((response['l7_h__near_hltall']/response['Population'])*100,0)) if 'l7_h__near_hltall' in response else 0
	# response['l8_h__near_hltall_percent'] = int(round((response['l8_h__near_hltall']/response['Population'])*100,0)) if 'l8_h__near_hltall' in response else 0
	# response['g8_h__near_hltall_percent'] = int(round((response['g8_h__near_hltall']/response['Population'])*100,0)) if 'g8_h__near_hltall' in response else 0

	# response['l1_h__itsx_prov_percent'] = int(round((response['l1_h__itsx_prov']/response['Population'])*100,0)) if 'l1_h__itsx_prov' in response else 0
	# response['l2_h__itsx_prov_percent'] = int(round((response['l2_h__itsx_prov']/response['Population'])*100,0)) if 'l2_h__itsx_prov' in response else 0
	# response['l3_h__itsx_prov_percent'] = int(round((response['l3_h__itsx_prov']/response['Population'])*100,0)) if 'l3_h__itsx_prov' in response else 0
	# response['l4_h__itsx_prov_percent'] = int(round((response['l4_h__itsx_prov']/response['Population'])*100,0)) if 'l4_h__itsx_prov' in response else 0
	# response['l5_h__itsx_prov_percent'] = int(round((response['l5_h__itsx_prov']/response['Population'])*100,0)) if 'l5_h__itsx_prov' in response else 0
	# response['l6_h__itsx_prov_percent'] = int(round((response['l6_h__itsx_prov']/response['Population'])*100,0)) if 'l6_h__itsx_prov' in response else 0
	# response['l7_h__itsx_prov_percent'] = int(round((response['l7_h__itsx_prov']/response['Population'])*100,0)) if 'l7_h__itsx_prov' in response else 0
	# response['l8_h__itsx_prov_percent'] = int(round((response['l8_h__itsx_prov']/response['Population'])*100,0)) if 'l8_h__itsx_prov' in response else 0
	# response['g8_h__itsx_prov_percent'] = int(round((response['g8_h__itsx_prov']/response['Population'])*100,0)) if 'g8_h__itsx_prov' in response else 0

	# response['l1_h__near_prov_percent'] = int(round((response['l1_h__near_prov']/response['Population'])*100,0)) if 'l1_h__near_prov' in response else 0
	# response['l2_h__near_prov_percent'] = int(round((response['l2_h__near_prov']/response['Population'])*100,0)) if 'l2_h__near_prov' in response else 0
	# response['l3_h__near_prov_percent'] = int(round((response['l3_h__near_prov']/response['Population'])*100,0)) if 'l3_h__near_prov' in response else 0
	# response['l4_h__near_prov_percent'] = int(round((response['l4_h__near_prov']/response['Population'])*100,0)) if 'l4_h__near_prov' in response else 0
	# response['l5_h__near_prov_percent'] = int(round((response['l5_h__near_prov']/response['Population'])*100,0)) if 'l5_h__near_prov' in response else 0
	# response['l6_h__near_prov_percent'] = int(round((response['l6_h__near_prov']/response['Population'])*100,0)) if 'l6_h__near_prov' in response else 0
	# response['l7_h__near_prov_percent'] = int(round((response['l7_h__near_prov']/response['Population'])*100,0)) if 'l7_h__near_prov' in response else 0
	# response['l8_h__near_prov_percent'] = int(round((response['l8_h__near_prov']/response['Population'])*100,0)) if 'l8_h__near_prov' in response else 0
	# response['g8_h__near_prov_percent'] = int(round((response['g8_h__near_prov']/response['Population'])*100,0)) if 'g8_h__near_prov' in response else 0

	# response['l1_h__near_dist_percent'] = int(round((response['l1_h__near_dist']/response['Population'])*100,0)) if 'l1_h__near_dist' in response else 0
	# response['l2_h__near_dist_percent'] = int(round((response['l2_h__near_dist']/response['Population'])*100,0)) if 'l2_h__near_dist' in response else 0
	# response['l3_h__near_dist_percent'] = int(round((response['l3_h__near_dist']/response['Population'])*100,0)) if 'l3_h__near_dist' in response else 0
	# response['l4_h__near_dist_percent'] = int(round((response['l4_h__near_dist']/response['Population'])*100,0)) if 'l4_h__near_dist' in response else 0
	# response['l5_h__near_dist_percent'] = int(round((response['l5_h__near_dist']/response['Population'])*100,0)) if 'l5_h__near_dist' in response else 0
	# response['l6_h__near_dist_percent'] = int(round((response['l6_h__near_dist']/response['Population'])*100,0)) if 'l6_h__near_dist' in response else 0
	# response['l7_h__near_dist_percent'] = int(round((response['l7_h__near_dist']/response['Population'])*100,0)) if 'l7_h__near_dist' in response else 0
	# response['l8_h__near_dist_percent'] = int(round((response['l8_h__near_dist']/response['Population'])*100,0)) if 'l8_h__near_dist' in response else 0
	# response['g8_h__near_dist_percent'] = int(round((response['g8_h__near_dist']/response['Population'])*100,0)) if 'g8_h__near_dist' in response else 0

	# data1 = []
	# data1.append(['agg_simplified_description','area_population'])
	# data1.append([_('Population with GSM coverage'),response['pop_on_gsm_coverage']])
	# data1.append([_('Population without GSM coverage'),response['Population']-response['pop_on_gsm_coverage']])
	# response['total_pop_coverage_chart'] = gchart.PieChart(SimpleDataSource(data=data1), html_id="pie_chart1", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270})

	# data2 = []
	# data2.append(['agg_simplified_description','area_population'])
	# data2.append([_('Area with GSM coverage'),response['area_on_gsm_coverage']])
	# data2.append([_('Area without GSM coverage'),response['Area']-response['area_on_gsm_coverage']])
	# response['total_area_coverage_chart'] = gchart.PieChart(SimpleDataSource(data=data2), html_id="pie_chart2", options={'title':'', 'width': 135,'height': 135, 'pieSliceText': 'number', 'pieSliceTextStyle': 'black','legend': 'none', 'pieHole': 0.75, 'slices':{0:{'color':'red'},1:{'color':'grey'}}, 'pieStartAngle': 270 })

	# dataNearestAirp = []
	# dataNearestAirp.append(['time','population'])
	# dataNearestAirp.append([_('< 1 h'),response['l1_h__near_airp'] if 'l1_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('< 2 h'),response['l2_h__near_airp'] if 'l2_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('< 3 h'),response['l3_h__near_airp'] if 'l3_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('< 4 h'),response['l4_h__near_airp'] if 'l4_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('< 5 h'),response['l5_h__near_airp'] if 'l5_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('< 6 h'),response['l6_h__near_airp'] if 'l6_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('< 7 h'),response['l7_h__near_airp'] if 'l7_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('< 8 h'),response['l8_h__near_airp'] if 'l8_h__near_airp' in response else 0])
	# dataNearestAirp.append([_('> 8 h'),response['g8_h__near_airp'] if 'g8_h__near_airp' in response else 0])
	# response['nearest_airport_chart'] = gchart.PieChart(SimpleDataSource(data=dataNearestAirp), html_id="pie_chart3", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })
	# # response['nearest_airport_chart'] = gchart.PieChart(SimpleDataSource(data=dataNearestAirp), html_id="pie_chart3", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': 'none', 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	# datatier1 = []
	# datatier1.append(['time','population'])
	# datatier1.append([_('< 1 h'),response['l1_h__near_hlt1'] if 'l1_h__near_hlt1' in response else 0])
	# datatier1.append([_('< 2 h'),response['l2_h__near_hlt1'] if 'l2_h__near_hlt1' in response else 0])
	# datatier1.append([_('< 3 h'),response['l3_h__near_hlt1'] if 'l3_h__near_hlt1' in response else 0])
	# datatier1.append([_('< 4 h'),response['l4_h__near_hlt1'] if 'l4_h__near_hlt1' in response else 0])
	# datatier1.append([_('< 5 h'),response['l5_h__near_hlt1'] if 'l5_h__near_hlt1' in response else 0])
	# datatier1.append([_('< 6 h'),response['l6_h__near_hlt1'] if 'l6_h__near_hlt1' in response else 0])
	# datatier1.append([_('< 7 h'),response['l7_h__near_hlt1'] if 'l7_h__near_hlt1' in response else 0])
	# datatier1.append([_('< 8 h'),response['l8_h__near_hlt1'] if 'l8_h__near_hlt1' in response else 0])
	# datatier1.append([_('> 8 h'),response['g8_h__near_hlt1'] if 'g8_h__near_hlt1' in response else 0])
	# response['tier1_chart'] = gchart.PieChart(SimpleDataSource(data=datatier1), html_id="pie_chart4", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	# datatier2 = []
	# datatier2.append(['time','population'])
	# datatier2.append([_('< 1 h'),response['l1_h__near_hlt2'] if 'l1_h__near_hlt2' in response else 0])
	# datatier2.append([_('< 2 h'),response['l2_h__near_hlt2'] if 'l2_h__near_hlt2' in response else 0])
	# datatier2.append([_('< 3 h'),response['l3_h__near_hlt2'] if 'l3_h__near_hlt2' in response else 0])
	# datatier2.append([_('< 4 h'),response['l4_h__near_hlt2'] if 'l4_h__near_hlt2' in response else 0])
	# datatier2.append([_('< 5 h'),response['l5_h__near_hlt2'] if 'l5_h__near_hlt2' in response else 0])
	# datatier2.append([_('< 6 h'),response['l6_h__near_hlt2'] if 'l6_h__near_hlt2' in response else 0])
	# datatier2.append([_('< 7 h'),response['l7_h__near_hlt2'] if 'l7_h__near_hlt2' in response else 0])
	# datatier2.append([_('< 8 h'),response['l8_h__near_hlt2'] if 'l8_h__near_hlt2' in response else 0])
	# datatier2.append([_('> 8 h'),response['g8_h__near_hlt2'] if 'g8_h__near_hlt2' in response else 0])
	# response['tier2_chart'] = gchart.PieChart(SimpleDataSource(data=datatier2), html_id="pie_chart5", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	# datatier3 = []
	# datatier3.append(['time','population'])
	# datatier3.append([_('< 1 h'),response['l1_h__near_hlt3'] if 'l1_h__near_hlt3' in response else 0])
	# datatier3.append([_('< 2 h'),response['l2_h__near_hlt3'] if 'l2_h__near_hlt3' in response else 0])
	# datatier3.append([_('< 3 h'),response['l3_h__near_hlt3'] if 'l3_h__near_hlt3' in response else 0])
	# datatier3.append([_('< 4 h'),response['l4_h__near_hlt3'] if 'l4_h__near_hlt3' in response else 0])
	# datatier3.append([_('< 5 h'),response['l5_h__near_hlt3'] if 'l5_h__near_hlt3' in response else 0])
	# datatier3.append([_('< 6 h'),response['l6_h__near_hlt3'] if 'l6_h__near_hlt3' in response else 0])
	# datatier3.append([_('< 7 h'),response['l7_h__near_hlt3'] if 'l7_h__near_hlt3' in response else 0])
	# datatier3.append([_('< 8 h'),response['l8_h__near_hlt3'] if 'l8_h__near_hlt3' in response else 0])
	# datatier3.append([_('> 8 h'),response['g8_h__near_hlt3'] if 'g8_h__near_hlt3' in response else 0])
	# response['tier3_chart'] = gchart.PieChart(SimpleDataSource(data=datatier3), html_id="pie_chart6", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	# datatierall = []
	# datatierall.append(['time','population'])
	# datatierall.append([_('< 1 h'),response['l1_h__near_hltall'] if 'l1_h__near_hltall' in response else 0])
	# datatierall.append([_('< 2 h'),response['l2_h__near_hltall'] if 'l2_h__near_hltall' in response else 0])
	# datatierall.append([_('< 3 h'),response['l3_h__near_hltall'] if 'l3_h__near_hltall' in response else 0])
	# datatierall.append([_('< 4 h'),response['l4_h__near_hltall'] if 'l4_h__near_hltall' in response else 0])
	# datatierall.append([_('< 5 h'),response['l5_h__near_hltall'] if 'l5_h__near_hltall' in response else 0])
	# datatierall.append([_('< 6 h'),response['l6_h__near_hltall'] if 'l6_h__near_hltall' in response else 0])
	# datatierall.append([_('< 7 h'),response['l7_h__near_hltall'] if 'l7_h__near_hltall' in response else 0])
	# datatierall.append([_('< 8 h'),response['l8_h__near_hltall'] if 'l8_h__near_hltall' in response else 0])
	# datatierall.append([_('> 8 h'),response['g8_h__near_hltall'] if 'g8_h__near_hltall' in response else 0])
	# response['tierall_chart'] = gchart.PieChart(SimpleDataSource(data=datatierall), html_id="pie_chart7", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	# datatitsx_prov = []
	# datatitsx_prov.append(['time','population'])
	# datatitsx_prov.append([_('< 1 h'),response['l1_h__itsx_prov'] if 'l1_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('< 2 h'),response['l2_h__itsx_prov'] if 'l2_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('< 3 h'),response['l3_h__itsx_prov'] if 'l3_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('< 4 h'),response['l4_h__itsx_prov'] if 'l4_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('< 5 h'),response['l5_h__itsx_prov'] if 'l5_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('< 6 h'),response['l6_h__itsx_prov'] if 'l6_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('< 7 h'),response['l7_h__itsx_prov'] if 'l7_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('< 8 h'),response['l8_h__itsx_prov'] if 'l8_h__itsx_prov' in response else 0])
	# datatitsx_prov.append([_('> 8 h'),response['g8_h__itsx_prov'] if 'g8_h__itsx_prov' in response else 0])
	# response['itsx_prov_chart'] = gchart.PieChart(SimpleDataSource(data=datatitsx_prov), html_id="pie_chart8", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	# datatnear_prov = []
	# datatnear_prov.append(['time','population'])
	# datatnear_prov.append([_('< 1 h'),response['l1_h__near_prov'] if 'l1_h__near_prov' in response else 0])
	# datatnear_prov.append([_('< 2 h'),response['l2_h__near_prov'] if 'l2_h__near_prov' in response else 0])
	# datatnear_prov.append([_('< 3 h'),response['l3_h__near_prov'] if 'l3_h__near_prov' in response else 0])
	# datatnear_prov.append([_('< 4 h'),response['l4_h__near_prov'] if 'l4_h__near_prov' in response else 0])
	# datatnear_prov.append([_('< 5 h'),response['l5_h__near_prov'] if 'l5_h__near_prov' in response else 0])
	# datatnear_prov.append([_('< 6 h'),response['l6_h__near_prov'] if 'l6_h__near_prov' in response else 0])
	# datatnear_prov.append([_('< 7 h'),response['l7_h__near_prov'] if 'l7_h__near_prov' in response else 0])
	# datatnear_prov.append([_('< 8 h'),response['l8_h__near_prov'] if 'l8_h__near_prov' in response else 0])
	# datatnear_prov.append([_('> 8 h'),response['g8_h__near_prov'] if 'g8_h__near_prov' in response else 0])
	# response['near_prov_chart'] = gchart.PieChart(SimpleDataSource(data=datatnear_prov), html_id="pie_chart9", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	# datatnear_dist = []
	# datatnear_dist.append(['time','population'])
	# datatnear_dist.append([_('< 1 h'),response['l1_h__near_dist'] if 'l1_h__near_dist' in response else 0])
	# datatnear_dist.append([_('< 2 h'),response['l2_h__near_dist'] if 'l2_h__near_dist' in response else 0])
	# datatnear_dist.append([_('< 3 h'),response['l3_h__near_dist'] if 'l3_h__near_dist' in response else 0])
	# datatnear_dist.append([_('< 4 h'),response['l4_h__near_dist'] if 'l4_h__near_dist' in response else 0])
	# datatnear_dist.append([_('< 5 h'),response['l5_h__near_dist'] if 'l5_h__near_dist' in response else 0])
	# datatnear_dist.append([_('< 6 h'),response['l6_h__near_dist'] if 'l6_h__near_dist' in response else 0])
	# datatnear_dist.append([_('< 7 h'),response['l7_h__near_dist'] if 'l7_h__near_dist' in response else 0])
	# datatnear_dist.append([_('< 8 h'),response['l8_h__near_dist'] if 'l8_h__near_dist' in response else 0])
	# datatnear_dist.append([_('> 8 h'),response['g8_h__near_dist'] if 'g8_h__near_dist' in response else 0])
	# response['near_dist_chart'] = gchart.PieChart(SimpleDataSource(data=datatnear_dist), html_id="pie_chart10", options={'title': "", 'width': 290,'height': 290, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'top', 'maxLines':4}, 'slices':{0:{'color':'#e3f8ff'},1:{'color':'#defdf0'},2:{'color':'#caf6e4'},3:{'color':'#fcfdde'},4:{'color':'#fef7dc'},5:{'color':'#fce6be'},6:{'color':'#ffd6c5'},7:{'color':'#fdbbac'},8:{'color':'#ffa19a'}} })

	response['lc_child'] = getListAccesibility(filterLock, flag, code)
	# data = getListAccesibility(filterLock, flag, code)
	# response['lc_child']=data

	if include_section('GeoJson', includes, excludes):
		response['GeoJson'] = getGeoJson(request, flag, code)

	return response

def getListAccesibility(filterLock, flag, code):
	response = []
	admdata = getProvinceSummary(filterLock, flag, code)
	for i in admdata:
		data ={}
		data['code'] = i['code']
		data['na_en'] = i['na_en']
		data['Population'] = i['Population']
		data['Area'] = i['Area']

		rawAccesibility = GetAccesibilityData(filterLock, 'currentProvince', i['code'])
		for x in rawAccesibility:
			data[x]=rawAccesibility[x]

		data['pop_coverage_percent'] = int(round((data['pop_on_gsm_coverage']/data['Population'])*100,0))
		data['area_coverage_percent'] = int(round((data['area_on_gsm_coverage']/data['Area'])*100,0))

		# print 'l1_h__near_airp' in data

		data['l1_h__near_airp_percent'] = int(round((data['l1_h__near_airp']/data['Population'])*100,0)) if 'l1_h__near_airp' in data else 0
		data['l2_h__near_airp_percent'] = int(round((data['l2_h__near_airp']/data['Population'])*100,0)) if 'l2_h__near_airp' in data else 0
		data['l3_h__near_airp_percent'] = int(round((data['l3_h__near_airp']/data['Population'])*100,0)) if 'l3_h__near_airp' in data else 0
		data['l4_h__near_airp_percent'] = int(round((data['l4_h__near_airp']/data['Population'])*100,0)) if 'l4_h__near_airp' in data else 0
		data['l5_h__near_airp_percent'] = int(round((data['l5_h__near_airp']/data['Population'])*100,0)) if 'l5_h__near_airp' in data else 0
		data['l6_h__near_airp_percent'] = int(round((data['l6_h__near_airp']/data['Population'])*100,0)) if 'l6_h__near_airp' in data else 0
		data['l7_h__near_airp_percent'] = int(round((data['l7_h__near_airp']/data['Population'])*100,0)) if 'l7_h__near_airp' in data else 0
		data['l8_h__near_airp_percent'] = int(round((data['l8_h__near_airp']/data['Population'])*100,0)) if 'l8_h__near_airp' in data else 0
		data['g8_h__near_airp_percent'] = int(round((data['g8_h__near_airp']/data['Population'])*100,0)) if 'g8_h__near_airp' in data else 0

		data['l1_h__near_hlt1_percent'] = int(round((data['l1_h__near_hlt1']/data['Population'])*100,0)) if 'l1_h__near_hlt1' in data else 0
		data['l2_h__near_hlt1_percent'] = int(round((data['l2_h__near_hlt1']/data['Population'])*100,0)) if 'l2_h__near_hlt1' in data else 0
		data['l3_h__near_hlt1_percent'] = int(round((data['l3_h__near_hlt1']/data['Population'])*100,0)) if 'l3_h__near_hlt1' in data else 0
		data['l4_h__near_hlt1_percent'] = int(round((data['l4_h__near_hlt1']/data['Population'])*100,0)) if 'l4_h__near_hlt1' in data else 0
		data['l5_h__near_hlt1_percent'] = int(round((data['l5_h__near_hlt1']/data['Population'])*100,0)) if 'l5_h__near_hlt1' in data else 0
		data['l6_h__near_hlt1_percent'] = int(round((data['l6_h__near_hlt1']/data['Population'])*100,0)) if 'l6_h__near_hlt1' in data else 0
		data['l7_h__near_hlt1_percent'] = int(round((data['l7_h__near_hlt1']/data['Population'])*100,0)) if 'l7_h__near_hlt1' in data else 0
		data['l8_h__near_hlt1_percent'] = int(round((data['l8_h__near_hlt1']/data['Population'])*100,0)) if 'l8_h__near_hlt1' in data else 0
		data['g8_h__near_hlt1_percent'] = int(round((data['g8_h__near_hlt1']/data['Population'])*100,0)) if 'g8_h__near_hlt1' in data else 0

		data['l1_h__near_hlt2_percent'] = int(round((data['l1_h__near_hlt2']/data['Population'])*100,0)) if 'l1_h__near_hlt2' in data else 0
		data['l2_h__near_hlt2_percent'] = int(round((data['l2_h__near_hlt2']/data['Population'])*100,0)) if 'l2_h__near_hlt2' in data else 0
		data['l3_h__near_hlt2_percent'] = int(round((data['l3_h__near_hlt2']/data['Population'])*100,0)) if 'l3_h__near_hlt2' in data else 0
		data['l4_h__near_hlt2_percent'] = int(round((data['l4_h__near_hlt2']/data['Population'])*100,0)) if 'l4_h__near_hlt2' in data else 0
		data['l5_h__near_hlt2_percent'] = int(round((data['l5_h__near_hlt2']/data['Population'])*100,0)) if 'l5_h__near_hlt2' in data else 0
		data['l6_h__near_hlt2_percent'] = int(round((data['l6_h__near_hlt2']/data['Population'])*100,0)) if 'l6_h__near_hlt2' in data else 0
		data['l7_h__near_hlt2_percent'] = int(round((data['l7_h__near_hlt2']/data['Population'])*100,0)) if 'l7_h__near_hlt2' in data else 0
		data['l8_h__near_hlt2_percent'] = int(round((data['l8_h__near_hlt2']/data['Population'])*100,0)) if 'l8_h__near_hlt2' in data else 0
		data['g8_h__near_hlt2_percent'] = int(round((data['g8_h__near_hlt2']/data['Population'])*100,0)) if 'g8_h__near_hlt2' in data else 0

		data['l1_h__near_hlt3_percent'] = int(round((data['l1_h__near_hlt3']/data['Population'])*100,0)) if 'l1_h__near_hlt3' in data else 0
		data['l2_h__near_hlt3_percent'] = int(round((data['l2_h__near_hlt3']/data['Population'])*100,0)) if 'l2_h__near_hlt3' in data else 0
		data['l3_h__near_hlt3_percent'] = int(round((data['l3_h__near_hlt3']/data['Population'])*100,0)) if 'l3_h__near_hlt3' in data else 0
		data['l4_h__near_hlt3_percent'] = int(round((data['l4_h__near_hlt3']/data['Population'])*100,0)) if 'l4_h__near_hlt3' in data else 0
		data['l5_h__near_hlt3_percent'] = int(round((data['l5_h__near_hlt3']/data['Population'])*100,0)) if 'l5_h__near_hlt3' in data else 0
		data['l6_h__near_hlt3_percent'] = int(round((data['l6_h__near_hlt3']/data['Population'])*100,0)) if 'l6_h__near_hlt3' in data else 0
		data['l7_h__near_hlt3_percent'] = int(round((data['l7_h__near_hlt3']/data['Population'])*100,0)) if 'l7_h__near_hlt3' in data else 0
		data['l8_h__near_hlt3_percent'] = int(round((data['l8_h__near_hlt3']/data['Population'])*100,0)) if 'l8_h__near_hlt3' in data else 0
		data['g8_h__near_hlt3_percent'] = int(round((data['g8_h__near_hlt3']/data['Population'])*100,0)) if 'g8_h__near_hlt3' in data else 0

		data['l1_h__near_hltall_percent'] = int(round((data['l1_h__near_hltall']/data['Population'])*100,0)) if 'l1_h__near_hltall' in data else 0
		data['l2_h__near_hltall_percent'] = int(round((data['l2_h__near_hltall']/data['Population'])*100,0)) if 'l2_h__near_hltall' in data else 0
		data['l3_h__near_hltall_percent'] = int(round((data['l3_h__near_hltall']/data['Population'])*100,0)) if 'l3_h__near_hltall' in data else 0
		data['l4_h__near_hltall_percent'] = int(round((data['l4_h__near_hltall']/data['Population'])*100,0)) if 'l4_h__near_hltall' in data else 0
		data['l5_h__near_hltall_percent'] = int(round((data['l5_h__near_hltall']/data['Population'])*100,0)) if 'l5_h__near_hltall' in data else 0
		data['l6_h__near_hltall_percent'] = int(round((data['l6_h__near_hltall']/data['Population'])*100,0)) if 'l6_h__near_hltall' in data else 0
		data['l7_h__near_hltall_percent'] = int(round((data['l7_h__near_hltall']/data['Population'])*100,0)) if 'l7_h__near_hltall' in data else 0
		data['l8_h__near_hltall_percent'] = int(round((data['l8_h__near_hltall']/data['Population'])*100,0)) if 'l8_h__near_hltall' in data else 0
		data['g8_h__near_hltall_percent'] = int(round((data['g8_h__near_hltall']/data['Population'])*100,0)) if 'g8_h__near_hltall' in data else 0

		data['l1_h__itsx_prov_percent'] = int(round((data['l1_h__itsx_prov']/data['Population'])*100,0)) if 'l1_h__itsx_prov' in data else 0
		data['l2_h__itsx_prov_percent'] = int(round((data['l2_h__itsx_prov']/data['Population'])*100,0)) if 'l2_h__itsx_prov' in data else 0
		data['l3_h__itsx_prov_percent'] = int(round((data['l3_h__itsx_prov']/data['Population'])*100,0)) if 'l3_h__itsx_prov' in data else 0
		data['l4_h__itsx_prov_percent'] = int(round((data['l4_h__itsx_prov']/data['Population'])*100,0)) if 'l4_h__itsx_prov' in data else 0
		data['l5_h__itsx_prov_percent'] = int(round((data['l5_h__itsx_prov']/data['Population'])*100,0)) if 'l5_h__itsx_prov' in data else 0
		data['l6_h__itsx_prov_percent'] = int(round((data['l6_h__itsx_prov']/data['Population'])*100,0)) if 'l6_h__itsx_prov' in data else 0
		data['l7_h__itsx_prov_percent'] = int(round((data['l7_h__itsx_prov']/data['Population'])*100,0)) if 'l7_h__itsx_prov' in data else 0
		data['l8_h__itsx_prov_percent'] = int(round((data['l8_h__itsx_prov']/data['Population'])*100,0)) if 'l8_h__itsx_prov' in data else 0
		data['g8_h__itsx_prov_percent'] = int(round((data['g8_h__itsx_prov']/data['Population'])*100,0)) if 'g8_h__itsx_prov' in data else 0

		data['l1_h__near_prov_percent'] = int(round((data['l1_h__near_prov']/data['Population'])*100,0)) if 'l1_h__near_prov' in data else 0
		data['l2_h__near_prov_percent'] = int(round((data['l2_h__near_prov']/data['Population'])*100,0)) if 'l2_h__near_prov' in data else 0
		data['l3_h__near_prov_percent'] = int(round((data['l3_h__near_prov']/data['Population'])*100,0)) if 'l3_h__near_prov' in data else 0
		data['l4_h__near_prov_percent'] = int(round((data['l4_h__near_prov']/data['Population'])*100,0)) if 'l4_h__near_prov' in data else 0
		data['l5_h__near_prov_percent'] = int(round((data['l5_h__near_prov']/data['Population'])*100,0)) if 'l5_h__near_prov' in data else 0
		data['l6_h__near_prov_percent'] = int(round((data['l6_h__near_prov']/data['Population'])*100,0)) if 'l6_h__near_prov' in data else 0
		data['l7_h__near_prov_percent'] = int(round((data['l7_h__near_prov']/data['Population'])*100,0)) if 'l7_h__near_prov' in data else 0
		data['l8_h__near_prov_percent'] = int(round((data['l8_h__near_prov']/data['Population'])*100,0)) if 'l8_h__near_prov' in data else 0
		data['g8_h__near_prov_percent'] = int(round((data['g8_h__near_prov']/data['Population'])*100,0)) if 'g8_h__near_prov' in data else 0

		data['l1_h__near_dist_percent'] = int(round((data['l1_h__near_dist']/data['Population'])*100,0)) if 'l1_h__near_dist' in data else 0
		data['l2_h__near_dist_percent'] = int(round((data['l2_h__near_dist']/data['Population'])*100,0)) if 'l2_h__near_dist' in data else 0
		data['l3_h__near_dist_percent'] = int(round((data['l3_h__near_dist']/data['Population'])*100,0)) if 'l3_h__near_dist' in data else 0
		data['l4_h__near_dist_percent'] = int(round((data['l4_h__near_dist']/data['Population'])*100,0)) if 'l4_h__near_dist' in data else 0
		data['l5_h__near_dist_percent'] = int(round((data['l5_h__near_dist']/data['Population'])*100,0)) if 'l5_h__near_dist' in data else 0
		data['l6_h__near_dist_percent'] = int(round((data['l6_h__near_dist']/data['Population'])*100,0)) if 'l6_h__near_dist' in data else 0
		data['l7_h__near_dist_percent'] = int(round((data['l7_h__near_dist']/data['Population'])*100,0)) if 'l7_h__near_dist' in data else 0
		data['l8_h__near_dist_percent'] = int(round((data['l8_h__near_dist']/data['Population'])*100,0)) if 'l8_h__near_dist' in data else 0
		data['g8_h__near_dist_percent'] = int(round((data['g8_h__near_dist']/data['Population'])*100,0)) if 'g8_h__near_dist' in data else 0

		response.append(data)
	return response

def dashboard_accessibility(request, filterLock, flag, code, includes=[], excludes=[]):

	response = dict_ext()

	if include_section('getCommonUse', includes, excludes):
		response.update(getCommonUse(request, flag, code))

	response['source'] = accessibility = getAccessibility(request, filterLock, flag, code)
	baseline = accessibility['baseline']
	panels = response.path('panels')
	charts = panels.path('charts')
	tables = panels.path('tables')

	titles = {'pop':_('GSM Coverage Population'), 'area':_('GSM Coverage Area'), 'building':_('GSM Coverage Building')}
	keys = {'pop':'pop', 'area':'area', 'building':'buildings'}
	for k,v in keys.items():
		with charts.path('gsmcoverage_'+k) as chart:
			chart['title'] = titles[k]
			chart['total'] = baseline[k+'_total']
			chart['gsmcoverage'] = accessibility[v+'_on_gsm_coverage']
			chart['child'] = [
				[_('With GSM Coverage'), accessibility[v+'_on_gsm_coverage']], 
				[_('Without GSM Coverage'), baseline[k+'_total']-accessibility[v+'_on_gsm_coverage']],
			]

	titles = {
		'near_airp':_('Travel Time to Nearest Airport'),
		'near_hlt1':_('Travel Time to Nearest Health Facilities Tier 1'),
		'near_hlt2':_('Travel Time to Nearest Health Facilities Tier 2'),
		'near_hlt3':_('Travel Time to Nearest Health Facilities Tier 3'),
		'near_hltall':_('Travel Time to Nearest Health Facilities Tier All'),
		'itsx_prov':_('Travel Time to Its Provincial Capital'),
		'near_prov':_('Travel Time to Nearest Provincial Capital'),
		'near_dist':_('Travel Time to Nearest District Capital')
	}
	for k,v in titles.items():
		with charts.path(k) as chart:
			chart['title'] = v
			chart['child'] = [[TIME_DISTANCE_TITLES[i],accessibility[k][i]] for i in TIME_DISTANCE_TYPES]
		
	for k,v in titles.items():
		with tables.path(k) as table:
			table['title'] = v
			table['parentdata'] = [response['parent_label']]+[accessibility[k][i] for i in TIME_DISTANCE_TYPES]
			table['child'] = [{
				'code':i['code'],
				'value':[i['na_en']]+[i.get('%s_h__%s'%(j,k)) or 0 for j in TIME_DISTANCE_TYPES],
			} for i in accessibility['lc_child']]

	if include_section('GeoJson', includes, excludes):
		response['GeoJson'] = geojsonadd_accessibility(response)

	return response

def geojsonadd_accessibility(response):

	accessibility = response['source']
	baseline = response['source']['baseline']
	boundary = response['source']['GeoJson']
	accessibility['lc_child_dict'] = {v['code']:v for v in accessibility['lc_child']}
	keys = ['Area','Population','area_on_gsm_coverage','buildings_on_gsm_coverage','na_en','pop_on_gsm_coverage',]
	TRAVELTIMETO_TYPES = ['near_airp','near_hlt1','near_hlt2','near_hlt3','near_hltall','itsx_prov','near_prov','near_dist']

	for i,l in enumerate(boundary.get('features',[])):
		boundary['features'][i]['properties'] = prop = dict_ext(boundary['features'][i]['properties'])

		# Checking if it's in a district
		if response['areatype'] == 'district':
			response['set_jenk_divider'] = 1
			prop.update({'%s_h__%s'%(j,k):accessibility[k][j] for k in TRAVELTIMETO_TYPES for j in TIME_DISTANCE_TYPES})
			prop.update({k:accessibility[k] for k in ['area_on_gsm_coverage','buildings_on_gsm_coverage','pop_on_gsm_coverage',]})
			prop.update({k:baseline[v] for k,v in {'Area':'area_total','Population':'pop_total',}.items()})
			prop.update({k:response[v] for k,v in {'na_en':'parent_label',}.items()})

		else:
			response['set_jenk_divider'] = 7
			if (prop['code'] in accessibility['lc_child_dict']):
				child = accessibility['lc_child_dict'][prop['code']]
				prop.update({'%s_h__%s'%(j,k):child.get('%s_h__%s'%(j,k)) or 0 for k in TRAVELTIMETO_TYPES for j in TIME_DISTANCE_TYPES})
				prop.update({k:child[k] for k in keys})

	return boundary

class AccesibilityStatisticResource(ModelResource):

	class Meta:
		# authorization = DjangoAuthorization()
		resource_name = 'statistic_accesibility'
		allowed_methods = ['post']
		detail_allowed_methods = ['post']
		cache = SimpleCache()
		object_class=None
		# always_return_data = True
 
	def getRisk(self, request):

		p = urlparse(request.META.get('HTTP_REFERER')).path.split('/')
		mapCode = p[3] if 'v2' in p else p[2]
		map_obj = _resolve_map(request, mapCode, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

		queryset = matrix(user=request.user,resourceid=map_obj,action='Interactive Calculation')
		queryset.save()

		boundaryFilter = json.loads(request.body)

		wkts = ['ST_GeomFromText(\'%s\',4326)'%(i) for i in boundaryFilter['spatialfilter']]
		bring = wkts[-1] if len(wkts) else None
		filterLock = 'ST_Union(ARRAY[%s])'%(','.join(wkts))

		response = getAccesibilityStatistic(request, filterLock, boundaryFilter.get('flag'), boundaryFilter.get('code'), date=boundaryFilter.get('date'))

		return response

	def post_list(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		response = self.getRisk(request)
		return self.create_response(request, response)  

def getAccesibilityStatistic(request,filterLock, flag, code, date):

	panels = dashboard_accessibility(request, filterLock, flag, code, date, excludes=['GeoJson'])['panels']

	panels_list = dict_ext()
	panels_list['charts'] = [v for k,v in panels['charts'].items() if k in ['gsmcoverage_building','gsmcoverage_area','gsmcoverage_pop','near_airp','near_hlt1','near_hlt2','ear_hlt3','near_hltall','itsx_prov','near_prov','near_dist']]
	panels_list['tables'] = [{
		'title':v['title'],
		'child':[v['parentdata']] + [i['value'] for i in v['child']]
	} for k,v in panels['tables'].items() if k in ['near_airp','near_hlt1','near_hlt2','near_hlt3','near_hltall','itsx_prov','near_prov','near_dist']]

	return panels_list
