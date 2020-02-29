"""
Tests for the JSON Schema App
"""
from bs4 import BeautifulSoup
from django.conf import settings
from django.http import JsonResponse
from django.test import SimpleTestCase, TestCase
from jsonschema import Draft7Validator, RefResolver

from hub_json_schema.published_schema import PUBLISHED
from hub_json_schema.schema.base.schema import JsonSchema


class PublishedSchemaTest(SimpleTestCase):
    """
    Test all published schemas
    """

    def test_schemas(self):
        """
        Test the schemas
        """
        for schema in PUBLISHED:
            with self.subTest(msg='Testing schema "{}"'.format(schema)):
                self.assertIsNotNone(schema)
                self.assertIn(JsonSchema, schema.__bases__)
                self.assertIsNotNone(getattr(schema, 'schema_name'))
                self.assertIsNotNone(getattr(schema, 'schema_version'))
                self.assertIsNotNone(getattr(schema, 'schema_definition'))
                self.assertGreater(int(schema.schema_version), 0)
                self.assertIsInstance(schema.schema_name, str)
                self.assertIsInstance(schema.schema_definition, dict)
                self.assertTrue(schema.schema_definition.get('$id').startswith(settings.JSON_SCHEMA_BASE))


class SchemaViewTest(TestCase):
    """
    Test Schema Views
    """

    def test_all_schema_links(self):
        """
        Test access to all schemas
        """
        with self.subTest(msg='Fetching Overview'):
            response = self.client.get('/schema/', follow=False)
            self.assertEqual(200, response.status_code)
        with self.subTest(msg='Checking that all published elements are available'):
            soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find_all('a', attrs={
                'data-link-type': 'schema'
            })
            self.assertEqual(len(soup), len(PUBLISHED))
        for link_element in soup:
            link = link_element['href']
            with self.subTest(msg='Testing link "{}"'.format(link)):
                response = self.client.get(link, follow=False)
                self.assertEqual(200, response.status_code)
                self.assertEqual('application/schema+json', response.content_type)
                bad_version_link = link.replace('-v1', '-v99999999')
                with self.subTest(msg='Testing a bad version for the link: "{}"'.format(bad_version_link)):
                    response = self.client.get(bad_version_link, follow=False)
                    self.assertEqual(404, response.status_code)

    def test_all_example_links(self):
        """
        Test access to all examples
        """
        with self.subTest(msg='Fetching Overview'):
            response = self.client.get('/schema/', follow=False)
            self.assertEqual(200, response.status_code)
            soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find_all('a', attrs={
                'data-link-type': 'example'
            })
        for link_element in soup:
            link = link_element['href']
            with self.subTest(msg='Testing example link "{}"'.format(link)):
                response = self.client.get(link, follow=False)
                self.assertEqual(200, response.status_code)
                self.assertIsInstance(response, JsonResponse)

    def test_non_existing_schema_name(self):
        """
        Test a schema that does not exist
        """
        response = self.client.get('/schema/not-existing-v1', follow=False)
        self.assertEqual(404, response.status_code)

    def test_non_existing_schema_name_example(self):
        """
        Test a schema example that does not exist
        """
        response = self.client.get('/schema/not-existing-v1.json', follow=False)
        self.assertEqual(404, response.status_code)

    def test_non_existing_schema_name_without_example(self):
        """
        Test a schema example that does not exist
        """
        response = self.client.get('/schema/type-username-v1.json', follow=False)
        self.assertEqual(404, response.status_code)


class ValidateAllSchemasAndExamplesTest(SimpleTestCase):
    """
    Validate all examples with a JSON schema validation
    """

    @classmethod
    def setUpClass(cls):
        super(ValidateAllSchemasAndExamplesTest, cls).setUpClass()
        schema_store = {}
        for schema in PUBLISHED:
            schema_store[schema.schema_definition.get('$id')] = schema.schema_definition
        cls.resolver = RefResolver('', settings.JSON_SCHEMA_BASE, store=schema_store)

    def test_check_schema(self):
        """
        Check all Schemas
        """
        for schema in PUBLISHED:
            with self.subTest(msg='Checking Schema "{}-v{}"'.format(schema.schema_name, schema.schema_version)):
                Draft7Validator.check_schema(schema.schema_definition)

    def test_all_examples(self):
        """
        Test all examples
        """
        for schema in PUBLISHED:
            example = schema.example
            if example is not None:
                with self.subTest('Checking example(s) for Schema "{}-v{}"'.format(
                        schema.schema_name, schema.schema_version
                )):
                    validator = Draft7Validator(schema.schema_definition, resolver=self.resolver)
                    validator.validate(example)
