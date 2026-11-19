/*! nonoha-client-js 1.1.0 | Apache-2.0 */
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
    EnvError: () => EnvError,
    GraphClient: () => GraphClient,
    INSPECTOR_PROTOCOL: () => INSPECTOR_PROTOCOL,
    InspectorClient: () => InspectorClient,
    InspectorCloseCode: () => InspectorCloseCode,
    PortDataType: () => PortDataType,
    SampleFlag: () => SampleFlag,
    clearEnv: () => clearEnv,
    fetchEngineCapabilities: () => fetchEngineCapabilities,
    fetchEnvStatus: () => fetchEnvStatus,
    fetchPlugins: () => fetchPlugins,
    graphDataClient: () => graphDataClient,
    makeGraphEndpoint: () => makeGraphEndpoint,
    nameToPortDataType: () => nameToPortDataType,
    parsePortValuesBytes: () => parsePortValuesBytes,
    pluginStaticUrl: () => pluginStaticUrl,
    setEnv: () => setEnv
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
      /** Per output port; lists are replaced on change, so delivery never allocates. */
      this.portCallbacks = /* @__PURE__ */ new Map();
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
          const callbacks = this.portCallbacks.get(portName);
          if (callbacks) {
            for (let i = 0; i < callbacks.length; ++i) callbacks[i](values);
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
    /**
     * Values of one output port. A port sends a value only when the graph
     * dispatches one, so a new subscriber sees nothing until then unless it
     * asks for the `current` value. Values are valid during the call only (the
     * arrays are reused for the port's next value). Returns the function that
     * stops the subscription.
     */
    subscribeOutput(portName, callback, options = {}) {
      let active = true;
      let live = false;
      const deliver = (values) => {
        live = true;
        callback(values);
      };
      this.portCallbacks.set(portName, (this.portCallbacks.get(portName) ?? []).concat(deliver));
      const current = options.current;
      if (current) {
        this.fetchOutputValues(portName).then((values) => {
          if (!active || live || values.length === 0) return;
          if (current === true) callback(values);
          else current(values);
        }).catch((error) => {
          if (active) options.onError?.(error);
        });
      }
      return () => {
        if (!active) return;
        active = false;
        const list = this.portCallbacks.get(portName);
        if (!list) return;
        const rest = list.filter((c) => c !== deliver);
        if (rest.length > 0) this.portCallbacks.set(portName, rest);
        else this.portCallbacks.delete(portName);
      };
    }
    addClosedCallback(callback) {
      this.onClosedCallbacks.push(callback);
    }
    // --- REST API ---
    /** The value an output port holds now; [] while it has none (the engine sends an empty body). */
    async fetchOutputValues(portName) {
      const url = `http://${this.engineGatewayUrl}/node-flow/graphs/${encodeURIComponent(this.graphName)}/outputs/${encodeURIComponent(portName)}/values`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Failed to fetch output values for '${portName}': ${res.status}`);
      const buf = await res.arrayBuffer();
      if (buf.byteLength === 0) return [];
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

  // src/capabilities.ts
  async function fetchEngineCapabilities(engineGatewayUrl, init) {
    const res = await fetch(`http://${engineGatewayUrl}/node-flow/capabilities`, init);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`capabilities: HTTP ${res.status}`);
    return await res.json();
  }

  // src/plugin-client.ts
  async function fetchPlugins(engineGatewayUrl) {
    const res = await fetch(`http://${engineGatewayUrl}/node-flow/plugins`);
    if (res.status === 404) return [];
    if (!res.ok) throw new Error(`plugins: HTTP ${res.status}`);
    return await res.json();
  }
  function pluginStaticUrl(engineGatewayUrl, plugin, path) {
    if (!plugin.static) return null;
    const folder = plugin.static.endsWith("/") ? plugin.static : `${plugin.static}/`;
    const file = path.replace(/^\.?\//, "").split("/").map(encodeURIComponent).join("/");
    const rev = plugin.rev ? `?rev=${encodeURIComponent(plugin.rev)}` : "";
    return `http://${engineGatewayUrl}${folder}${file}${rev}`;
  }

  // src/inspector-client.ts
  var INSPECTOR_PROTOCOL = 1;
  var InspectorCloseCode = {
    Disabled: 4403,
    NoGraph: 4404,
    /** The engine ended the session: the client stopped reading or acknowledging (reconnects). */
    Ended: 4408,
    TooMany: 4429
  };
  var FRAME_SAMPLE = 33;
  var HEADER_SIZE = 26;
  var WATCH_ID_MAX = 65535;
  var SampleFlag = {
    /** Cut by `slice`, or to fit `maxBytes`: fewer items, or strides (see `steps`). */
    Reduced: 1,
    /** Every item of the dispatch (`batch: 'all'`), or of every dispatch since the last sample (`'since'`). */
    BatchAll: 2,
    /** Numbers converted: `cast`, or complex values sent as their magnitude. */
    Cast: 4,
    /** `batch: 'since'`: items were lost before this sample (the engine could not keep or send them all). */
    Gap: 16
  };
  var NO_STEPS = [];
  var DEFAULT_INTERVAL_MS = 200;
  var MAX_BACKOFF_MS = 1e4;
  function refKey(ref) {
    return `${ref.node}\0${ref.dir}\0${ref.port}`;
  }
  function watchKey(ref, o) {
    return `${refKey(ref)}\0${o.maxBytes ?? ""}|${o.batch ?? "last"}|${JSON.stringify(o.slice ?? null)}|${(o.autoStride ?? []).join(",")}|${o.cast ?? ""}`;
  }
  var InspectorClient = class {
    constructor(engineGatewayUrl, graphName, options = {}) {
      this.socket = null;
      this.wanted = false;
      this.backoffMs = 500;
      this.reconnectTimer = null;
      this.nextWatchId = 1;
      this.nextActivityId = 1;
      this.watchesByKey = /* @__PURE__ */ new Map();
      this.watchesById = /* @__PURE__ */ new Map();
      this.activityIntervalMs = 500;
      this.activityPorts = /* @__PURE__ */ new Map();
      this.activityById = /* @__PURE__ */ new Map();
      this.changedActivity = [];
      this.activityListeners = /* @__PURE__ */ new Set();
      this.statusListeners = /* @__PURE__ */ new Set();
      this.helloListeners = /* @__PURE__ */ new Set();
      this._status = { state: "idle", reasons: [] };
      /** Last status reported by the engine (restored when the page becomes visible). */
      this.engineStatus = { state: "ok", reasons: [] };
      this._hello = null;
      this.hidden = false;
      this.onVisibility = () => this.applyVisibility();
      this.engineGatewayUrl = engineGatewayUrl;
      this.graphName = graphName;
      this.options = {
        clientName: options.clientName ?? "nonoha-client-js",
        reconnect: options.reconnect ?? true,
        pauseWhenHidden: options.pauseWhenHidden ?? true
      };
      this.WebSocketImpl = options.WebSocketImpl;
    }
    get status() {
      return this._status;
    }
    /** The engine's hello (limits and loaded plugins), once connected. */
    get hello() {
      return this._hello;
    }
    // --- connection ------------------------------------------------------------------
    connect() {
      this.wanted = true;
      if (this.socket) return;
      if (this.options.pauseWhenHidden && typeof document !== "undefined") {
        document.addEventListener("visibilitychange", this.onVisibility);
        this.hidden = document.visibilityState === "hidden";
      }
      this.open();
    }
    close() {
      this.wanted = false;
      if (this.reconnectTimer !== null) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", this.onVisibility);
      }
      const socket = this.socket;
      this.socket = null;
      if (socket) socket.close(1e3);
      this.setStatus({ state: "closed", reasons: [] });
    }
    open() {
      const Impl = this.WebSocketImpl ?? WebSocket;
      const url = `ws://${this.engineGatewayUrl}/node-flow/graphs/${encodeURIComponent(this.graphName)}/inspector/ws`;
      const socket = new Impl(url);
      socket.binaryType = "arraybuffer";
      this.socket = socket;
      this.setStatus({ state: "connecting", reasons: [] });
      socket.onopen = () => {
        this.backoffMs = 500;
        this.sendJson({ op: "hello", protocol: INSPECTOR_PROTOCOL, client: this.options.clientName });
        this.sendActivity();
        this.watchesById.forEach((watch) => this.sendWatch(watch));
        if (this.hidden) this.sendJson({ op: "pause" });
      };
      socket.onmessage = (event) => {
        const data = event.data;
        if (typeof data === "string") this.handleText(data);
        else this.handleSample(data);
      };
      socket.onclose = (event) => {
        if (this.socket !== socket) return;
        this.socket = null;
        this.handleClose(event.code);
      };
    }
    handleClose(code) {
      if (code === InspectorCloseCode.Disabled) {
        this.setStatus({ state: "disabled", reasons: [] });
        return;
      }
      if (code === InspectorCloseCode.NoGraph) {
        this.setStatus({ state: "no_graph", reasons: [] });
        return;
      }
      if (!this.wanted || !this.options.reconnect) {
        this.setStatus({ state: "closed", reasons: [] });
        return;
      }
      const reasons = code === InspectorCloseCode.TooMany ? ["too_many"] : code === InspectorCloseCode.Ended ? ["ended"] : [];
      this.setStatus({ state: "connecting", reasons });
      const delay = this.backoffMs;
      this.backoffMs = Math.min(MAX_BACKOFF_MS, this.backoffMs * 2);
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        if (this.wanted && !this.socket) this.open();
      }, delay);
    }
    applyVisibility() {
      const hidden = document.visibilityState === "hidden";
      if (hidden === this.hidden) return;
      this.hidden = hidden;
      this.sendJson({ op: hidden ? "pause" : "resume" });
      if (!this.socket) return;
      this.setStatus(hidden ? { state: "hidden", reasons: [] } : this.engineStatus);
    }
    /**
     * End the engine's own pause now (it paused sampling because its event
     * loop lagged; it would resume by itself once that recovers). Only for an
     * explicit user action: `pause`/`resume` from tab visibility concern this
     * connection alone.
     */
    forceResume() {
      this.sendJson({ op: "force_resume" });
    }
    // --- watches ---------------------------------------------------------------------
    watch(ref, options, callbacks) {
      const key = watchKey(ref, options);
      let watch = this.watchesByKey.get(key);
      if (!watch) {
        let id = this.nextWatchId;
        for (let tries = 0; this.watchesById.has(id) && tries < WATCH_ID_MAX; ++tries) {
          id = id >= WATCH_ID_MAX ? 1 : id + 1;
        }
        this.nextWatchId = id >= WATCH_ID_MAX ? 1 : id + 1;
        watch = {
          id,
          key,
          ref: { node: ref.node, dir: ref.dir, port: ref.port },
          options: { ...options },
          subscribers: [],
          intervalMs: Infinity,
          info: null,
          sample: { watchId: id, frameSeq: 0, sampleSeq: 0, dispatchCount: 0, t: 0, flags: 0, steps: NO_STEPS, values: [] },
          previous: void 0
        };
        this.watchesByKey.set(key, watch);
        this.watchesById.set(id, watch);
      }
      const subscriber = { intervalMs: options.intervalMs ?? DEFAULT_INTERVAL_MS, callbacks };
      watch.subscribers = watch.subscribers.concat(subscriber);
      if (!this.updateInterval(watch) && watch.subscribers.length > 1) {
        this.sendJson({ op: "snapshot", id: watch.id });
      }
      if (watch.info) callbacks.onInfo?.(watch.info);
      const engineWatch = watch;
      return {
        ref: engineWatch.ref,
        setInterval: (intervalMs) => {
          subscriber.intervalMs = intervalMs;
          this.updateInterval(engineWatch);
        },
        snapshot: () => this.sendJson({ op: "snapshot", id: engineWatch.id }),
        unwatch: () => {
          const remaining = engineWatch.subscribers.filter((s) => s !== subscriber);
          if (remaining.length === engineWatch.subscribers.length) return;
          engineWatch.subscribers = remaining;
          if (remaining.length === 0) {
            this.watchesByKey.delete(engineWatch.key);
            this.watchesById.delete(engineWatch.id);
            this.sendJson({ op: "unwatch", id: engineWatch.id });
          } else {
            this.updateInterval(engineWatch);
          }
        }
      };
    }
    /** Send the watch when its shortest interval changed; returns whether it was sent. */
    updateInterval(watch) {
      let min = Infinity;
      const subscribers = watch.subscribers;
      for (let i = 0; i < subscribers.length; ++i) if (subscribers[i].intervalMs < min) min = subscribers[i].intervalMs;
      if (min === watch.intervalMs) return false;
      watch.intervalMs = min;
      this.sendWatch(watch);
      return true;
    }
    sendWatch(watch) {
      const o = watch.options;
      this.sendJson({
        op: "watch",
        id: watch.id,
        node: watch.ref.node,
        dir: watch.ref.dir,
        port: watch.ref.port,
        interval_ms: watch.intervalMs,
        max_bytes: o.maxBytes,
        batch: o.batch ?? "last",
        slice: o.slice ?? null,
        auto_stride: o.autoStride ?? [],
        cast: o.cast ?? null
      });
    }
    // --- activity --------------------------------------------------------------------
    /**
     * Set the ports whose activity is reported (e.g. the ports visible on
     * screen); [] stops activity. Unchanged ports keep their statistics.
     */
    setActivityPorts(refs, intervalMs = this.activityIntervalMs) {
      const keep = /* @__PURE__ */ new Set();
      for (const ref of refs) {
        const key = refKey(ref);
        keep.add(key);
        if (!this.activityPorts.has(key)) {
          const id = this.nextActivityId++;
          const port = {
            id,
            entry: { ref: { node: ref.node, dir: ref.dir, port: ref.port }, count: 0, hz: 0, age: null, dtype: null, shape: null, stats: null, last: null }
          };
          this.activityPorts.set(key, port);
          this.activityById.set(id, port);
        }
      }
      this.activityPorts.forEach((port, key) => {
        if (!keep.has(key)) {
          this.activityPorts.delete(key);
          this.activityById.delete(port.id);
        }
      });
      this.activityIntervalMs = intervalMs;
      this.sendActivity();
    }
    /** Latest activity of a port, if it is in the activity set. */
    activityOf(ref) {
      return this.activityPorts.get(refKey(ref))?.entry;
    }
    onActivity(listener) {
      this.activityListeners.add(listener);
      return () => this.activityListeners.delete(listener);
    }
    onStatus(listener) {
      this.statusListeners.add(listener);
      return () => this.statusListeners.delete(listener);
    }
    onHello(listener) {
      this.helloListeners.add(listener);
      return () => this.helloListeners.delete(listener);
    }
    sendActivity() {
      const max = this._hello?.limits.max_activity_ports ?? Infinity;
      const ports = [];
      this.activityPorts.forEach(({ id, entry }) => {
        if (ports.length < max) ports.push({ id, node: entry.ref.node, dir: entry.ref.dir, port: entry.ref.port });
      });
      this.sendJson({ op: "activity", interval_ms: this.activityIntervalMs, ports });
    }
    // --- messages --------------------------------------------------------------------
    sendJson(message) {
      const socket = this.socket;
      if (socket && socket.readyState === 1) socket.send(JSON.stringify(message));
    }
    setStatus(status) {
      this._status = status;
      this.statusListeners.forEach((listener) => listener(status));
    }
    handleText(text) {
      let message;
      try {
        message = JSON.parse(text);
      } catch {
        return;
      }
      switch (message.t) {
        case "activity":
          this.handleActivity(message.p);
          break;
        case "watch_ack": {
          const watch = this.watchesById.get(message.id);
          if (!watch) break;
          watch.info = { types: message.types ?? [], shape: message.shape ?? null };
          const info = watch.info;
          watch.subscribers.forEach((s) => s.callbacks.onInfo?.(info));
          break;
        }
        case "gone": {
          const watch = this.watchesById.get(message.id);
          if (watch) watch.subscribers.forEach((s) => s.callbacks.onGone?.());
          break;
        }
        case "status":
          this.engineStatus = {
            state: message.state,
            reasons: message.reasons ?? [],
            lagMs: message.lag_ms,
            intervalScale: message.interval_scale
          };
          if (!this.hidden) this.setStatus(this.engineStatus);
          break;
        case "hello":
          if (message.protocol !== INSPECTOR_PROTOCOL) {
            this.wanted = false;
            this.socket?.close(1e3);
            this.setStatus({ state: "unsupported", reasons: [`protocol ${message.protocol}`] });
            break;
          }
          this._hello = { protocol: message.protocol, limits: message.limits ?? {}, plugins: message.plugins ?? [] };
          if (this.activityPorts.size > (this._hello.limits.max_activity_ports ?? Infinity)) this.sendActivity();
          this.engineStatus = { state: "ok", reasons: [] };
          this.setStatus(this.hidden ? { state: "hidden", reasons: [] } : this.engineStatus);
          const hello = this._hello;
          this.helloListeners.forEach((listener) => listener(hello));
          break;
        case "error": {
          const watch = message.id != null ? this.watchesById.get(message.id) : void 0;
          if (watch) watch.subscribers.forEach((s) => s.callbacks.onError?.(message.code, message.message));
          break;
        }
      }
    }
    handleActivity(rows) {
      const changed = this.changedActivity;
      changed.length = 0;
      for (let i = 0; i < rows.length; ++i) {
        const row = rows[i];
        const port = this.activityById.get(row[0]);
        if (!port) continue;
        const entry = port.entry;
        entry.count = row[1];
        entry.hz = row[2];
        entry.age = row[3];
        entry.dtype = row[4];
        entry.shape = row[5];
        entry.stats = row[6];
        entry.last = row[7];
        changed.push(entry);
      }
      if (changed.length === 0) return;
      this.activityListeners.forEach((listener) => listener(changed));
    }
    handleSample(buffer) {
      if (buffer.byteLength < HEADER_SIZE) return;
      const view = new DataView(buffer);
      if (view.getUint8(0) !== FRAME_SAMPLE) return;
      const frameSeq = view.getUint32(4);
      this.socket?.send('{"op":"ack","seq":' + frameSeq + "}");
      const watch = this.watchesById.get(view.getUint16(2));
      if (!watch) return;
      const sample = watch.sample;
      sample.frameSeq = frameSeq;
      sample.sampleSeq = view.getUint32(8);
      sample.dispatchCount = view.getUint32(12);
      sample.t = view.getFloat64(16);
      const flags = view.getUint8(24);
      sample.flags = flags;
      const slots = view.getUint8(25);
      let offset = HEADER_SIZE;
      if (slots === 0) {
        sample.steps = NO_STEPS;
      } else {
        let steps = sample.steps;
        if (steps === NO_STEPS || steps.length !== slots) steps = sample.steps = new Array(slots);
        for (let s = 0; s < slots; ++s) {
          const n = view.getUint8(offset++);
          let dims = steps[s];
          if (!dims || dims.length !== n) dims = steps[s] = new Array(n);
          for (let d = 0; d < n; ++d) {
            dims[d] = view.getUint16(offset);
            offset += 2;
          }
        }
      }
      const [values] = parsePortValuesBytes(view, offset, watch.previous);
      watch.previous = values;
      sample.values = values;
      const subscribers = watch.subscribers;
      for (let i = 0; i < subscribers.length; ++i) subscribers[i].callbacks.onSample(sample);
    }
  };

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

  // src/env-client.ts
  var EnvError = class extends Error {
    constructor(status, message) {
      super(message);
      this.status = status;
      this.name = "EnvError";
    }
  };
  async function requestEnv(url, init) {
    const res = await fetch(url, init);
    if (!res.ok) {
      let detail = "";
      try {
        const body = await res.json();
        if (typeof body.detail === "string") detail = body.detail;
      } catch {
      }
      throw new EnvError(res.status, detail || `HTTP ${res.status}`);
    }
    return await res.json();
  }
  function envUrl(engineGatewayUrl, name) {
    const base = `http://${engineGatewayUrl}/node-flow/env`;
    return name === void 0 ? base : `${base}/${encodeURIComponent(name)}`;
  }
  function fetchEnvStatus(engineGatewayUrl) {
    return requestEnv(envUrl(engineGatewayUrl));
  }
  function setEnv(engineGatewayUrl, name, value) {
    return requestEnv(envUrl(engineGatewayUrl, name), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value })
    });
  }
  function clearEnv(engineGatewayUrl, name) {
    return requestEnv(envUrl(engineGatewayUrl, name), { method: "DELETE" });
  }
  return __toCommonJS(index_exports);
})();
