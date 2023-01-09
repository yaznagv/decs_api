from django.db.models.functions import Length, Substr
from django.conf import settings

from tastypie.resources import Resource
from tastypie.paginator import Paginator
from tastypie.utils.mime import determine_format
from tastypie import fields

# Modelos de thesaurus utilizados en las diferentes opciiones del ws decs
from thesaurus.models import TreeNumbersListDesc, TreeNumbersListQualif

# funciones para la busqueda en ElasticSearch
from api.esearch_functions import *
# Serializador para que formato xml sea igual al del servicio de buaqueda rapida actual
from api.ws_decs_serializer import QuickDecsSerializer, WsDecsSerializer

# limitar traceback en las respuestas con error
# import sys
# sys.tracebacklimit=0


class NoPaginator(Paginator):

	def __init__(self, request_data, objects, resource_uri=None, limit=None, offset=0, max_limit=1000,
	             collection_name='objects'):
		# limit = 1000, Show all results
		super(NoPaginator, self).__init__(request_data, objects, resource_uri, 20, offset, max_limit, collection_name)

	def page(self):
		output = super(NoPaginator, self).page()

		# no mostrar datos de meta (total de registros, ctdad en una pag, ...)
		#del output['meta']

		return output


class QuickTermObject(object):
	def __init__(self, identifier=None, term_type=None, term_string=None):
		self.identifier = identifier
		self.term_type = term_type
		self.term_string = term_string


class QuickTermResource(Resource):
	identifier = fields.IntegerField(attribute='identifier')
	term_type = fields.CharField(attribute='term_type', null=True, blank=True)
	term_string = fields.CharField(attribute='term_string', null=True, blank=True)

	class Meta:
		resource_name = 'quickterm'
		allowed_methods = ['get']
		object_class = QuickTermObject
		include_resource_uri = False
		serializer = QuickDecsSerializer(formats=['xml', 'json'])
		# elimina datos de paginacion
		paginator_class = NoPaginator

	def determine_format(self, request):
		"""
		return application/xml as the default format, request uri does not need format=xml
		"""
		fmt = determine_format(request, self._meta.serializer, default_format='application/xml')

		return fmt

	def get_object_list(self, bundle, **kwargs):
		results = []
		terms = self.get_search(bundle.request, **kwargs)

		for term in terms:
			new_obj = QuickTermObject(term['identifier'], term['term_type'], term['term_string'])
			results.append(new_obj)

		return results

	def obj_get_list(self, bundle, **kwargs):
		return self.get_object_list(bundle, **kwargs)

	def get_search(self, request, **kwargs):
		self.method_check(request, allowed=['get'])

		# default thesaurus 1 (decs)
		ths = request.GET.get('ths', '1')

		# default status 1 (decs)
		status = request.GET.get('status', '1')

		response = []
		if 'query' in request.GET:
			query = request.GET.get('query', '')
			quick_search = get_search_q('quick', query, None, status, None, ths)
			response = execute_quick_search(quick_search)

		self.log_throttled_access(request)
		# para probar search desde la url
		#return self.create_response(request, response)
		return response

	def dehydrate(self, bundle):

		if bundle.obj.term_type == 'descriptor':
			term_string = bundle.obj.term_string
			# descriptor models
			TreeNumbersList = TreeNumbersListDesc
		else:
			term_string = "/" + bundle.obj.term_string
			# qualifier models
			TreeNumbersList = TreeNumbersListQualif

		# If term has many tree_number, we get first tree_number
		treeN_list = TreeNumbersList.objects.filter(identifier_id=bundle.obj.identifier).order_by('tree_number')
		tree_number = treeN_list[0].tree_number

		item = {
			'attr': {
				'id': tree_number,
				'term': term_string,
			}
		}

		bundle.data.pop('identifier')
		bundle.data.pop('term_type')
		bundle.data.pop('term_string')

		bundle.data['item'] = item

		return bundle
