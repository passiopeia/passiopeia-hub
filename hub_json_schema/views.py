"""
Views for the JSON Schema Delivery
"""
from django.http import HttpRequest, Http404, JsonResponse
from django.views import View
from django.views.generic import TemplateView

from hub_json_schema.registry import Registry


class JsonSchemaResponse(JsonResponse):
    """
    A JSON schema response
    """

    content_type = 'application/schema+json'


class ListJSONSchemasView(TemplateView):
    """
    List available JSON Schemas
    """

    content_type = 'text/html'
    template_name = 'hub_json_schema/list-view.html'

    def get_context_data(self, **kwargs):
        context = super(ListJSONSchemasView, self).get_context_data(**kwargs)
        schema_list = []
        for schema_name, schema_versions in Registry().schemas.items():
            schema_version_list = []
            for schema_version, schema_data in schema_versions.items():
                schema_version_list.append({
                    'sortable_version': schema_version,
                    'has_example': schema_data.get('example', None) is not None
                })
            schema_info = {
                'sortable_name': schema_name,
                'schema_versions': schema_version_list,
            }
            schema_list.append(schema_info)
        context['schema_list'] = schema_list
        return context


class JSONSchemaView(View):
    """
    Show a JSON Schema
    """

    http_method_names = ['get']

    def get(self, request: HttpRequest, schema: str, version: str, example: str = None):
        """
        Send the schema
        """
        registry = Registry()
        schema = registry.schemas.get(schema, None)
        if schema is None:
            raise Http404()
        version = schema.get(version, None)
        if version is None:
            raise Http404()
        if example == '.json':
            example = version.get('example', None)
            if example is None:
                raise Http404()
            return JsonResponse(example, json_dumps_params={'indent': 2})
        return JsonSchemaResponse(version.get('def'), json_dumps_params={'indent': 2})
