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
        context['schemas'] = Registry().schemas
        return context


class JSONSchemaView(View):
    """
    Show a JSON Schema
    """

    http_method_names = ['get']

    def get(self, request: HttpRequest, schema: str, version: str):
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
        return JsonSchemaResponse(version, json_dumps_params={'indent': 2})
