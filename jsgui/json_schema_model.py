from typing import Union
import jsonschema.exceptions
import numpy as np
from copy import deepcopy
import jsonschema
from jsonschema import validate
from decomply import Decomply, enumerable


class JSONSchemaModel:
    def __init__(self, json_schema: Union[dict, list] = None) -> None:
        self.schema = None
        self.original_schema = None  # for validation when saving
        self.original_schema_initialized = None  # for $ref
        self.set_schema(json_schema)

    def set_schema(self, json_schema: Union[dict, list]) -> None:
        """
        Initialize the schema variants
        Args:
            json_schema (Union[dict, list]): The original schema
        """
        self.schema = deepcopy(json_schema)
        self.original_schema = deepcopy(json_schema)
        if json_schema:
            self.initialize()
            self.original_schema_initialized = deepcopy(self.schema)

    def initialize(self) -> None:
        """
        include the active and value keys in the schema. required and default values are inserted
        :return: None
        """
        traverse_keywords = ["type", "oneOf", "$ref"]
        recursive_keywords = ["oneOf", "properties"]

        def traverse(trace, item):
            return np.all([keyword not in item for keyword in traverse_keywords])

        def apply(trace: list, item: dict):
            if hasattr(item, "items"):
                required = self.is_required(trace)
                item["active"] = required
                for recursive_keyword in recursive_keywords:
                    if recursive_keyword in item:
                        trace.append(recursive_keyword)
                        item[recursive_keyword] = decomply.decomply(
                            item[recursive_keyword], trace, initial_check=False)
                        trace.pop()
                # if required and "additionalProperties" in item and "$ref" in item["additionalProperties"]:
                #    item["additionalProperties"]["$ref"] = self.resolve_reference(item["additionalProperties"]["$ref"])
                if "default" in item:
                    item["value"] = item["default"]
                    item["active"] = True
            return item

        decomply = Decomply(traverse=traverse, apply=apply)
        self.schema = decomply.decomply(
            self.schema, initial_check=False
        )

    def get(self, trace: list[Union[str, int]]) -> any:
        """Lookup a value in the nested dict schema.
        Args:
            trace (list[Union[str, int]]): the list of keys

        Returns:
            any: the found value or None
        """
        return JSONSchemaModel.staticGet(self.schema, trace)

    @staticmethod
    def staticGet(schema, trace: list[Union[str, int]]) -> any:
        """@get
        """
        item = schema
        for identifier in trace:
            handler = enumerable.get_handler(item)
            if not handler.contains_key(identifier, item):
                return None
            item = item[identifier]
        return item

    def is_required(self, trace: list[Union[str, int]]) -> bool:
        """Check whether the property associated with the trace is required.
        Since the required property in a schema is one level above, need to adjust
        Note that False is also returned if the trace is invalid
        Args:
            trace (list[Union[str, int]]): the list of keys

        Returns:
            bool: whether the property is required
        """
        if len(trace) < 3:
            keys = list()
        else:
            keys = deepcopy(trace[:-2])
        keys.append("required")
        required = self.get(keys)
        res = required != None and trace[-1] in required
        return res

    def resolve_reference(self, ref):
        referencedItem = JSONSchemaModel.staticGet(
            self.original_schema_initialized, ref.replace("#/", "").split("/"))
        if not referencedItem:
            raise Exception("Could not resolve reference %s" % ref)
        return referencedItem

    def check(self, trace: list[Union[str, int]]) -> bool:
        """Activate or deactive the property associated with the given trace
        Special treatment is required for .* and for $ref
        Args:
            trace (list[Union[str, int]]): the list of keys

        Raises:
            Exception: if $ref is not resolvable

        Returns:
            bool: the new active-status
        """
        parent = self.get(trace[:-1])
        item = parent[trace[-1]]
        if trace[-2] == "additionalProperties":
            if "active" in item:
                if item["active"]:
                    del parent[trace[-1]]
                # else case can't happen?
            if "$ref" in parent:
                ref = parent["$ref"]
                referencedItem = self.resolve_reference(ref)
                #if item["active"]:  # has been selected
                    # insert the ref information
                parent[trace[-1]] = deepcopy(referencedItem)
                parent[trace[-1]]["active"] = True
                item = parent[trace[-1]]
                    # parent[trace[-1]]["$ref"] = ref
                #else:  # has been deselected
                #    parent[trace[-1]] = {
                #        "$ref": ref,
                #        "active": False
                #    }
        else:
            item["active"] = not item["active"]
        return item["active"]

    def add_key(self, trace: list[Union[str, int]], key_name: str) -> list[Union[str, int]]:
        """Create a new key by duplicating the property associated with the given trace
        Used to handle .*
        Args:
            trace (list[Union[str, int]]): the list of keys
            key_name (str): the name of the new key

        Returns:
            list[Union[str, int]]: the list of keys with the new key incorporated
        """
        new_trace = trace[:-1] + [key_name]
        # if self.get(new_trace):
        #    self.get(new_trace)["active"] = True
        #    return new_trace
        parent = self.get(trace[:-1])
        # add the requested key into the schema using the .* value
        parent[key_name] = deepcopy(parent[trace[-1]])
        # exchange the old key with the new and return entire trace
        return new_trace

    def update_key(self, trace: list[Union[str, int]], key_name: str) -> None:
        """Change the name of the key associated with the given trace

        Args:
            trace (list[Union[str, int]]): a list of keys
            key_name (str): the new key name
        """
        parent = self.get(trace[:-1])
        # just reassign the key and drop the old one
        parent[key_name] = parent[trace[-1]]
        del parent[trace[-1]]
        return trace[:-1] + [key_name]

    def set_value(self, trace: list[Union[str, int]], value: any) -> any:
        """set the value for the property associated with the given trace
        Need to ensure the .get method exists
        Args:
            trace (list[Union[str, int]]): a list of keys
            value (any): the value to assign

        Returns:
            any: Either the assigned value or None, if trace is invalid
        """
        item = self.get(trace)
        if item:
            item["value"] = value
            return value
        return None

    def print(self) -> None:

        def flatten(d, s="", indent=0):
            for key, value in d.items():
                s += "\n" + ("\t" * indent) + str(key) + " : "
                if isinstance(value, dict):
                    s += "{" + flatten(value, indent=indent + 1)
                # elif isinstance(value, list):
                #     s += "["
                else:
                    s += str(value)
            return s + "\n" + ("\t" * indent) + "}"

        print("SCHEMA\n", flatten(self.schema, "{"))

    def save(self) -> str:
        """In order to save, we must skip every 2nd layer (the metadata). Also we need to delete all metadata
        Then, the actual name of a key must map directly to the value, instead of mapping to a new dict, like the schema does
        For that, we jump off the traverse when we have the dict of a key. we return item["value"] which is assigned
        to the key directly within decomply logic
        Returns: 
            str: either the json or an error message, if the schema is violated
        """
        def isValueEmptyString(item):
            return isinstance(item["value"], str) and len(item["value"]) == 0

        def isValueEmptyWidget(item):
            return hasattr(item["value"], "get") and len(item["value"].get()) == 0

        def isEmpty(item):
            return "value" in item and (isValueEmptyString(item) or isValueEmptyWidget(item))

        traverse = (
            lambda _, item: "type" not in item and "oneOf" not in item
        )  # or "$id" in item or item["type"] == "object"
        delete = (
            lambda trace, item: trace[-1] == "type"
            or trace[-1] == "$id"
            or ("active" in item and not item["active"])
            or trace[-1] == "required"
            or isEmpty(item)
            or trace[-1] == "$ref"
        )

        def apply(trace, item):
            res = dict()
            if "properties" in item:
                res.update(decomply.decomply(item["properties"]))
            if "additionalProperties" in item:
                res.update(decomply.decomply(item["additionalProperties"]))
            if "oneOf" in item:
                options = decomply.decomply(item["oneOf"])
                if len(options) == 0:
                    return []
                # retrieve just the unique value
                res.update(options[0])

            if len(res) > 0:
                return res

            if not "value" in item:
                return None
            if item["type"] == "number":
                try:
                    return float(item["value"])
                except:
                    pass
            return item["value"]

        decomply = Decomply(traverse=traverse, apply=apply, delete=delete)
        out_json = decomply.decomply(
            self.schema["properties"]
        )
        try:
            validate(instance=out_json, schema=self.original_schema)
        except jsonschema.exceptions.ValidationError as e:
            return str(e.relative_path) + " " + e.message
        except jsonschema.exceptions.SchemaError as e:
            return str(e.relative_path) + " " + e.message
        else:
            return out_json

    def merge(self, other_model: "JSONSchemaModel", key_to_merge: str = "value") -> None:
        """Loop through the entire model and include the key_to_merge from the other_model, if the key architecture is equal
        Used for loading
        example:
        {
            a: 1, 
            b: { 
                c: 2,
                d: 3
            }
        }.merge({
            b: {
                e: 4
            }
        }, key_to_merge="e")
        =
        {
            a: 1,
            b: {
                c: 2,
                d: 3,
                e: 4
            }
        }

        Args:
            other_model (JSONSchemaModel): the model to merge with. the key architecture of that model must in principle be equal to this model
            key_to_merge (str, optional): the key to search for in other model. the key and its value will be copied into this model in the same key hierachy level. Defaults to "value".
        """

        def apply(trace, item):
            other_item = other_model.get(trace)
            if isinstance(other_item, dict):
                if key_to_merge in other_item:
                    item[key_to_merge] = other_item[key_to_merge]
                return decomply.decomply(item, trace=trace, initial_check=False)
            return item

        decomply = Decomply(traverse=lambda _, __: False, apply=apply)
        self.schema = decomply.decomply(self.schema, initial_check=False)
