# import asyncio
# from functools import reduce
# from typing import Any
# import numpy as np
# import logging

# from ..port import PortDirection, StaticTypePort
# from ..node import BaseNode
# from ..data_type import DataType, PropertyDataType, data_type_to_name, name_to_data_type

# logger = logging.getLogger(__name__)


# class RealNumberSumNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealNumberSum")

#         input_value = StaticTypePort("value", PortDirection.INPUT, [DataType.Float32])
#         input_value.subscribe(id(self), self._on_input_value)

#         input_reset = StaticTypePort("reset", PortDirection.INPUT, [DataType.Any])
#         input_reset.subscribe(id(self), self._on_input_reset)

#         output_value = StaticTypePort("sum", PortDirection.OUTPUT, [DataType.Float32])

#         self._sum = 0

#         self._output_value = output_value
#         self._input_value = input_value
#         self._input_reset = input_reset

#         self.inputs[input_value.name] = input_value
#         self.inputs[input_reset.name] = input_reset
#         self.outputs[output_value.name] = output_value

#     def _on_input_value(self, values_any: list[Any]):
#         value_array: np.ndarray = values_any[0]
#         self._sum += np.sum(value_array)
#         self._output_value.dispatch([np.array([self._sum])])

#     def _on_input_reset(self, values_any: list[Any]):
#         self._sum = 0
#         self._output_value.dispatch([np.array([self._sum])])


# class RealNumberClipNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealNumberClip")

#         self._min: float = -1
#         self._max: float = 1
#         self._use_min: bool = True
#         self._use_max: bool = True

#         input_value = StaticTypePort("value", PortDirection.INPUT, [DataType.Float32])
#         input_value.subscribe(id(self), self._on_value)

#         output_value = StaticTypePort("value", PortDirection.OUTPUT, [DataType.Float32])

#         self._output_value = output_value
#         self._input_value = input_value

#         self.inputs[input_value.name] = input_value
#         self.outputs[output_value.name] = output_value

#         self.properties["min"] = self._min
#         self.properties["max"] = self._max
#         self.properties["use_min"] = self._use_min
#         self.properties["use_max"] = self._use_max

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         min_value = self._min
#         max_value = self._max
#         if "min" in properties:
#             min_value = float(properties["min"])
#         if "max" in properties:
#             max_value = float(properties["max"])

#         if min_value >= max_value:
#             raise ValueError("min must be less than max")

#         use_min = self._use_min
#         use_max = self._use_max
#         if "use_min" in properties:
#             use_min = bool(properties["use_min"])
#         if "use_max" in properties:
#             use_max = bool(properties["use_max"])

#         self._min = min_value
#         self._max = max_value
#         self._use_min = use_min
#         self._use_max = use_max

#         self.properties["min"] = min_value
#         self.properties["max"] = max_value
#         self.properties["use_min"] = use_min
#         self.properties["use_max"] = use_max

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_value(self, values_any: list[Any]):
#         value_array: np.ndarray = values_any[0]
#         out = np.clip(
#             value_array,
#             self._min if self._use_min else None,
#             self._max if self._use_max else None,
#         )
#         self._output_value.dispatch([out])


# class RealVecSliceNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecSlice")

#         input_vector = StaticTypePort(
#             "vector", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         input_vector.subscribe(id(self), self._on_vectors)
#         input_indices = StaticTypePort(
#             "indices", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         # input_indices.subscribe(id(self), self._on_indices)

#         output_vector = StaticTypePort(
#             "vector", PortDirection.OUTPUT, [DataType.Float32Vec]
#         )

#         # self._indices: np.ndarray | None = None
#         self._range = (5, 10)

#         self._output_vector = output_vector
#         self._input_vector = input_vector
#         self._input_indices = input_indices

#         self.inputs[input_vector.name] = input_vector
#         self.inputs[input_indices.name] = input_indices
#         self.outputs[output_vector.name] = output_vector

#         self.properties["range_begin"] = self._range[0]
#         self.properties["range_end"] = self._range[1]

#     # def _on_indices(self, values_any: list[Any]):
#     #     indices_array: np.ndarray = values_any[0]
#     #     indices = indices_array[-1]
#     #     self._indices = indices
#     #     print(indices)

#     # def _update_window(self):

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         range_begin = self._range[0]
#         range_end = self._range[1]
#         if "range_begin" in properties:
#             range_begin = float(properties["range_begin"])
#         if "range_end" in properties:
#             range_end = float(properties["range_end"])

#         if range_begin > range_end:
#             raise ValueError("range_begin must be less than range_end")

#         self._range = (range_begin, range_end)

#         self.properties["range_begin"] = range_begin
#         self.properties["range_end"] = range_end

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_vectors(self, values_any: list[Any]):
#         vectors: np.ndarray = values_any[0]
#         # print(self._range)

#         if self._input_indices.current_values is not None:
#             indices: np.ndarray = self._input_indices.current_values[0][-1]
#             vectors = vectors[
#                 :, (indices >= self._range[0]) & (indices < self._range[1])
#             ]
#         else:
#             vectors = vectors[:, int(self._range[0]) : int(self._range[1])]

#         self._output_vector.dispatch([vectors])


# class RealVecFilterNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecFilter")

#         input_vector = StaticTypePort(
#             "vector", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         input_vector.subscribe(id(self), self._on_input_vector)

#         input_filter = StaticTypePort("filter", PortDirection.INPUT, [DataType.BoolVec])

#         output_vector = StaticTypePort(
#             "vector", PortDirection.OUTPUT, [DataType.Float32Vec]
#         )

#         self._input_vector = input_vector
#         self._input_filter = input_filter
#         self._output_vector = output_vector

#         self.inputs[input_vector.name] = input_vector
#         self.inputs[input_filter.name] = input_filter
#         self.outputs[output_vector.name] = output_vector

#     def _on_input_vector(self, values_any: list[Any]):
#         vector_array: np.ndarray = values_any[0]

#         if self._input_filter.current_values is None:
#             self._output_vector.dispatch([vector_array])
#             return

#         filter_array = self._input_filter.current_values[0]
#         if len(filter_array) == 1:
#             self._output_vector.dispatch([vector_array[:, filter_array[0]]])
#             return

#         outs = [v[f] for v, f in zip(vector_array, filter_array)]
#         # print(f"{self.name=} {outs=}")


# class RealVecPercentileNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecPercentile")

#         input_vectors = StaticTypePort(
#             "vector", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         input_percent = StaticTypePort(
#             "percent", PortDirection.INPUT, [DataType.Float32]
#         )
#         input_vectors.subscribe(id(self), self._on_input_vector)

#         output_percentile = StaticTypePort(
#             "percentile", PortDirection.OUTPUT, [DataType.Float32]
#         )

#         self._output_percentile = output_percentile
#         self._input_vectors = input_vectors
#         self._input_percent = input_percent

#         self.inputs[input_vectors.name] = input_vectors
#         self.inputs[input_percent.name] = input_percent
#         self.outputs[output_percentile.name] = output_percentile

#     def _on_input_vector(self, values_any: list[Any]):
#         vectors: np.ndarray = values_any[0]
#         if self._input_percent.current_values is None:
#             logger.warning("ratio is not set")
#             return

#         percent_array = self._input_percent.current_values[0]
#         try:
#             out = np.percentile(vectors, percent_array, axis=1).reshape(-1)
#             # print(f"{out=}")
#         except Exception as e:
#             logger.warning(f"{e=}")
#             return
#         self._output_percentile.dispatch([out])


# class RealVecMinNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecMin")

#         input_vectors = StaticTypePort(
#             "vector", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         input_vectors.subscribe(id(self), self._on_input_vectors)

#         output_value = StaticTypePort("min", PortDirection.OUTPUT, [DataType.Float32])

#         self._output_value = output_value
#         self._input_vectors = input_vectors

#         self.inputs[input_vectors.name] = input_vectors
#         self.outputs[output_value.name] = output_value

#     def _on_input_vectors(self, values_any: list[Any]):
#         vectors: np.ndarray = values_any[0]
#         out = np.min(vectors, axis=1)

#         self._output_value.dispatch([out])


# class RealVecMaxNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecMax")

#         input_vectors = StaticTypePort(
#             "vector", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         input_vectors.subscribe(id(self), self._on_input_vectors)

#         output_value = StaticTypePort("max", PortDirection.OUTPUT, [DataType.Float32])

#         self._output_value = output_value
#         self._input_vectors = input_vectors

#         self.inputs[input_vectors.name] = input_vectors
#         self.outputs[output_value.name] = output_value

#     def _on_input_vectors(self, values_any: list[Any]):
#         vectors: np.ndarray = values_any[0]
#         out = np.max(vectors, axis=1)

#         self._output_value.dispatch([out])


# class RealVecMedianNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecMedian")

#         input_vectors = StaticTypePort(
#             "vector", PortDirection.INPUT, [DataType.Float32Vec]
#         )
#         input_vectors.subscribe(id(self), self._on_vectors)

#         output_value = StaticTypePort(
#             "median", PortDirection.OUTPUT, [DataType.Float32]
#         )

#         self._output_value = output_value
#         self._input_vectors = input_vectors

#         self.inputs[input_vectors.name] = input_vectors
#         self.outputs[output_value.name] = output_value

#     def _on_vectors(self, values_any: list[Any]):
#         vectors: np.ndarray = values_any[0]
#         out = np.median(vectors, axis=1)

#         self._output_value.dispatch([out])

#         # print(vectors, out)


# class RealVecClipNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealVecClip")

#         self._min: float = -1
#         self._max: float = 1
#         self._use_min: bool = True
#         self._use_max: bool = True

#         input_vectors = StaticTypePort("in", PortDirection.INPUT, [DataType.Float32Vec])
#         input_vectors.subscribe(id(self), self._on_vectors)

#         output_vectors = StaticTypePort(
#             "out", PortDirection.OUTPUT, [DataType.Float32Vec]
#         )

#         self._output_vectors = output_vectors
#         self._input_vectors = input_vectors

#         self.inputs[input_vectors.name] = input_vectors
#         self.outputs[output_vectors.name] = output_vectors

#         self.properties["min"] = self._min
#         self.properties["max"] = self._max
#         self.properties["use_min"] = self._use_min
#         self.properties["use_max"] = self._use_max

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         min_value = self._min
#         max_value = self._max
#         if "min" in properties:
#             min_value = float(properties["min"])
#         if "max" in properties:
#             max_value = float(properties["max"])

#         if min_value >= max_value:
#             raise ValueError("min must be less than max")

#         use_min = self._use_min
#         use_max = self._use_max
#         if "use_min" in properties:
#             use_min = bool(properties["use_min"])
#         if "use_max" in properties:
#             use_max = bool(properties["use_max"])

#         self._min = min_value
#         self._max = max_value
#         self._use_min = use_min
#         self._use_max = use_max

#         self.properties["min"] = min_value
#         self.properties["max"] = max_value
#         self.properties["use_min"] = use_min
#         self.properties["use_max"] = use_max

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_vectors(self, values_any: list[Any]):
#         vectors: np.ndarray = values_any[0]
#         out = np.clip(
#             vectors,
#             self._min if self._use_min else None,
#             self._max if self._use_max else None,
#         )

#         self._output_vectors.dispatch([out])


# class RealNumberMinNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RealNumberMin")

#         count = 2

#         input_values = StaticTypePort(
#             "values", PortDirection.INPUT, [DataType.Float32] * count
#         )
#         input_values.subscribe(id(self), self._on_values)
#         output_value = StaticTypePort("value", PortDirection.OUTPUT, [DataType.Float32])

#         self._output_value = output_value
#         self._input_values = input_values
#         self._count = count

#         self.inputs[input_values.name] = input_values
#         self.outputs[output_value.name] = output_value

#         self.properties["count"] = count

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         count = self._count
#         if "count" in properties:
#             count = int(properties["count"])

#         if count < 2:
#             raise ValueError("count must be at least 2")
#         if self._count != count:
#             input_values = StaticTypePort(
#                 "values", PortDirection.INPUT, [DataType.Float32] * count
#             )
#             input_values.subscribe(id(self), self._on_values)

#             if self.parent_graph is not None:
#                 self.parent_graph.disconnect_all_from_node_input(
#                     self.name, self._input_values.name
#                 )
#             self.inputs[input_values.name] = input_values
#             self._input_values = input_values
#             self._count = count

#         self.properties["count"] = count

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_values(self, values_any: list[Any]):
#         out = reduce(np.minimum, values_any[: self._count])
#         self._output_value.dispatch([out])


# class VectorLengthNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "VectorLength")

#         value_type = DataType.Float32Vec

#         input_vector = StaticTypePort("vector", PortDirection.INPUT, [value_type])
#         input_vector.subscribe(id(self), self._on_input_vector)

#         output_length = StaticTypePort("length", PortDirection.OUTPUT, [DataType.Int32])

#         self._output_length = output_length
#         self._input_vector = input_vector
#         self._value_type = value_type

#         self.inputs[input_vector.name] = input_vector
#         self.outputs[output_length.name] = output_length

#         self.properties["value_type"] = data_type_to_name(value_type)

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         value_type = self._value_type
#         if "value_type" in properties:
#             value_type_str = properties["value_type"]
#             if not isinstance(value_type_str, str):
#                 raise ValueError("value_type must be a string")

#             value_type = name_to_data_type(value_type_str)

#         if value_type not in [
#             DataType.Float32Vec,
#             DataType.Complex128Vec,
#             DataType.Complex64Vec,
#             DataType.BoolVec,
#         ]:
#             raise ValueError("value_type must be a vector type")

#         if value_type != self._value_type:
#             input_vector = StaticTypePort("vector", PortDirection.INPUT, [value_type])
#             input_vector.subscribe(id(self), self._on_input_vector)

#             if self.parent_graph is not None:
#                 self.parent_graph.disconnect_all_from_node_input(
#                     self.name, self._input_vector.name
#                 )

#             self._input_vector.unsubscribe(id(self))
#             self.inputs[input_vector.name] = input_vector
#             self._input_vector = input_vector
#             self._value_type = value_type

#         self._value_type = value_type
#         self.properties["value_type"] = data_type_to_name(value_type)

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_input_vector(self, values_any: list[Any]):
#         vector_array: np.ndarray | list = values_any[0]
#         length_array = np.array(
#             [len(vector) for vector in vector_array], dtype=np.int32
#         )
#         self._output_length.dispatch([length_array])


# ===============================


# import asyncio
# from functools import reduce
# import operator
# from typing import Any
# import numpy as np
# import logging

# from ..port import PortDirection, StaticTypePort
# from ..node import BaseNode
# from ..data_type import DataType, PropertyDataType, data_type_to_name, name_to_data_type

# logger = logging.getLogger(__name__)


# class LinearFunctionNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "LinearFunction")

#         input_x = StaticTypePort("x", PortDirection.INPUT, [DataType.Float32])
#         input_x.subscribe(id(self), self._on_input_x)

#         input_a = StaticTypePort("a", PortDirection.INPUT, [DataType.Float32])

#         input_b = StaticTypePort("b", PortDirection.INPUT, [DataType.Float32])

#         output_y = StaticTypePort("y", PortDirection.OUTPUT, [DataType.Float32])

#         self._input_x = input_x
#         self._input_a = input_a
#         self._input_b = input_b
#         self._output_y = output_y
#         self._sign_a = 1.0
#         self._sign_b = 1.0

#         self.inputs[input_x.name] = input_x
#         self.inputs[input_a.name] = input_a
#         self.inputs[input_b.name] = input_b
#         self.outputs[output_y.name] = output_y

#         self.properties["sign_a"] = self._sign_a
#         self.properties["sign_b"] = self._sign_b

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         sign_a = self._sign_a
#         sign_b = self._sign_b
#         if "sign_a" in properties:
#             sign_a = float(properties["sign_a"])
#         if "sign_b" in properties:
#             sign_b = float(properties["sign_b"])

#         self._sign_a = sign_a
#         self._sign_b = sign_b

#         self.properties["sign_a"] = sign_a
#         self.properties["sign_b"] = sign_b

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_input_x(self, values_any: list[Any]):
#         x_array: np.ndarray = values_any[0]

#         if self._input_a.current_values is None or self._input_b.current_values is None:
#             logger.warning("a or b is not set")
#             return

#         a_array: np.ndarray = self._input_a.current_values[0]
#         b_array: np.ndarray = self._input_b.current_values[0]

#         try:
#             # print(f"{self.name=} {a_array=} {b_array=} {x_array=}")
#             y_array = self._sign_a * a_array * x_array + self._sign_b * b_array
#             self._output_y.dispatch([y_array])
#         except Exception as e:
#             logger.warning(f"{self.name=} {e=}")
#             return


# class SigmoidFunctionNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "SigmoidFunction")

#         input_x = StaticTypePort("x", PortDirection.INPUT, [DataType.Float32])
#         input_x.subscribe(id(self), self._on_input_x)

#         input_a = StaticTypePort("a", PortDirection.INPUT, [DataType.Float32])

#         output_y = StaticTypePort("y", PortDirection.OUTPUT, [DataType.Float32])

#         self._input_x = input_x
#         self._input_a = input_a
#         self._output_y = output_y

#         self.inputs[input_x.name] = input_x
#         self.inputs[input_a.name] = input_a
#         self.outputs[output_y.name] = output_y

#     def _on_input_x(self, values_any: list[Any]):
#         x_array: np.ndarray = values_any[0]

#         if self._input_a.current_values is None:
#             logger.warning("a is not set")
#             return

#         a_array: np.ndarray = self._input_a.current_values[0]

#         try:
#             y_array = 1 / (1 + np.exp(-a_array * x_array))
#             self._output_y.dispatch([y_array])
#         except Exception as e:
#             logger.warning(f"{self.name=} {e=}")
#             return

# ==============================

# import asyncio
# from typing import Any
# import numpy as np
# import logging
# import traceback
# from numpy.lib.stride_tricks import sliding_window_view
# from sklearn.preprocessing import RobustScaler


# from ..port import PortDirection, StaticTypePort
# from ..node import BaseNode
# from ..data_type import (
#     DataType,
#     PropertyDataType,
#     data_type_to_name,
#     name_to_data_type,
# )

# logger = logging.getLogger(__name__)


# class RobustScalerNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RobustScaler")

#         input_fit = StaticTypePort("fit", PortDirection.INPUT, [DataType.Float32])
#         input_fit.subscribe(id(self), self._on_input_fit)

#         input_in = StaticTypePort("in", PortDirection.INPUT, [DataType.Float32])
#         input_in.subscribe(id(self), self._on_input_in)

#         output_scaled = StaticTypePort("fit", PortDirection.OUTPUT, [DataType.Float32])

#         scaler = RobustScaler(
#             with_centering=True,
#             with_scaling=True,
#             quantile_range=(25.0, 75.0),
#         )

#         self._scaler = scaler
#         self._input_fit = input_fit
#         self._input_in = input_in
#         self._output_scaled = output_scaled

#         self.inputs[input_in.name] = input_in
#         self.inputs[input_fit.name] = input_fit
#         self.outputs[output_scaled.name] = output_scaled

#     def _on_input_fit(self, values_any: list[Any]):
#         value_array: np.ndarray = values_any[0]

#         self._scaler.fit(value_array.reshape(-1, 1))

#     def _on_input_in(self, values_any: list[Any]):
#         value_array: np.ndarray = values_any[0]

#         try:
#             scaled = self._scaler.transform(value_array.reshape(-1, 1))

#             print(f"{scaled=}")
#         except Exception as e:
#             logger.warning(f"Failed to scale: {e}")
