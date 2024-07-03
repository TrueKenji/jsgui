# JSGUI - A JSON Schema based GUI to create and edit JSON files

JSGUI provides a little tkinter based gui to allow for convenient configuration of json files using a schema file as base.

## Features

- Visualises JSON Schemas using 
  - checkboxes
  - textfields
  - drop-down menus
  - hover tips / tool tip texts
- Allows modification and saving as a .json file conforming to the underlying schema
- Allows to load an existing .json file into an underlying json schema for easy manipulation
- supports the following JSON Schema keywords:
  - properties
  - type
  - $comment
  - enum
  - patternProperties
  - $ref
  - required
  - default
  - <i> ... work in progress to enable more keywords </i>

## Install

`pip install jsgui`

## How to use

Simply start the application to open an empty window. Either drag-and-drop a json schema or use the Load Menu Button. The schema will be loaded with all `required` fields being active and `default` values inserted already.
Modify as you please and click "Save" to save.

After loading a schema you may also load a valid .json file to have its values inserted accordingly.

Note that drag-and-drop will try to guess whether you dropped a schema or a "data" json file by searching for typical schema keywords in the first level of the object.