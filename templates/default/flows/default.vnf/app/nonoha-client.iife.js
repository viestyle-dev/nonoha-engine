"use strict";
var NonohaClient = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/index.ts
  var index_exports = {};
  __export(index_exports, {
    DataClient: () => DataClient,
    GraphClient: () => GraphClient,
    PortDataType: () => PortDataType,
    graphDataClient: () => graphDataClient,
    makeGraphEndpoint: () => makeGraphEndpoint,
    nameToPortDataType: () => nameToPortDataType,
    parsePortValuesBytes: () => parsePortValuesBytes
  });

  // src/types.ts
  var PortDataType = /* @__PURE__ */ ((PortDataType2) => {
    PortDataType2[PortDataType2["Bool"] = 0] = "Bool";
    PortDataType2[PortDataType2["Int8"] = 1] = "Int8";
    PortDataType2[PortDataType2["Uint8"] = 2] = "Uint8";
    PortDataType2[PortDataType2["Int16"] = 3] = "Int16";
    PortDataType2[PortDataType2["Uint16"] = 4] = "Uint16";
    PortDataType2[PortDataType2["Int32"] = 5] = "Int32";
    PortDataType2[PortDataType2["Uint32"] = 6] = "Uint32";
    PortDataType2[PortDataType2["Int64"] = 7] = "Int64";
    PortDataType2[PortDataType2["Uint64"] = 8] = "Uint64";
    PortDataType2[PortDataType2["Float32"] = 9] = "Float32";
    PortDataType2[PortDataType2["Float64"] = 10] = "Float64";
    PortDataType2[PortDataType2["Complex64"] = 11] = "Complex64";
    PortDataType2[PortDataType2["Complex128"] = 12] = "Complex128";
    PortDataType2[PortDataType2["String"] = 13] = "String";
    PortDataType2[PortDataType2["Any"] = 14] = "Any";
    return PortDataType2;
  })(PortDataType || {});
  var nameToPortDataType = {
    bool: 0 /* Bool */,
    i8: 1 /* Int8 */,
    u8: 2 /* Uint8 */,
    i16: 3 /* Int16 */,
    u16: 4 /* Uint16 */,
    i32: 5 /* Int32 */,
    u32: 6 /* Uint32 */,
    i64: 7 /* Int64 */,
    u64: 8 /* Uint64 */,
    f32: 9 /* Float32 */,
    f64: 10 /* Float64 */,
    c64: 11 /* Complex64 */,
    c128: 12 /* Complex128 */,
    str: 13 /* String */,
    any: 14 /* Any */
  };

  // src/port-parser.ts
  var textDecoder = new TextDecoder();
  function parsePortValuesBytes(dataView, offset, reuseFrom) {
    const values = [];
    const valueCount = dataView.getUint8(offset++);
    for (let i = 0; i < valueCount; ++i) {
      const dataType = dataView.getUint8(offset++);
      const ndim = dataView.getUint8(offset++);
      const shape = new Array(ndim + 1);
      let elementSize = 1;
      for (let j = 1; j < ndim + 1; ++j) {
        shape[j] = dataView.getUint16(offset);
        offset += 2;
        elementSize *= shape[j];
      }
      const dataSize = dataView.getUint32(offset);
      offset += 4;
      const prev = reuseFrom?.[i];
      switch (dataType) {
        case 9 /* Float32 */: {
          const length = dataSize / 4;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new Float32Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getFloat32(offset + j * 4);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 10 /* Float64 */: {
          const length = dataSize / 8;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new Float64Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getFloat64(offset + j * 8);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 1 /* Int8 */: {
          const value = new Int8Array(dataView.buffer, dataView.byteOffset + offset, dataSize);
          shape[0] = elementSize ? value.length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 2 /* Uint8 */:
        case 0 /* Bool */: {
          const value = new Uint8Array(dataView.buffer, dataView.byteOffset + offset, dataSize);
          shape[0] = elementSize ? value.length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 3 /* Int16 */: {
          const length = dataSize / 2;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new Int16Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getInt16(offset + j * 2);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 4 /* Uint16 */: {
          const length = dataSize / 2;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new Uint16Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getUint16(offset + j * 2);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 5 /* Int32 */: {
          const length = dataSize / 4;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new Int32Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getInt32(offset + j * 4);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 6 /* Uint32 */: {
          const length = dataSize / 4;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new Uint32Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getUint32(offset + j * 4);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 7 /* Int64 */: {
          const length = dataSize / 8;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new BigInt64Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getBigInt64(offset + j * 8);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 8 /* Uint64 */: {
          const length = dataSize / 8;
          const value = prev && prev.dataType === dataType && prev.array.length === length ? prev.array : new BigUint64Array(length);
          for (let j = 0; j < length; ++j) {
            value[j] = dataView.getBigUint64(offset + j * 8);
          }
          shape[0] = elementSize ? length / elementSize : 0;
          values.push({ dataType, shape, array: value });
          break;
        }
        case 13 /* String */: {
          if (dataSize === 0) {
            shape[0] = 0;
            values.push({ dataType, shape, array: [] });
            break;
          }
          const stringData = textDecoder.decode(
            new Uint8Array(dataView.buffer, dataView.byteOffset + offset, dataSize)
          );
          const parts = stringData.split("\0");
          const strings = parts.slice(0, -1);
          shape[0] = elementSize ? strings.length / elementSize : 0;
          values.push({ dataType, shape, array: strings });
          break;
        }
      }
      offset += dataSize;
    }
    return [values, offset];
  }

  // src/graph-client.ts
  var GraphClient = class {
    constructor(engineGatewayUrl, graphName) {
      this.endpointSocket = null;
      this.onOutputCallbacks = [];
      this.onClosedCallbacks = [];
      this.textDecoder = new TextDecoder();
      this.textEncoder = new TextEncoder();
      this.outputBuffers = /* @__PURE__ */ new Map();
      this.engineGatewayUrl = engineGatewayUrl;
      this.graphName = graphName;
    }
    // --- WebSocket ---
    connect() {
      if (this.endpointSocket) return;
      const url = `ws://${this.engineGatewayUrl}/node-flow/graphs/${this.graphName}/endpoint/ws`;
      const socket = new WebSocket(url);
      socket.binaryType = "arraybuffer";
      socket.onmessage = (event) => {
        const arrayBuffer = event.data;
        const dataView = new DataView(arrayBuffer);
        const eventType = dataView.getUint8(0);
        if (eventType === 1) {
          let offset = 1;
          const portNameLength = dataView.getUint8(offset++);
          const portName = this.textDecoder.decode(
            new Uint8Array(arrayBuffer, offset, portNameLength)
          );
          offset += portNameLength;
          const reuseFrom = this.outputBuffers.get(portName);
          const [values, newOffset] = parsePortValuesBytes(dataView, offset, reuseFrom);
          offset = newOffset;
          this.outputBuffers.set(portName, values);
          const portData = { portName, values };
          for (let i = 0; i < this.onOutputCallbacks.length; ++i) {
            this.onOutputCallbacks[i](portData);
          }
        }
      };
      socket.onclose = (event) => {
        for (let i = 0; i < this.onClosedCallbacks.length; ++i) {
          this.onClosedCallbacks[i](event.wasClean);
        }
      };
      this.endpointSocket = socket;
    }
    close() {
      if (!this.endpointSocket) return;
      this.endpointSocket.close();
      this.endpointSocket = null;
    }
    dispatchInput(input) {
      if (!this.endpointSocket) return;
      const buffer = this.serializePortData(input);
      this.endpointSocket.send(buffer);
    }
    addOutputCallback(callback) {
      this.onOutputCallbacks.push(callback);
    }
    removeOutputCallback(callback) {
      const index = this.onOutputCallbacks.indexOf(callback);
      if (index !== -1) {
        this.onOutputCallbacks.splice(index, 1);
      }
    }
    addClosedCallback(callback) {
      this.onClosedCallbacks.push(callback);
    }
    // --- REST API ---
    async fetchOutputValues(portName) {
      const url = `http://${this.engineGatewayUrl}/node-flow/graphs/${encodeURIComponent(this.graphName)}/outputs/${encodeURIComponent(portName)}/values`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Failed to fetch output values for '${portName}': ${res.status}`);
      const buf = await res.arrayBuffer();
      const [values] = parsePortValuesBytes(new DataView(buf), 0);
      return values;
    }
    // --- Serialization (private) ---
    serializePortData(input) {
      const preEncodedStrings = [];
      let totalLength = 1 + // eventType
      1 + // portNameLength
      input.portName.length + 1;
      for (let i = 0; i < input.values.length; i++) {
        const v = input.values[i];
        totalLength += 2;
        totalLength += 2 * (v.shape.length - 1);
        totalLength += 4;
        switch (v.dataType) {
          case 1 /* Int8 */:
          case 2 /* Uint8 */:
          case 0 /* Bool */:
            totalLength += v.array.length;
            break;
          case 3 /* Int16 */:
          case 4 /* Uint16 */:
            totalLength += 2 * v.array.length;
            break;
          case 9 /* Float32 */:
          case 5 /* Int32 */:
          case 6 /* Uint32 */:
            totalLength += 4 * v.array.length;
            break;
          case 10 /* Float64 */:
          case 7 /* Int64 */:
          case 8 /* Uint64 */:
            totalLength += 8 * v.array.length;
            break;
          case 13 /* String */: {
            const encoded = [];
            for (const s of v.array) {
              const enc = this.textEncoder.encode(s);
              encoded.push(enc);
              totalLength += enc.length + 1;
            }
            preEncodedStrings[i] = encoded;
            break;
          }
          default:
            throw new Error("Unsupported data type");
        }
      }
      const buffer = new ArrayBuffer(totalLength);
      const dataView = new DataView(buffer);
      const uint8View = new Uint8Array(buffer);
      let offset = 0;
      dataView.setUint8(offset++, 0);
      dataView.setUint8(offset++, input.portName.length);
      for (let i = 0; i < input.portName.length; i++) {
        dataView.setUint8(offset++, input.portName.charCodeAt(i));
      }
      dataView.setUint8(offset++, input.values.length);
      for (let i = 0; i < input.values.length; i++) {
        const value = input.values[i];
        dataView.setUint8(offset++, value.dataType);
        dataView.setUint8(offset++, value.shape.length - 1);
        for (let j = 1; j < value.shape.length; j++) {
          dataView.setUint16(offset, value.shape[j]);
          offset += 2;
        }
        switch (value.dataType) {
          case 9 /* Float32 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 4);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setFloat32(offset, value.array[j]);
              offset += 4;
            }
            break;
          }
          case 10 /* Float64 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 8);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setFloat64(offset, value.array[j]);
              offset += 8;
            }
            break;
          }
          case 1 /* Int8 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setInt8(offset++, value.array[j]);
            }
            break;
          }
          case 2 /* Uint8 */:
          case 0 /* Bool */: {
            const len = value.array.length;
            dataView.setUint32(offset, len);
            offset += 4;
            uint8View.set(value.array, offset);
            offset += len;
            break;
          }
          case 3 /* Int16 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 2);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setInt16(offset, value.array[j]);
              offset += 2;
            }
            break;
          }
          case 4 /* Uint16 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 2);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setUint16(offset, value.array[j]);
              offset += 2;
            }
            break;
          }
          case 5 /* Int32 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 4);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setInt32(offset, value.array[j]);
              offset += 4;
            }
            break;
          }
          case 6 /* Uint32 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 4);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setUint32(offset, value.array[j]);
              offset += 4;
            }
            break;
          }
          case 7 /* Int64 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 8);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setBigInt64(offset, value.array[j]);
              offset += 8;
            }
            break;
          }
          case 8 /* Uint64 */: {
            const len = value.array.length;
            dataView.setUint32(offset, len * 8);
            offset += 4;
            for (let j = 0; j < len; j++) {
              dataView.setBigUint64(offset, value.array[j]);
              offset += 8;
            }
            break;
          }
          case 13 /* String */: {
            const encoded = preEncodedStrings[i];
            let dataSize = 0;
            for (const enc of encoded) {
              dataSize += enc.length + 1;
            }
            dataView.setUint32(offset, dataSize);
            offset += 4;
            for (const enc of encoded) {
              uint8View.set(enc, offset);
              offset += enc.length;
              uint8View[offset++] = 0;
            }
            break;
          }
          default:
            throw new Error("Unsupported data type");
        }
      }
      return buffer;
    }
  };
  function makeGraphEndpoint(engineGatewayUrl, graphName) {
    return new GraphClient(engineGatewayUrl, graphName);
  }

  // src/data-client.ts
  async function parseErrorResponse(response) {
    try {
      return await response.json();
    } catch {
      const text = await response.text();
      return { detail: text || `HTTP ${response.status}` };
    }
  }
  function throwApiError(detail, code) {
    throw Object.assign(new Error(detail), { code });
  }
  var _DataClient = class _DataClient {
    constructor(engineGatewayUrl, basePath) {
      this.engineGatewayUrl = engineGatewayUrl;
      this.basePath = basePath.endsWith("/") ? basePath.slice(0, -1) : basePath;
    }
    buildUrl(path, raw) {
      const base = `http://${this.engineGatewayUrl}${this.basePath}/`;
      if (!path) {
        return raw ? `${base}?raw` : base;
      }
      const encoded = path.split("/").map(encodeURIComponent).join("/");
      const url = `${base}${encoded}`;
      return raw ? `${url}?raw` : url;
    }
    async fetchPath(path) {
      const response = await fetch(this.buildUrl(path));
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
      }
      return response.json();
    }
    async fetchFileRaw(filePath) {
      const response = await fetch(this.buildUrl(filePath, true));
      if (!response.ok) {
        const text2 = await response.text();
        throw new Error(text2 || `HTTP ${response.status}`);
      }
      const blob = await response.blob();
      const text = await blob.text();
      return { text, blob };
    }
    async deletePath(path, options) {
      let url = this.buildUrl(path);
      if (options?.recursive) {
        url += (url.includes("?") ? "&" : "?") + "recursive=true";
      }
      const response = await fetch(url, { method: "DELETE" });
      if (!response.ok) {
        const err = await parseErrorResponse(response);
        throwApiError(err.detail, err.code);
      }
    }
    async createDirectory(path) {
      const url = this.buildUrl(path) + "?type=directory";
      const response = await fetch(url, { method: "PUT" });
      if (!response.ok) {
        const err = await parseErrorResponse(response);
        throwApiError(err.detail, err.code);
      }
      return response.json();
    }
    uploadFile(path, file, options) {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        let url = this.buildUrl(path);
        if (options?.overwrite) {
          url += (url.includes("?") ? "&" : "?") + "overwrite=true";
        }
        xhr.open("PUT", url);
        if (options?.signal) {
          options.signal.addEventListener("abort", () => xhr.abort());
        }
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable && options?.onProgress) {
            options.onProgress(e.loaded, e.total);
          }
        });
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            try {
              const err = JSON.parse(xhr.responseText);
              reject(Object.assign(new Error(err.detail), { code: err.code }));
            } catch {
              reject(new Error(xhr.responseText || `HTTP ${xhr.status}`));
            }
          }
        });
        xhr.addEventListener("error", () => reject(new Error("Network error")));
        xhr.addEventListener("abort", () => reject(new Error("Upload aborted")));
        const formData = new FormData();
        formData.append("file", file);
        xhr.send(formData);
      });
    }
    async uploadFileResumable(path, file, options) {
      const chunkSize = options?.chunkSize ?? _DataClient.DEFAULT_CHUNK_SIZE;
      let uploadId = options?.resumeUploadId ?? "";
      let offset = 0;
      if (uploadId) {
        offset = await this.getUploadOffset(path, uploadId);
        if (offset === 0) uploadId = "";
      }
      if (!uploadId) {
        const init = await this.initResumableUpload(
          path,
          file.size,
          options?.overwrite ?? false
        );
        uploadId = init.upload_id;
      }
      while (offset < file.size) {
        if (options?.signal?.aborted) throw new Error("Upload aborted");
        const end = Math.min(offset + chunkSize, file.size);
        const chunk = await file.slice(offset, end).arrayBuffer();
        const result = await this.sendChunk(
          path,
          uploadId,
          offset,
          chunk,
          options?.signal
        );
        offset = result.received_offset;
        options?.onProgress?.(offset, file.size);
      }
      return this.completeResumableUpload(path, uploadId);
    }
    async initResumableUpload(path, size, overwrite) {
      let url = this.buildUrl(path) + "?upload=init";
      if (overwrite) url += "&overwrite=true";
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ size })
      });
      if (!response.ok) {
        const err = await parseErrorResponse(response);
        throwApiError(err.detail, err.code);
      }
      return response.json();
    }
    async sendChunk(path, uploadId, offset, chunk, signal) {
      const url = this.buildUrl(path) + `?upload_id=${encodeURIComponent(uploadId)}&offset=${offset}`;
      const response = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/octet-stream" },
        body: chunk,
        signal
      });
      if (!response.ok) {
        const err = await parseErrorResponse(response);
        throwApiError(err.detail, err.code);
      }
      return response.json();
    }
    async completeResumableUpload(path, uploadId) {
      const url = this.buildUrl(path) + `?upload_id=${encodeURIComponent(uploadId)}&upload=complete`;
      const response = await fetch(url, { method: "POST" });
      if (!response.ok) {
        const err = await parseErrorResponse(response);
        throwApiError(err.detail, err.code);
      }
      return response.json();
    }
    async getUploadOffset(path, uploadId) {
      const url = this.buildUrl(path) + `?upload_id=${encodeURIComponent(uploadId)}`;
      const response = await fetch(url, { method: "HEAD" });
      if (!response.ok) return 0;
      return Number(response.headers.get("X-Upload-Offset") ?? "0");
    }
  };
  _DataClient.RESUMABLE_THRESHOLD = 10 * 1024 * 1024;
  _DataClient.DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024;
  var DataClient = _DataClient;
  function graphDataClient(engineGatewayUrl, graphName) {
    return new DataClient(
      engineGatewayUrl,
      `/node-flow/graphs/${encodeURIComponent(graphName)}/data`
    );
  }
  return __toCommonJS(index_exports);
})();
