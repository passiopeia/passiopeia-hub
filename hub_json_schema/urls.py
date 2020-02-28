"""
URL Config for the hub_json_schema, which delivers JSON Schemas
"""
from django.conf.urls import url

from hub_json_schema.views import ListJSONSchemasView, JSONSchemaView

urlpatterns = [  # pylint: disable=invalid-name
    url(r'(?P<schema>[a-z][a-z0-9\-]{0,50}[a-z0-9])-v(?P<version>\d+)$', JSONSchemaView.as_view(), name='schema'),
    url(r'^$', ListJSONSchemasView.as_view(), name='list'),
]
