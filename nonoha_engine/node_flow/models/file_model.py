from typing import Any, TypeAlias

from pydantic import BaseModel, model_validator

from nonoha_core.data_type import PropertyDataType


class EdgeModel(BaseModel):
    source: str
    target: str


class NodeInputPortModel(BaseModel):
    dispatch_flags: list[bool] = []

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy(cls, data):
        if isinstance(data, dict) and "values" in data and "dispatch_flags" not in data:
            data["dispatch_flags"] = [v.get("dispatch_flag", False) for v in data["values"]]
            del data["values"]
        return data


class PropertyGroupModel(BaseModel):
    keys: list[str]
    dispatch_flags: list[bool]


class NodeModel(BaseModel):
    type: str
    properties: dict[str, PropertyDataType]
    inputs: dict[str, NodeInputPortModel] = {}
    property_groups: list[PropertyGroupModel] = []

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_groups(cls, data):
        """Migrate old format: [["a","b"]] → [{"keys":["a","b"],"dispatch_flags":[false,false]}]"""
        if isinstance(data, dict) and "property_groups" in data:
            groups = data["property_groups"]
            if groups and isinstance(groups[0], list):
                data["property_groups"] = [
                    {"keys": g, "dispatch_flags": [False] * len(g)} for g in groups
                ]
        return data


class PortModel(BaseModel):
    types: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy(cls, data):
        if isinstance(data, dict) and "values" in data and "types" not in data:
            data["types"] = [v["type"] for v in data["values"]]
            del data["values"]
        return data


class NodeGraphModel(BaseModel):
    properties: dict[str, PropertyDataType]
    nodes: dict[str, NodeModel]
    inputs: dict[str, PortModel]
    outputs: dict[str, PortModel]
    edges: list[EdgeModel]


class NodeFlowModel(BaseModel):
    graphs: list[str]


EditorModel: TypeAlias = dict[str, Any]
