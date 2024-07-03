import json
from view.tkview import TKView
from decomply import Decomply
from json_schema_model import JSONSchemaModel


def is_json_schema(json_content: dict) -> bool:
    """whether the supplied dict is a json schema

    Args:
        json_content (dict): the content to test

    Returns:
        bool: whether the supplied dict is a json schema
    """
    schema_keywords = {"$schema", "$id", "type", "properties", "items", "required",
                       "definitions", "$ref", "additionalProperties", "patternProperties"}

    if isinstance(json_content, dict):
        if any(keyword in json_content for keyword in schema_keywords):
            return True
    return False


class Controller:

    def __init__(self):
        self.model = JSONSchemaModel()
        self.view = TKView(self)
        pass

    def mainloop(self):
        self.view.mainloop()

    def load(self, full_file: str, schema_flg: bool = None) -> None:
        """load from the given file. If schema_flg is not given, 
        code will try to guess whether the file is actually a schema

        Args:
            full_file (str): a full file path
            schema_flg (bool, optional): whether the file is a schema. Defaults to None.
        """
        with open(full_file) as json_file:
            json_data = json.load(json_file)

        if schema_flg or is_json_schema(json_data):
            self._load_schema(json_data)
        else:
            self._load_json(json_data)

        self.view.paint(self.model)

    def _load_schema(self, json_data: dict) -> None:
        self.model.set_schema(json_data)

    def _load_json(self, json_data: dict) -> None:
        """
        Load json data into the model, using the @merge method. Since the file misses the "in-between" layers "properties"
        of the schema file, the data has to be enriched with these layers. Additionally, the value and active flags must be
        incorporated
        example:
            {
                name: hans
            }
        should be transformed to
            {
                properties: {
                    name: {
                        value: hans,
                        active: true
                    }
                }
            }

        Args:
            json_data (dict): the json data to load
        """
        def apply(trace, item):
            if isinstance(item, dict):
                return {
                    "properties": decomply.decomply(item, initial_check=False),
                    "active": True,
                }
            else:
                return {"value": item, "active": True}

        decomply = Decomply(traverse=lambda _, __: False, apply=apply)
        value_data = decomply.decomply(json_data, initial_check=False)
        wrapped_data = {"properties": value_data}
        value_model = JSONSchemaModel(wrapped_data)

        self.model.merge(value_model, key_to_merge="active")
        self.model.merge(value_model, key_to_merge="value")

    def save(self) -> None:
        if self.is_valid():
            full_filepath = self.view.save()
            if (full_filepath):
                self._save(full_filepath)

    def _save(self, full_filepath: str) -> None:
        out = self.model.save()
        with open(full_filepath.name, "w") as fp:
            json.dump(out, fp, indent=4)
        full_filepath.close()
        self.view.paint(self.model)

    def is_valid(self) -> bool:
        out = self.model.save()
        if isinstance(out, dict):
            return True
        else:
            self.view.popup_showerror(title="Invalid JSON", msg=out)
        return False

    def check(self, ids: list) -> None:
        self.model.check(ids)
        self.view.paint(self.model)

    def widget_value_changed(self, trace: list, new_value: any) -> None:
        self.model.set_value(trace, new_value)

    def key_field_changed(self, trace: list, key_text: str) -> None:
        """key fields are associated with patternProperties.
        If the placeholder field has changed, introduce an entirely new concrete field
        If an existing field has changed, just update the key

        Args:
            trace (list): a list of keys
            key_text (str): the key_text to use for the patternProperties property
        """
        if len(key_text) > 0 and trace[-2] == "patternProperties":
            # distinguish wildcard placeholder or existing property
            if not self.model.get(trace)["active"]:
                newTrace = self.model.add_key(trace, key_text)
                self.check(newTrace)
            else:
                self.model.update_key(trace, key_text)
        self.view.paint(self.model)


if __name__ == "__main__":
    controller = Controller()
    controller.mainloop()
