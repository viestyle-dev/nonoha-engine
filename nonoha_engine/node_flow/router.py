import asyncio
import errno
from typing import Any
from fastapi import APIRouter, Body, HTTPException, Request, Response, UploadFile, WebSocket
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
import traceback

from .node_flow import NodeFlow
from .models import protocol_model
from .node import PropertyDataType
from .data_storage import DataStorage, purge_trash_entry
from nonoha_core.data_type import name_to_port_value_type
from nonoha_core.port import (
    StaticTypeInputPort,
    StaticTypeOutputPort,
    port_values_to_bytes,
)


def generate_router(node_flow: NodeFlow):
    router = APIRouter(prefix="/node-flow")

    @router.post("/graphs")
    async def post_graphs():
        return {"status": "ok"}

    @router.get("/graphs")
    async def get_graphs() -> list[str]:
        return list(node_flow.graph_names)

    @router.get("/graphs/{graph_name}/nodes")
    async def get_graphs_graph_nodes(graph_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        return list(graph.get_node_names())

    @router.post("/graphs/{graph_name}/nodes")
    async def post_graphs_graph_nodes(
        graph_name: str, request: protocol_model.CreateNodeRequest
    ) -> protocol_model.NodeModel:
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        definition = node_flow.node_registry.node_definitions.get(request.type)
        if definition is None:
            raise HTTPException(status_code=404, detail="Node type not found")

        node_name = request.preferred_name
        if node_name is not None and graph.get_node(node_name) is not None:
            node_name = f"{request.preferred_name}_{graph.max_node_id + 1}"

        if node_name is None:
            node_name = f"{request.type}_{graph.max_node_id + 1}"

        node = definition.factory(node_name)

        graph.add_node(node)
        if request.properties is not None:
            node.set_properties(request.properties)

        node._do_activate()

        # Configuration contract: set_properties/activate may make nodes
        # emit; the caller commits once after the batch (see
        # BaseNodeGraph.flush_outputs).
        graph.flush_outputs()

        return protocol_model.NodeModel(
            name=node.name,
            type=node.type,
            properties=node.properties,
            inputs=[
                protocol_model.InputPortModel(
                    name=port.name,
                    values=[
                        protocol_model.InputPortValueModel(
                            type=value_type.name, name=name, dispatch_flag=flag
                        )
                        for name, value_type, flag in zip(
                            port.value_name_list,
                            port.value_type_list,
                            port.dispatch_flags,
                        )
                    ],
                )
                for port in node.inputs.values()
            ],
            outputs=[
                protocol_model.OutputPortModel(
                    name=port.name,
                    values=[
                        protocol_model.OutputPortValueModel(
                            type=value_type.name, name=name
                        )
                        for name, value_type in zip(
                            port.value_name_list, port.value_type_list
                        )
                    ],
                )
                for port in node.outputs.values()
            ],
        )

    @router.get("/graphs/{graph_name}/nodes/{node_name}")
    async def get_graphs_graph_nodes_node(graph_name: str, node_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        node = graph.get_node(node_name)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")

        # Build property_groups from node's internal state
        groups_list: list[protocol_model.PropertyGroupModel] = []
        seen: set[int] = set()
        for pg in node._property_group_by_key.values():
            pg_id = id(pg)
            if pg_id not in seen:
                seen.add(pg_id)
                groups_list.append(protocol_model.PropertyGroupModel(
                    keys=pg.keys, dispatch_flags=pg.dispatch_flags
                ))

        return protocol_model.NodeModel(
            name=node.name,
            type=node.type,
            properties=node.properties,
            inputs=[
                protocol_model.InputPortModel(
                    name=port.name,
                    values=[
                        protocol_model.InputPortValueModel(
                            type=value_type.name, name=name, dispatch_flag=flag
                        )
                        for name, value_type, flag in zip(
                            port.value_name_list,
                            port.value_type_list,
                            port.dispatch_flags,
                        )
                    ],
                )
                for port in node.inputs.values()
            ],
            outputs=[
                protocol_model.OutputPortModel(
                    name=port.name,
                    values=[
                        protocol_model.OutputPortValueModel(
                            type=value_type.name, name=name
                        )
                        for name, value_type in zip(
                            port.value_name_list, port.value_type_list
                        )
                    ],
                )
                for port in node.outputs.values()
            ],
            property_groups=groups_list,
        )

    @router.delete("/graphs/{graph_name}/nodes/{node_name}")
    async def delete_graphs_graph_nodes_node(graph_name: str, node_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        node = graph.get_node(node_name)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")

        graph.remove_node(node_name)

    @router.get("/graphs/{graph_name}/nodes/{node_name}/properties")
    async def get_graphs_graph_nodes_node_properties(
        graph_name: str, node_name: str
    ) -> dict[str, PropertyDataType]:
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        node = graph.get_node(node_name)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")

        return node.properties

    @router.patch("/graphs/{graph_name}/nodes/{node_name}/properties")
    async def patch_graphs_graph_nodes_node_properties(
        graph_name: str, node_name: str, properties: dict[str, PropertyDataType]
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        node = graph.get_node(node_name)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")

        try:
            node.set_properties(properties)
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(stack_trace)

            raise HTTPException(status_code=400, detail=str(e))

        # Configuration contract: the set_properties caller owns the commit.
        graph.flush_outputs()

    @router.patch("/graphs/{graph_name}/nodes/{node_name}/property-groups")
    async def patch_graphs_graph_nodes_node_property_groups(
        graph_name: str,
        node_name: str,
        body: protocol_model.PatchPropertyGroupsModel = Body(...),
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        node = graph.get_node(node_name)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")

        node.set_property_groups([
            {"keys": pg.keys, "dispatch_flags": pg.dispatch_flags}
            for pg in body.property_groups
        ])
        graph.notify_node_updated(node)

    @router.patch("/graphs/{graph_name}/nodes/{node_name}/inputs/{input_name}")
    async def patch_graphs_graph_nodes_node_inputs_input(
        graph_name: str,
        node_name: str,
        input_name: str,
        input_model: protocol_model.PatchInputPortModel = Body(...),
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")
        node = graph.get_node(node_name)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")

        input_port = node.inputs.get(input_name)
        if input_port is None:
            raise HTTPException(status_code=404, detail="Input not found")

        if input_model.values is not None:
            for i, value in enumerate(input_model.values):
                if value.dispatch_flag is not None:
                    input_port.dispatch_flags[i] = value.dispatch_flag

        graph.notify_node_updated(node)

    @router.get("/graphs/{graph_name}/properties")
    async def get_graphs_graph_properties(
        graph_name: str,
    ) -> dict[str, PropertyDataType]:
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        return graph.properties

    @router.patch("/graphs/{graph_name}/properties")
    async def patch_graphs_graph_properties(
        graph_name: str, properties: dict[str, PropertyDataType]
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        try:
            graph.set_properties(properties)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Configuration contract: the set_properties caller owns the commit
        # (GraphPropertiesChanged no longer flushes from its callback).
        graph.flush_outputs()

    @router.get("/graphs/{graph_name}/inputs")
    async def get_graphs_graph_inputs(graph_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        return [
            protocol_model.InputPortModel(
                name=port.name,
                values=[
                    protocol_model.InputPortValueModel(
                        type=value_type.name, name=name, dispatch_flag=flag
                    )
                    for name, value_type, flag in zip(
                        port.value_name_list, port.value_type_list, port.dispatch_flags
                    )
                ],
            )
            for port in graph.inputs.values()
        ]

    @router.post("/graphs/{graph_name}/inputs")
    async def post_graphs_graph_inputs(
        graph_name: str, port_model: protocol_model.InputPortModel
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        try:
            input_port = StaticTypeInputPort(
                port_model.name,
                [name_to_port_value_type(value.type) for value in port_model.values],
            )
            graph.add_input_port(input_port)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        return port_model

    @router.delete("/graphs/{graph_name}/inputs/{input_name}")
    async def delete_graphs_graph_inputs_input_name(graph_name: str, input_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        if input_name not in graph.inputs:
            raise HTTPException(status_code=404, detail="Input not found")

        graph.remove_input_port(input_name)

    @router.get("/graphs/{graph_name}/outputs")
    async def get_graphs_graph_outputs(graph_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        return [
            protocol_model.OutputPortModel(
                name=port.name,
                values=[
                    protocol_model.OutputPortValueModel(name=name, type=value_type.name)
                    for name, value_type in zip(
                        port.value_name_list, port.value_type_list
                    )
                ],
            )
            for port in graph.outputs.values()
        ]

    @router.post("/graphs/{graph_name}/outputs")
    async def post_graphs_graph_outputs(
        graph_name: str, port_model: protocol_model.OutputPortModel
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        try:
            output_port = StaticTypeOutputPort(
                port_model.name,
                [name_to_port_value_type(value.type) for value in port_model.values],
            )
            graph.add_output_port(output_port)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        return protocol_model.OutputPortModel(
            name=port_model.name,
            values=[
                protocol_model.OutputPortValueModel(type=value_type.name, name=name)
                for name, value_type in zip(
                    output_port.value_name_list, output_port.value_type_list
                )
            ],
        )

    @router.delete("/graphs/{graph_name}/outputs/{output_name}")
    async def delete_graphs_graph_outputs_output_name(
        graph_name: str, output_name: str
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        if output_name not in graph.outputs:
            raise HTTPException(status_code=404, detail="Output not found")

        graph.remove_output_port(output_name)

    @router.get("/graphs/{graph_name}/outputs/{output_name}/values")
    async def get_graphs_graph_outputs_output_values(graph_name: str, output_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        port = graph.outputs[output_name]
        if port is None:
            raise HTTPException(status_code=404, detail="Output not found")

        values = port.current_values
        if values is None:
            return Response(content=b"", media_type="application/octet-stream")

        bytes_to_send = port_values_to_bytes(values, port.value_type_list, bytearray())
        return Response(
            content=bytes(bytes_to_send), media_type="application/octet-stream"
        )

    @router.get("/graphs/{graph_name}/edges")
    async def get_graphs_graph_edges(graph_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        return [
            protocol_model.EdgeModel(source=s, target=t, valid=edge.valid)
            for (s, t), edge in graph._edges.items()
        ]

    @router.post("/graphs/{graph_name}/edges")
    async def post_graphs_graph_edges(graph_name: str, edge: protocol_model.EdgeModel):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        try:
            source_node_name, source_port_name = edge.source.split(".", 1)
            target_node_name, target_port_name = edge.target.split(".", 1)
            # print(f"{edge.source} -> {edge.target}")

            if source_node_name == "" and target_node_name != "":
                graph.connect_input_to_node(
                    source_port_name, target_node_name, target_port_name
                )
            elif source_node_name != "" and target_node_name == "":
                graph.connect_node_to_output(
                    source_node_name, source_port_name, target_port_name
                )
            elif source_node_name != "" and target_node_name != "":
                graph.connect_nodes(
                    source_node_name,
                    source_port_name,
                    target_node_name,
                    target_port_name,
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid edge")

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/graphs/{graph_name}/edges/{edge_key}")
    async def delete_graphs_graph_edges_edge_key(graph_name: str, edge_key: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        try:
            source, target = edge_key.split("-")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        if (source, target) not in graph.get_edges():
            raise HTTPException(status_code=404, detail="Edge not found")

        try:
            source_node_name, source_port_name = source.split(".", 1)
            target_node_name, target_port_name = target.split(".", 1)

            if source_node_name == "" and target_node_name != "":
                graph.disconnect_input_to_node(
                    source_port_name, target_node_name, target_port_name
                )
            elif source_node_name != "" and target_node_name == "":
                graph.disconnect_node_to_output(
                    source_node_name, source_port_name, target_port_name
                )
            elif source_node_name != "" and target_node_name != "":
                graph.disconnect_nodes(
                    source_node_name,
                    source_port_name,
                    target_node_name,
                    target_port_name,
                )
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))

    @router.websocket("/graphs/{graph_name}/endpoint/ws")
    async def websocket_graphs_graph_endpoint_ws(websocket: WebSocket, graph_name: str):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            await websocket.close()
            return

        await graph.handle_websocket_endpoint(websocket)

    @router.get("/graphs/{graph_name}/editors/{editor_name}/models/{model_name}")
    async def get_graphs_graph_editors_editor_models_model(
        graph_name: str, editor_name: str, model_name: str, query: str
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        value = await graph.get_editor_model_value(editor_name, model_name, query)
        return value

    @router.put("/graphs/{graph_name}/editors/{editor_name}/models/{model_name}")
    async def put_graphs_graph_editors_editor_models_model(
        graph_name: str,
        editor_name: str,
        model_name: str,
        query: str,
        value: Any = Body(...),
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        await graph.put_editor_model_value(editor_name, model_name, query, value)

    @router.patch("/graphs/{graph_name}/editors/{editor_name}/models/{model_name}")
    async def patch_graphs_graph_editors_editor_models_model(
        graph_name: str,
        editor_name: str,
        model_name: str,
        query: str,
        value: Any = Body(...),
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        await graph.patch_editor_model_value(editor_name, model_name, query, value)

    @router.delete("/graphs/{graph_name}/editors/{editor_name}/models/{model_name}")
    async def delete_graphs_graph_editors_editor_models_model(
        graph_name: str, editor_name: str, model_name: str, query: str
    ):
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")

        await graph.delete_editor_model_value(editor_name, model_name, query)

    @router.get("/catalog/nodes")
    async def get_catalog_nodes():
        catalog = []
        for defn in node_flow.node_registry.node_definitions.values():
            m = defn.metadata
            entry = {
                "type": defn.type_name,
                "description": m.description,
                "category": m.category,
                "inputs": [
                    {
                        "name": p.name,
                        "description": p.description,
                        "types": p.value_types,
                        **({"value_names": p.value_names} if any(n is not None for n in p.value_names) else {}),
                    }
                    for p in m.inputs
                ],
                "outputs": [
                    {
                        "name": p.name,
                        "description": p.description,
                        "types": p.value_types,
                        **({"value_names": p.value_names} if any(n is not None for n in p.value_names) else {}),
                    }
                    for p in m.outputs
                ],
                "properties": {
                    name: {
                        "default": prop.default,
                        "description": prop.description,
                    }
                    for name, prop in m.properties.items()
                },
            }
            catalog.append(entry)
        return catalog

    # -- Data file access --

    def _get_data_storage(graph_name: str) -> DataStorage:
        graph = node_flow.get_graph(graph_name)
        if graph is None:
            raise HTTPException(status_code=404, detail="Graph not found")
        storage = graph.data_storage
        if storage is None:
            raise HTTPException(
                status_code=404, detail="Graph has no persist storage"
            )
        return storage

    def _validate_or_400(storage: DataStorage, file_path: str, *, writable: bool = False):
        try:
            return storage.validate_path(file_path, writable=writable)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/graphs/{graph_name}/data/{file_path:path}")
    @router.get("/graphs/{graph_name}/data/")
    async def get_graphs_graph_data(
        request: Request, graph_name: str, file_path: str = ""
    ):
        storage = _get_data_storage(graph_name)
        target = _validate_or_400(storage, file_path)

        if await asyncio.to_thread(target.is_dir):
            return await asyncio.to_thread(storage.list_directory, target, file_path)

        if await asyncio.to_thread(target.is_file):
            if "raw" in request.query_params:
                return FileResponse(target, filename=target.name)
            return await asyncio.to_thread(
                storage.get_file_info, target, graph_name, file_path
            )

        raise HTTPException(status_code=404, detail="Not found")

    @router.delete("/graphs/{graph_name}/data/{file_path:path}")
    async def delete_graphs_graph_data(
        graph_name: str,
        file_path: str,
        recursive: bool = False,
        upload_id: str | None = None,
    ):
        storage = _get_data_storage(graph_name)

        if upload_id is not None:
            found = await asyncio.to_thread(storage.abort_upload, upload_id)
            if not found:
                raise HTTPException(
                    status_code=410, detail="Upload session not found"
                )
            return Response(status_code=204)

        target = _validate_or_400(storage, file_path, writable=True)

        if not await asyncio.to_thread(target.exists):
            raise HTTPException(status_code=404, detail="Not found")

        if await asyncio.to_thread(target.is_dir):
            if not recursive:
                has_children = await asyncio.to_thread(
                    lambda: any(target.iterdir())
                )
                if has_children:
                    raise HTTPException(
                        status_code=409,
                        detail="Directory not empty; pass ?recursive=true",
                    )

        try:
            trash_target = await asyncio.to_thread(storage.trash_move, target)
        except PermissionError as e:
            if storage.readonly:
                raise HTTPException(status_code=403, detail=str(e))
            raise HTTPException(status_code=409, detail="File is in use")
        except OSError as e:
            if e.errno == errno.EXDEV:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete: target is on a different filesystem from data root",
                )
            raise HTTPException(status_code=500, detail=f"I/O error: {e}")

        asyncio.create_task(
            asyncio.to_thread(purge_trash_entry, trash_target)
        )
        return Response(status_code=204)

    @router.put("/graphs/{graph_name}/data/{file_path:path}")
    async def put_graphs_graph_data(
        request: Request,
        graph_name: str,
        file_path: str,
        overwrite: bool = False,
        type: str | None = None,
        upload_id: str | None = None,
        offset: int | None = None,
    ):
        storage = _get_data_storage(graph_name)

        # --- Resumable chunk upload ---
        if upload_id is not None and offset is not None:
            body = await request.body()
            try:
                new_size = await asyncio.to_thread(
                    storage.write_chunk, upload_id, offset, body
                )
            except FileNotFoundError:
                raise HTTPException(
                    status_code=410, detail="Upload session not found"
                )
            except ValueError as e:
                msg = str(e)
                if msg.startswith("Chunk too large"):
                    raise HTTPException(status_code=413, detail=msg)
                raise HTTPException(status_code=409, detail=msg)
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            return {"received_offset": new_size}

        target = _validate_or_400(storage, file_path, writable=True)

        # --- Folder create ---
        if type == "directory":
            try:
                result = await asyncio.to_thread(storage.create_directory, target)
            except FileExistsError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            return JSONResponse(content=result, status_code=201)

        # --- Single file upload (multipart) ---
        form = await request.form()
        try:
            upload_file = form.get("file")
            if upload_file is None or not hasattr(upload_file, "file"):
                raise HTTPException(status_code=400, detail="file field required")

            try:
                result, is_overwrite = await asyncio.to_thread(
                    storage.write_file_atomic,
                    target,
                    upload_file.file,
                    overwrite=overwrite,
                )
            except IsADirectoryError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except FileExistsError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))

            status_code = 200 if is_overwrite else 201
            return JSONResponse(content=result, status_code=status_code)
        finally:
            await form.close()

    @router.post("/graphs/{graph_name}/data/{file_path:path}")
    async def post_graphs_graph_data(
        request: Request,
        graph_name: str,
        file_path: str,
        upload: str | None = None,
        upload_id: str | None = None,
        overwrite: bool = False,
    ):
        storage = _get_data_storage(graph_name)

        if upload == "init":
            target = _validate_or_400(storage, file_path, writable=True)
            body_json = await request.json()
            size = body_json.get("size")
            if not isinstance(size, int) or size < 0:
                raise HTTPException(
                    status_code=400,
                    detail="size must be a non-negative integer",
                )
            try:
                result = await asyncio.to_thread(
                    storage.init_resumable, target, file_path, size, overwrite
                )
            except IsADirectoryError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except FileExistsError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            return JSONResponse(content=result, status_code=201)

        elif upload == "complete" and upload_id is not None:
            try:
                result, is_overwrite = await asyncio.to_thread(
                    storage.complete_resumable, upload_id
                )
            except FileNotFoundError:
                raise HTTPException(
                    status_code=410, detail="Upload session not found"
                )
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except FileExistsError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            status_code = 200 if is_overwrite else 201
            return JSONResponse(content=result, status_code=status_code)

        raise HTTPException(status_code=400, detail="Invalid request")

    @router.head("/graphs/{graph_name}/data/{file_path:path}")
    @router.head("/graphs/{graph_name}/data/")
    async def head_graphs_graph_data(
        graph_name: str, file_path: str = "", upload_id: str | None = None
    ):
        storage = _get_data_storage(graph_name)

        if upload_id is not None:
            offset = await asyncio.to_thread(storage.get_upload_offset, upload_id)
            if offset is None:
                raise HTTPException(
                    status_code=410, detail="Upload session not found"
                )
            return Response(
                status_code=200,
                headers={"X-Upload-Offset": str(offset)},
            )

        target = _validate_or_400(storage, file_path)
        if not await asyncio.to_thread(target.exists):
            raise HTTPException(status_code=404, detail="Not found")
        return Response(status_code=200)

    return router
