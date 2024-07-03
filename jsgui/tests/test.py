import unittest
from jsgui.json_schema_model import JSONSchemaModel


class TestJSONSchemaModel(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None  # Allow for full diff output
        self.input_schema = {
            "$id": "testSchema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "$comment": "Name of someone",
                    "default": "anonymous"
                },
                "age": {
                    "type": "number",
                    "$comment": "Age of someone"
                },
                "preferredColor": {
                    "type": "string",
                    "enum": [
                        "Red",
                        "Blue",
                        "Green"
                    ],
                    "default": "Red"
                },
                "freekeys": {
                    "type": "object",
                    "properties": {
                        ".*": {
                            "type": "string",
                        }
                    }
                }
            },
            "required": ["name"]
        }
        self.model = JSONSchemaModel(self.input_schema)

    def test_init_model(self):
        expected = JSONSchemaModel()
        expected.schema = {
            '$id': 'testSchema',
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    '$comment': 'Name of someone',
                    'default': 'anonymous',
                    'active': True,
                    'value': 'anonymous'
                },
                'age': {
                    'type': 'number',
                    '$comment': 'Age of someone',
                    'active': False
                },
                'preferredColor': {
                    'type': 'string',
                    'enum': ['Red', 'Blue', 'Green'
                             ],
                    'default': 'Red',
                    'active': True,
                    'value': 'Red'
                },
                "freekeys": {
                    "type": "object",
                    "properties": {
                        ".*": {
                            "type": "string",
                            "active": False
                        }
                    },
                    "active": False
                }
            },
            "required": ["name"]
        }

        expected.original_schema = self.input_schema
        expected.original_schema_initialized = {
            "$id": "testSchema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "$comment": "Name of someone",
                    "default": "anonymous",
                    "active": True,
                    "value": "anonymous"
                },
                "age": {
                    "type": "number",
                    "$comment": "Age of someone",
                    "active": False
                },
                "preferredColor": {
                    "type": "string",
                    "enum": [
                        "Red",
                        "Blue",
                        "Green"
                    ],
                    "default": "Red",
                    "active": True,
                    "value": "Red"
                },
                "freekeys": {
                    "type": "object",
                    "properties": {
                        ".*": {
                            "type": "string",
                            "active": False
                        }
                    },
                    "active": False
                }
            },
            "required": ["name"]
        }

        self.assertDictEqual(self.model.schema, expected.schema)
        self.assertDictEqual(self.model.original_schema,
                             expected.original_schema)
        self.assertDictEqual(
            self.model.original_schema_initialized, expected.original_schema_initialized)

    def test_get(self):
        trace = ["properties", "preferredColor", "active"]
        expected = True

        self.assertEqual(self.model.get(trace=trace), expected)

    def test_is_required(self):
        trace = ["properties", "preferredColor"]
        self.assertFalse(self.model.is_required(trace))

        trace = ["properties", "name"]
        self.assertTrue(self.model.is_required(trace))

    def test_check(self):
        trace = ["properties", "preferredColor"]
        self.assertFalse(self.model.check(trace))

        trace = ["properties", "age"]
        self.assertTrue(self.model.check(trace))

    def test_add_key(self):
        trace = ["properties", "freekeys", "properties", ".*"]
        expected = ["properties", "freekeys", "properties", "hobby"]
        self.assertListEqual(self.model.add_key(
            trace=trace, key_name="hobby"), expected)
        self.assertEqual(self.model.get(trace), self.model.get(expected))

    def test_update_key(self):
        trace = ["properties", "freekeys", "properties", ".*"]
        trace = self.model.add_key(trace=trace, key_name="hobby")
        child = self.model.get(trace)
        new_trace = self.model.update_key(trace=trace, key_name="newkey")
        self.assertEqual(self.model.get(new_trace), child)

    def test_set_value(self):
        trace = ["properties", "preferredColor"]
        expected = "Blue"
        self.assertEqual(self.model.set_value(trace, expected), expected)

    def test_save(self):
        expected = {
            "name": "anonymous",
            "preferredColor": "Red"
        }
        self.assertDictEqual(self.model.save(), expected)

    def test_merge(self):
        load_json = JSONSchemaModel({
            "properties": {
                "name": {
                    "active": True,
                    "value": "Kenji"
                },
                "age": {
                    "active": True,
                    "value": "-5"
                }
            }
        })
        expected = {
            "$id": "testSchema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "$comment": "Name of someone",
                    "default": "anonymous",
                    "active": True,
                    "value": "Kenji"
                },
                "age": {
                    "type": "number",
                    "$comment": "Age of someone",
                    "active": True,
                    "value": "-5"
                },
                "preferredColor": {
                    "type": "string",
                    "enum": [
                        "Red",
                        "Blue",
                        "Green"
                    ],
                    "default": "Red",
                    "active": True,
                    "value": "Red"
                },
                "freekeys": {
                    "type": "object",
                    "properties": {
                        ".*": {
                            "type": "string",
                            "active": False
                        }
                    },
                    "active": False
                }
            },
            "required": ["name"]
        }
        
        self.model.merge(load_json, key_to_merge="value")
        self.model.merge(load_json, key_to_merge="active")
        self.assertDictEqual(self.model.schema, expected)


if __name__ == '__main__':
    unittest.main()
