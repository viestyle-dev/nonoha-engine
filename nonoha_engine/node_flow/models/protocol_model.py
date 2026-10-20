from pydantic import BaseModel

from nonoha_core.data_type import PropertyDataType


class InputPortValueModel(BaseModel):
    name: str | None = None
    type: str
    dispatch_flag: bool = False


class InputPortModel(BaseModel):
    name: str
    values: list[InputPortValueModel]


class OutputPortValueModel(BaseModel):
    name: str | None = None
    type: str


class OutputPortModel(BaseModel):
    name: str
    values: list[OutputPortValueModel]


class EdgeModel(BaseModel):
    source: str
    target: str
    valid: bool = True


class PropertyGroupModel(BaseModel):
    keys: list[str]
    dispatch_flags: list[bool]


class NodeModel(BaseModel):
    name: str
    type: str
    properties: dict[str, PropertyDataType]
    inputs: list[InputPortModel]
    outputs: list[OutputPortModel]
    property_groups: list[PropertyGroupModel] = []


class CreateNodeRequest(BaseModel):
    type: str
    preferred_name: str | None = None
    properties: dict[str, PropertyDataType] | None = None


class PatchInputPortValue(BaseModel):
    dispatch_flag: bool | None = None


class PatchInputPortModel(BaseModel):
    values: list[PatchInputPortValue] | None = None


class PatchPropertyGroupsModel(BaseModel):
    property_groups: list[PropertyGroupModel]


# https://stackoverflow.com/questions/21592030/map-or-array-for-restful-design-of-finite-unordered-collection
# https://stackoverflow.com/questions/30442072/http-api-response-list-vs-map
