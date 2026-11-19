/*! nonoha-views 1.1.0 (view SDK 1) | Apache-2.0 */
"use strict";
var NonohaViews = (() => {
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
    VIEW_SDK_VERSION: () => VIEW_SDK_VERSION,
    builtinViewEntry: () => builtinViewEntry,
    builtinViews: () => builtinViews,
    createViewHost: () => createViewHost,
    defaultViewTheme: () => defaultViewTheme,
    defineView: () => defineView,
    inputAccepts: () => inputAccepts,
    levelMeterView: () => levelMeterView,
    loadView: () => loadView,
    loadViewCatalog: () => loadViewCatalog,
    manifestDrift: () => manifestDrift,
    manifestOf: () => manifestOf,
    mountView: () => mountView,
    resolveSettings: () => resolveSettings,
    spectrogramView: () => spectrogramView,
    typeAccepts: () => typeAccepts,
    viewDefinitionProblems: () => viewDefinitionProblems,
    viewMetadataOf: () => viewMetadataOf,
    watchOptionsFor: () => watchOptionsFor
  });

  // src/sdk.ts
  var VIEW_SDK_VERSION = 1;
  function defineView(definition) {
    return { sdk: VIEW_SDK_VERSION, ...definition };
  }
  function parseType(type) {
    const match = /^([a-z0-9]+)(?:\[(.*)\])?$/.exec(type.trim());
    if (!match) return { dtype: type.trim(), dims: [] };
    return { dtype: match[1], dims: match[2] ? match[2].split("x") : [] };
  }
  function typeAccepts(pattern, portType) {
    if (pattern === "any") return true;
    const p = parseType(pattern);
    const t = parseType(portType);
    if (p.dtype !== "any" && p.dtype !== t.dtype) return false;
    if (p.dims.length === 1 && p.dims[0] === "*") return true;
    if (p.dims.length !== t.dims.length) return false;
    for (let i = 0; i < p.dims.length; ++i) {
      if (p.dims[i] !== "?" && p.dims[i] !== t.dims[i]) return false;
    }
    return true;
  }
  function inputAccepts(input, portType) {
    for (let i = 0; i < input.accepts.length; ++i) if (typeAccepts(input.accepts[i], portType)) return true;
    return false;
  }

  // src/host.ts
  var WHOLE = Object.freeze({ steps: Object.freeze([]), gap: false });
  function resolveSetting(spec, value) {
    if (spec.type === "number") {
      const parsed = typeof value === "number" ? value : typeof value === "string" && value.trim() !== "" ? Number(value) : NaN;
      let number = Number.isFinite(parsed) ? parsed : typeof spec.default === "number" ? spec.default : void 0;
      if (number === void 0) return void 0;
      if (spec.min !== void 0 && number < spec.min) number = spec.min;
      if (spec.max !== void 0 && number > spec.max) number = spec.max;
      return number;
    }
    if (spec.type === "boolean") {
      if (value === true || value === "true") return true;
      if (value === false || value === "false") return false;
      return typeof spec.default === "boolean" ? spec.default : void 0;
    }
    const text = typeof value === "string" ? value : typeof value === "number" || typeof value === "boolean" ? String(value) : void 0;
    if (text !== void 0 && (!spec.enum || spec.enum.indexOf(text) >= 0)) return text;
    return typeof spec.default === "string" ? spec.default : void 0;
  }
  function resolveSettings(specs, raw) {
    const out = {};
    if (raw) {
      for (const key in raw) if (raw[key] !== void 0) out[key] = raw[key];
    }
    if (specs) {
      for (const key in specs) {
        const value = resolveSetting(specs[key], raw ? raw[key] : void 0);
        if (value === void 0) delete out[key];
        else out[key] = value;
      }
    }
    return out;
  }
  function createViewHost(view, element, options) {
    if (view.sdk !== VIEW_SDK_VERSION) throw new Error(`view "${view.id}" needs view SDK ${view.sdk}, host has ${VIEW_SDK_VERSION}`);
    const listeners = /* @__PURE__ */ new Map();
    const report = options.onError ?? ((error) => console.error(`[view ${view.id}]`, error));
    let settings = resolveSettings(view.settings, options.settings);
    let theme = options.theme;
    const size = { width: options.size.width, height: options.size.height };
    let frame = null;
    let pending = [];
    let running = [];
    let destroyed = false;
    let visible = true;
    const observer = typeof IntersectionObserver === "undefined" ? null : new IntersectionObserver((entries) => {
      visible = entries[entries.length - 1].isIntersecting;
      if (visible && pending.length > 0 && frame === null && !destroyed) frame = requestAnimationFrame(runFrame);
    });
    const runFrame = () => {
      frame = null;
      if (!visible) return;
      const draws = pending;
      pending = running;
      running = draws;
      for (let i = 0; i < draws.length; ++i) {
        try {
          draws[i]();
        } catch (error) {
          report(error);
        }
      }
      draws.length = 0;
    };
    const context = {
      onValues(input, callback) {
        const list = listeners.get(input) ?? [];
        listeners.set(input, list.concat(callback));
        return () => {
          const current = listeners.get(input);
          if (current) listeners.set(input, current.filter((c) => c !== callback));
        };
      },
      requestFrame(draw) {
        if (destroyed) return;
        if (pending.indexOf(draw) < 0) pending.push(draw);
        if (frame === null && visible) frame = requestAnimationFrame(runFrame);
      },
      get settings() {
        return settings;
      },
      get theme() {
        return theme;
      },
      get size() {
        return size;
      }
    };
    let instance;
    try {
      instance = view.mount(element, context);
    } catch (error) {
      report(error);
    }
    observer?.observe(element);
    return {
      deliver(input, values, info = WHOLE) {
        const list = listeners.get(input);
        if (!list) return;
        for (let i = 0; i < list.length; ++i) {
          try {
            list[i](values, info);
          } catch (error) {
            report(error);
          }
        }
      },
      resize(width, height) {
        if (width === size.width && height === size.height) return;
        size.width = width;
        size.height = height;
        instance?.resize?.(width, height);
      },
      setSettings(next) {
        settings = resolveSettings(view.settings, next);
        instance?.settingsChanged?.(settings);
      },
      setTheme(next) {
        theme = next;
        instance?.themeChanged?.(next);
      },
      destroy() {
        destroyed = true;
        observer?.disconnect();
        if (frame !== null) cancelAnimationFrame(frame);
        frame = null;
        pending.length = 0;
        listeners.clear();
        try {
          instance?.destroy?.();
        } catch (error) {
          report(error);
        }
      }
    };
  }
  function defaultViewTheme(isDark = true) {
    return isDark ? {
      isDark,
      background: "#111318",
      surface: "#1d2024",
      text: "#e2e2e9",
      textMuted: "#c4c6d0",
      grid: "#44474e",
      accent: "#b2c5ff",
      series: ["#7cb7ff", "#ffb870", "#7ad7a8", "#f48fb1", "#c5a3ff", "#ffe082", "#80deea", "#bcaaa4"],
      fontFamily: "system-ui, sans-serif"
    } : {
      isDark,
      background: "#ffffff",
      surface: "#f3f3fa",
      text: "#1a1b20",
      textMuted: "#44474e",
      grid: "#c4c6d0",
      accent: "#3450c3",
      series: ["#1565c0", "#e65100", "#2e7d32", "#ad1457", "#6a1b9a", "#f9a825", "#00838f", "#5d4037"],
      fontFamily: "system-ui, sans-serif"
    };
  }
  var EVERY_WATCH = { intervalMs: 66, batch: "since", maxBytes: 512 * 1024 };
  var LATEST_WATCH = { intervalMs: 66, batch: "all", maxBytes: 1024 * 1024, autoStride: [0, 1] };
  function watchOptionsFor(input) {
    return input.delivery === "latest" ? LATEST_WATCH : EVERY_WATCH;
  }

  // src/catalog.ts
  function builtinViewEntry(view) {
    return {
      key: `builtin/${view.id}`,
      id: view.id,
      title: view.title ?? view.id,
      description: view.description ?? "",
      inputs: view.inputs,
      settings: view.settings ?? {},
      size: view.size,
      suits: view.suits ?? [],
      source: "builtin",
      definition: view
    };
  }
  var VIEWS_FOLDER = "views/";
  async function loadViewCatalog(options) {
    const catalog = /* @__PURE__ */ new Map();
    for (const view of options.builtins ?? []) {
      const entry = builtinViewEntry(view);
      catalog.set(entry.key, entry);
    }
    const staticUrl = options.staticUrl;
    const manifests = await Promise.all(
      (options.plugins ?? []).map(async (plugin) => {
        const url = staticUrl?.(plugin, `${VIEWS_FOLDER}manifest.json`);
        if (!url) return null;
        try {
          const res = await fetch(url);
          if (res.status === 404) return null;
          if (!res.ok) throw new Error(`view manifest: HTTP ${res.status}`);
          const manifest = await res.json();
          if (manifest.sdk !== VIEW_SDK_VERSION) {
            throw new Error(`view manifest needs view SDK ${manifest.sdk}; this host has ${VIEW_SDK_VERSION}`);
          }
          return { plugin, manifest };
        } catch (error) {
          options.onError?.(plugin.id, error);
          return null;
        }
      })
    );
    for (const found of manifests) {
      if (!found) continue;
      const { plugin, manifest } = found;
      for (const view of manifest.views ?? []) {
        const moduleUrl = staticUrl?.(plugin, `${VIEWS_FOLDER}${view.module.replace(/^\.\//, "")}`);
        if (!moduleUrl) continue;
        const key = `${plugin.id}/${view.id}`;
        catalog.set(key, {
          key,
          id: view.id,
          title: view.title ?? view.id,
          description: view.description ?? "",
          inputs: view.inputs ?? [],
          settings: view.settings ?? {},
          size: view.size,
          suits: view.suits ?? [],
          source: "plugin",
          pluginId: plugin.id,
          pluginVersion: plugin.version,
          moduleUrl
        });
      }
    }
    return catalog;
  }
  function canonical(value) {
    if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
    if (value && typeof value === "object") {
      const record = value;
      return `{${Object.keys(record).filter((key) => record[key] !== void 0).sort().map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`).join(",")}}`;
    }
    return JSON.stringify(value);
  }
  function manifestDrift(entry, definition) {
    const drift = [];
    if (canonical(entry.inputs) !== canonical(definition.inputs)) drift.push("inputs");
    if (canonical(entry.settings) !== canonical(definition.settings ?? {})) drift.push("settings");
    return drift;
  }
  var moduleCache = /* @__PURE__ */ new Map();
  var reportedDrift = /* @__PURE__ */ new Set();
  function loadView(view) {
    if (typeof view !== "string" && view.source === "builtin") return Promise.resolve(view.definition);
    const url = typeof view === "string" ? view : view.moduleUrl;
    let pending = moduleCache.get(url);
    if (!pending) {
      pending = import(
        /* webpackIgnore: true */
        /* @vite-ignore */
        url
      ).then((mod) => {
        const definition = mod.default;
        if (!definition || typeof definition.mount !== "function") throw new Error(`${url} has no default view export`);
        if (definition.sdk !== VIEW_SDK_VERSION) {
          throw new Error(`${url} needs view SDK ${definition.sdk}; this host has ${VIEW_SDK_VERSION}`);
        }
        return definition;
      });
      pending.catch(() => moduleCache.delete(url));
      moduleCache.set(url, pending);
    }
    if (typeof view === "string") return pending;
    return pending.then((definition) => {
      if (!reportedDrift.has(url)) {
        reportedDrift.add(url);
        const drift = manifestDrift(view, definition);
        if (drift.length > 0) {
          console.warn(`[view ${view.key}] the module's ${drift.join(" and ")} differ from manifest.json; using the module's`);
        }
      }
      return definition;
    });
  }

  // src/manifest.ts
  function viewMetadataOf(view) {
    return {
      id: view.id,
      title: view.title,
      description: view.description,
      inputs: view.inputs,
      settings: view.settings,
      size: view.size,
      suits: view.suits
    };
  }
  function manifestOf(views) {
    return {
      sdk: VIEW_SDK_VERSION,
      views: views.map(({ module, view }) => {
        const { id, title, description, ...rest } = viewMetadataOf(view);
        return { id, title, description, module, ...rest };
      })
    };
  }
  var SETTING_TYPES = ["number", "string", "boolean"];
  var isText = (value) => typeof value === "string" && value !== "";
  var isFiniteNumber = (value) => typeof value === "number" && Number.isFinite(value);
  function viewDefinitionProblems(value) {
    if (!value || typeof value !== "object") return ["the default export is not a view object"];
    const view = value;
    const problems = [];
    if (view.sdk !== VIEW_SDK_VERSION) problems.push(`sdk is ${JSON.stringify(view.sdk)}, expected ${VIEW_SDK_VERSION}`);
    if (typeof view.mount !== "function") problems.push("mount is not a function");
    if (!isText(view.id) || view.id.indexOf("/") >= 0) problems.push('id must be a non-empty string without "/"');
    for (const key of ["title", "description"]) {
      if (view[key] !== void 0 && typeof view[key] !== "string") problems.push(`${key} must be a string`);
    }
    if (!Array.isArray(view.inputs)) {
      problems.push("inputs must be an array");
    } else {
      const names = /* @__PURE__ */ new Set();
      view.inputs.forEach((input, i) => {
        if (!input || !isText(input.name)) problems.push(`inputs[${i}].name must be a non-empty string`);
        else if (names.has(input.name)) problems.push(`input "${input.name}" is declared twice`);
        else names.add(input.name);
        if (!input || !Array.isArray(input.accepts) || input.accepts.length === 0 || !input.accepts.every(isText)) {
          problems.push(`inputs[${i}].accepts must be a non-empty array of types`);
        }
        if (input && input.delivery !== void 0 && input.delivery !== "every" && input.delivery !== "latest") {
          problems.push(`inputs[${i}].delivery must be "every" or "latest"`);
        }
      });
    }
    if (view.settings !== void 0) {
      if (!view.settings || typeof view.settings !== "object") problems.push("settings must be an object");
      else
        for (const [name, raw] of Object.entries(view.settings)) {
          const where = `setting "${name}"`;
          if (!raw || !SETTING_TYPES.includes(raw.type)) {
            problems.push(`${where}: type must be one of ${SETTING_TYPES.join(", ")}`);
            continue;
          }
          if (raw.default !== void 0 && typeof raw.default !== raw.type) problems.push(`${where}: default must be a ${raw.type}`);
          if (raw.enum !== void 0) {
            if (raw.type !== "string" || !Array.isArray(raw.enum) || !raw.enum.every(isText)) problems.push(`${where}: enum must list strings of a string setting`);
            else if (raw.default !== void 0 && !raw.enum.includes(raw.default)) problems.push(`${where}: default is not in enum`);
          }
          for (const bound of ["min", "max"]) {
            if (raw[bound] === void 0) continue;
            if (raw.type !== "number" || !isFiniteNumber(raw[bound])) problems.push(`${where}: ${bound} must be a number of a number setting`);
          }
          if (isFiniteNumber(raw.min) && isFiniteNumber(raw.max) && raw.min > raw.max) problems.push(`${where}: min is above max`);
          if (isFiniteNumber(raw.default)) {
            if (isFiniteNumber(raw.min) && raw.default < raw.min || isFiniteNumber(raw.max) && raw.default > raw.max) {
              problems.push(`${where}: default is outside min..max`);
            }
          }
        }
    }
    if (view.size !== void 0) {
      const size = view.size;
      if (!size || !isFiniteNumber(size.width) || !isFiniteNumber(size.height)) problems.push("size must be { width, height } in px");
    }
    if (view.suits !== void 0) {
      if (!Array.isArray(view.suits)) problems.push("suits must be an array");
      else
        view.suits.forEach((suit, i) => {
          if (!suit || !isText(suit.node) || !isText(suit.port)) problems.push(`suits[${i}] must be { node, port }`);
        });
    }
    return problems;
  }

  // src/mount.ts
  var GAP = 16;
  async function mountView(view, element, options) {
    const { bindings, outputs, samples } = options;
    for (const input in bindings) {
      const byPort = typeof bindings[input] === "string";
      if (byPort ? !outputs : !samples) throw new Error(`binding "${input}" needs options.${byPort ? "outputs" : "samples"}`);
    }
    const definition = "mount" in view ? view : await loadView(view);
    const report = options.onError ?? ((error) => console.error(`[view ${definition.id}]`, error));
    const rect = element.getBoundingClientRect();
    const host = createViewHost(definition, element, {
      theme: options.theme ?? defaultViewTheme(true),
      settings: options.settings,
      size: { width: rect.width, height: rect.height },
      onError: options.onError
    });
    const stops = [];
    const watches = [];
    for (const input in bindings) {
      const binding = bindings[input];
      const spec = definition.inputs.find((i) => i.name === input) ?? { name: input, accepts: ["any"] };
      if (typeof binding === "string") {
        stops.push(
          outputs.subscribeOutput(binding, (values) => host.deliver(input, values), {
            current: spec.delivery === "latest",
            onError: options.onError
          })
        );
        continue;
      }
      const { watch, ...ref } = binding;
      const info = { steps: [], gap: false };
      watches.push(
        samples.watch(ref, watch ?? watchOptionsFor(spec), {
          onSample: (sample) => {
            info.steps = sample.steps;
            info.gap = (sample.flags & GAP) !== 0;
            host.deliver(input, sample.values, info);
          },
          // e.g. too_large: the value does not fit the input's budget even reduced
          onError: (code, message) => report(new Error(`${input}: ${message} (${code})`)),
          onGone: () => report(new Error(`${input}: the port ${ref.node}.${ref.port} is gone`))
        })
      );
    }
    const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver((entries) => {
      const box = entries[entries.length - 1].contentRect;
      host.resize(box.width, box.height);
    }) : null;
    observer?.observe(element);
    return {
      host,
      unmount() {
        observer?.disconnect();
        for (let i = 0; i < stops.length; ++i) stops[i]();
        for (let i = 0; i < watches.length; ++i) watches[i].unwatch();
        host.destroy();
      }
    };
  }

  // src/builtin/canvas.ts
  var pixelRatio = () => typeof devicePixelRatio === "number" && devicePixelRatio > 0 ? devicePixelRatio : 1;
  function createSurface(element, width, height) {
    const canvas = document.createElement("canvas");
    canvas.style.display = "block";
    element.appendChild(canvas);
    const g = canvas.getContext("2d");
    if (!g) throw new Error("2D canvas is not available");
    const state = { width: 0, height: 0, dpr: pixelRatio() };
    const apply = () => {
      const w = Math.max(1, Math.round(state.width * state.dpr));
      const h = Math.max(1, Math.round(state.height * state.dpr));
      canvas.style.width = `${state.width}px`;
      canvas.style.height = `${state.height}px`;
      if (canvas.width === w && canvas.height === h) return false;
      canvas.width = w;
      canvas.height = h;
      return true;
    };
    const surface = {
      canvas,
      g,
      get width() {
        return state.width;
      },
      get height() {
        return state.height;
      },
      get dpr() {
        return state.dpr;
      },
      setSize(w, h) {
        state.width = Math.max(0, w);
        state.height = Math.max(0, h);
        return apply();
      },
      syncPixelRatio() {
        const dpr = pixelRatio();
        if (dpr === state.dpr) return false;
        state.dpr = dpr;
        apply();
        return true;
      },
      begin() {
        g.setTransform(state.width > 0 ? canvas.width / state.width : 1, 0, 0, state.height > 0 ? canvas.height / state.height : 1, 0, 0);
      },
      destroy() {
        canvas.remove();
      }
    };
    surface.setSize(width, height);
    return surface;
  }
  function font(px, family, weight = 400) {
    return `${weight} ${px}px ${family}`;
  }

  // src/builtin/scales.ts
  var DB_FLOOR = -200;
  function powerToDb(power) {
    return power > 1e-20 ? 10 * Math.log10(power) : DB_FLOOR;
  }
  function amplitudeToDb(amplitude) {
    const a = amplitude < 0 ? -amplitude : amplitude;
    return a > 1e-10 ? 20 * Math.log10(a) : DB_FLOOR;
  }
  function log10PowerToDb(value) {
    const db = 10 * value;
    return db > DB_FLOOR ? db : DB_FLOOR;
  }
  function dbToUnit(db, minDb, maxDb) {
    if (!(maxDb > minDb)) return 0;
    const t = (db - minDb) / (maxDb - minDb);
    return t <= 0 ? 0 : t >= 1 ? 1 : t;
  }
  var clean = (x) => Number(x.toPrecision(12));
  function frequencyTicks(fMin, fMax, log, maxTicks) {
    const ticks = [];
    if (!(fMax > fMin) || maxTicks < 1) return ticks;
    if (log) {
      if (!(fMin > 0)) return ticks;
      const d0 = Math.floor(Math.log10(fMin));
      const d1 = Math.ceil(Math.log10(fMax));
      for (const mantissas of [[1, 2, 5], [1]]) {
        ticks.length = 0;
        for (let d = d0; d <= d1; ++d) {
          for (const m of mantissas) {
            const f = clean(m * Math.pow(10, d));
            if (f >= fMin * (1 - 1e-9) && f <= fMax * (1 + 1e-9)) ticks.push(f);
          }
        }
        if (ticks.length <= maxTicks) return ticks;
      }
      const stride = Math.ceil(ticks.length / maxTicks);
      return ticks.filter((_, i) => i % stride === 0);
    }
    const raw = (fMax - fMin) / maxTicks;
    const magnitude = Math.pow(10, Math.floor(Math.log10(raw)));
    let step = magnitude * 10;
    for (const m of [1, 2, 5, 10]) {
      if (m * magnitude >= raw) {
        step = m * magnitude;
        break;
      }
    }
    for (let f = Math.ceil(fMin / step) * step; f <= fMax * (1 + 1e-9); f += step) ticks.push(clean(f));
    return ticks;
  }
  function formatFrequency(f) {
    const a = Math.abs(f);
    if (a >= 1e3) return `${Number((f / 1e3).toFixed(a >= 1e4 ? 0 : 1))}k`;
    if (a >= 100) return String(Math.round(f));
    if (a >= 1) return String(Number(f.toFixed(1)));
    if (a === 0) return "0";
    return String(Number(f.toPrecision(2)));
  }
  function createRowMap() {
    return {
      rows: 0,
      bins: 0,
      lo: new Int32Array(0),
      hi: new Int32Array(0),
      frac: new Float32Array(0),
      uMin: 0,
      uMax: 0,
      log: false,
      u: new Float64Array(0)
    };
  }
  function fractionalBin(u, first, last, x) {
    if (x <= u[first]) return first;
    if (x >= u[last]) return last;
    let lo = first;
    let hi = last;
    while (hi - lo > 1) {
      const mid = lo + hi >> 1;
      if (u[mid] <= x) lo = mid;
      else hi = mid;
    }
    const span = u[hi] - u[lo];
    return span > 0 ? lo + (x - u[lo]) / span : lo;
  }
  function buildRowMap(map, rows, bins, freqs, log) {
    if (map.lo.length < rows) {
      map.lo = new Int32Array(rows);
      map.hi = new Int32Array(rows);
      map.frac = new Float32Array(rows);
    }
    if (map.u.length < bins) map.u = new Float64Array(bins);
    map.rows = rows;
    map.bins = bins;
    map.log = log;
    const u = map.u;
    let first = 0;
    for (let k = 0; k < bins; ++k) {
      const f = freqs ? freqs[k] : k;
      u[k] = log ? f > 0 ? Math.log10(f) : -Infinity : f;
    }
    if (log) while (first < bins - 1 && !(u[first] > -Infinity)) ++first;
    const last = bins - 1;
    map.uMin = bins > 0 ? u[first] : 0;
    map.uMax = bins > 0 ? u[last] : 0;
    const span = map.uMax - map.uMin;
    if (!(span > 0) || bins < 2) {
      for (let r = 0; r < rows; ++r) {
        map.lo[r] = Math.max(0, first);
        map.hi[r] = -1;
        map.frac[r] = 0;
      }
      return;
    }
    for (let r = 0; r < rows; ++r) {
      const a = map.uMin + span * r / rows;
      const b = map.uMin + span * (r + 1) / rows;
      const pa = fractionalBin(u, first, last, a);
      const pb = fractionalBin(u, first, last, b);
      if (pb - pa >= 1) {
        const lo = Math.round(pa);
        map.lo[r] = lo;
        map.hi[r] = r === rows - 1 ? bins : Math.min(bins, Math.max(lo + 1, Math.round(pb)));
        map.frac[r] = 0;
      } else {
        const pc = fractionalBin(u, first, last, (a + b) / 2);
        const lo = Math.min(last, Math.floor(pc));
        map.lo[r] = lo;
        map.hi[r] = -1;
        map.frac[r] = pc - lo;
      }
    }
  }
  function rowValue(map, values, offset, r) {
    const lo = map.lo[r];
    const hi = map.hi[r];
    let v = values[offset + lo];
    if (hi < 0) {
      const f = map.frac[r];
      if (f > 0 && lo + 1 < map.bins) v += (values[offset + lo + 1] - v) * f;
      return v;
    }
    for (let k = lo + 1; k < hi; ++k) {
      const x = values[offset + k];
      if (x > v) v = x;
    }
    return v;
  }
  function frequencyToUnit(map, f) {
    const x = map.log ? f > 0 ? Math.log10(f) : NaN : f;
    const span = map.uMax - map.uMin;
    return span > 0 ? (x - map.uMin) / span : NaN;
  }
  function accumulateBlock(data, channels, sumSq, peak) {
    const n = data.length - data.length % channels;
    let c = 0;
    for (let i = 0; i < n; ++i) {
      const x = data[i];
      if (x === x) {
        sumSq[c] += x * x;
        const a = x < 0 ? -x : x;
        if (a > peak[c]) peak[c] = a;
      }
      if (++c === channels) c = 0;
    }
    return n / channels;
  }
  function meterTickStep(minDb, lengthPx, minSpacing) {
    const range = Math.abs(minDb);
    for (const step of [1, 2, 3, 6, 10, 12, 20, 30, 60]) {
      if (lengthPx * step / range >= minSpacing) return step;
    }
    return range;
  }
  function meterTicks(minDb, step) {
    const ticks = [];
    if (!(step > 0) || !(minDb < 0)) return [0];
    for (let db = 0; db >= minDb - 1e-9; db -= step) ticks.push(db);
    return ticks;
  }
  function fallToward(current, target, dt, rate) {
    if (target >= current) return target;
    const next = current - rate * dt;
    return next > target ? next : target;
  }

  // src/builtin/level-meter.ts
  var HOT_DB = -6;
  var STALE_SECONDS = 0.3;
  function createMeterState(channels, minDb) {
    return {
      channels,
      rms: new Float32Array(channels).fill(minDb),
      peak: new Float32Array(channels).fill(minDb),
      hold: new Float32Array(channels).fill(minDb),
      holdLeft: new Float32Array(channels),
      clipLeft: new Float32Array(channels)
    };
  }
  function stepMeterChannel(m, c, rmsDb, peakDb, clipped, dt, fallRate, holdTime, minDb) {
    m.rms[c] = fallToward(m.rms[c], rmsDb > minDb ? rmsDb : minDb, dt, fallRate);
    const peak = m.peak[c] = fallToward(m.peak[c], peakDb > minDb ? peakDb : minDb, dt, fallRate);
    if (peak >= m.hold[c]) {
      m.hold[c] = peak;
      m.holdLeft[c] = holdTime;
    } else if (m.holdLeft[c] > 0) {
      m.holdLeft[c] = Math.max(0, m.holdLeft[c] - dt);
    } else {
      m.hold[c] = Math.max(peak, m.hold[c] - fallRate * dt);
    }
    m.clipLeft[c] = clipped ? holdTime : Math.max(0, m.clipLeft[c] - dt);
    return m.rms[c] > minDb || peak > minDb || m.hold[c] > minDb || m.clipLeft[c] > 0;
  }
  function sampleArray(value) {
    if (!value) return null;
    const array = value.array;
    if (array instanceof Float32Array || array instanceof Float64Array) return array;
    return null;
  }
  var now = () => typeof performance !== "undefined" ? performance.now() : Date.now();
  var levelMeterView = defineView({
    id: "level-meter",
    title: "Level meter",
    description: "Per-channel RMS and peak levels in dBFS with peak hold and a clip lamp.",
    inputs: [
      {
        name: "frames",
        accepts: ["f32", "f32[?]", "f32[?x?]", "f64", "f64[?]", "f64[?x?]"],
        delivery: "every",
        // levels are measured over all samples
        description: "Audio samples: rows = samples, last axis = channels (a plain f32 stream is mono)"
      }
    ],
    settings: {
      decay: { type: "number", default: 1.5, min: 0.05, max: 30, description: "Seconds the peak hold stays; bars fall the whole scale in this time" },
      minDb: { type: "number", default: -60, min: -200, max: -6, description: "Bottom of the scale in dBFS" }
    },
    size: { width: 160, height: 220 },
    mount(element, ctx) {
      const surface = createSurface(element, ctx.size.width, ctx.size.height);
      const g = surface.g;
      let theme = ctx.theme;
      let decay = 1.5;
      let minDb = -60;
      let channels = 0;
      let meter = createMeterState(0, minDb);
      let sumSq = new Float64Array(0);
      let blockPeak = new Float32Array(0);
      let pendingFrames = 0;
      let targetRms = new Float32Array(0);
      let targetPeak = new Float32Array(0);
      let clipNow = new Uint8Array(0);
      let lastData = -Infinity;
      let lastFrame = now();
      let layoutDirty = true;
      let vertical = true;
      let x0 = 0;
      let x1 = 0;
      let y0 = 0;
      let y1 = 0;
      let length = 0;
      let slot = 0;
      let gap = 0;
      let showReadout = false;
      let tickUnits = new Float32Array(0);
      let tickLabels = [];
      let readoutKeys = new Int32Array(0);
      let readouts = [];
      let labelFont = "";
      let animating = false;
      const scale = document.createElement("canvas");
      const sg = scale.getContext("2d");
      if (!sg) throw new Error("2D canvas is not available");
      let scaleDirty = true;
      function setChannels(n) {
        channels = n;
        meter = createMeterState(n, minDb);
        sumSq = new Float64Array(n);
        blockPeak = new Float32Array(n);
        targetRms = new Float32Array(n).fill(minDb);
        targetPeak = new Float32Array(n).fill(minDb);
        clipNow = new Uint8Array(n);
        readoutKeys = new Int32Array(n).fill(2147483647);
        readouts = new Array(n).fill("");
        pendingFrames = 0;
        layoutDirty = true;
        scaleDirty = true;
      }
      function readSettings(settings) {
        decay = settings.decay;
        const nextMin = settings.minDb;
        if (nextMin !== minDb) {
          minDb = nextMin;
          setChannels(channels);
        }
        layoutDirty = true;
      }
      function layout() {
        layoutDirty = false;
        scaleDirty = true;
        const w = surface.width;
        const h = surface.height;
        const pad = 6;
        const lamp = 5;
        vertical = w <= h * 1.33;
        const n = Math.max(1, channels);
        if (vertical) {
          x0 = pad + 28;
          x1 = w - pad;
          slot = Math.max(0, (x1 - x0) / n);
          showReadout = slot >= 26 && h >= 90;
          y0 = pad + lamp + 3;
          y1 = h - pad - (showReadout ? 14 : 0);
          length = Math.max(0, y1 - y0);
        } else {
          y0 = pad;
          y1 = h - pad - 14;
          slot = Math.max(0, (y1 - y0) / n);
          showReadout = slot >= 10 && w >= 140;
          x0 = pad;
          x1 = w - pad - (showReadout ? 40 : 0) - lamp - 3;
          length = Math.max(0, x1 - x0);
        }
        gap = Math.min(8, slot * 0.2);
        const step = meterTickStep(minDb, length, vertical ? 16 : 28);
        const ticks = meterTicks(minDb, step);
        tickUnits = new Float32Array(ticks.length);
        tickLabels = ticks.map((db) => String(db));
        for (let i = 0; i < ticks.length; ++i) tickUnits[i] = dbToUnit(ticks[i], minDb, 0);
      }
      function span(to, u0, u1, c0, c1) {
        if (u1 <= u0) return;
        if (vertical) to.fillRect(c0, y1 - u1 * length, c1 - c0, (u1 - u0) * length);
        else to.fillRect(x0 + u0 * length, c0, (u1 - u0) * length, c1 - c0);
      }
      function bar(u, hotU, c0, c1) {
        g.fillStyle = theme.accent;
        span(g, 0, Math.min(u, hotU), c0, c1);
        if (u > hotU) {
          g.fillStyle = theme.series[1] ?? theme.accent;
          span(g, hotU, u, c0, c1);
        }
      }
      function drawScale(s) {
        scaleDirty = false;
        const canvas = surface.canvas;
        if (scale.width !== canvas.width || scale.height !== canvas.height) {
          scale.width = canvas.width;
          scale.height = canvas.height;
        }
        const w = surface.width;
        const h = surface.height;
        s.setTransform(w > 0 ? canvas.width / w : 1, 0, 0, h > 0 ? canvas.height / h : 1, 0, 0);
        s.globalAlpha = 1;
        s.fillStyle = theme.background;
        s.fillRect(0, 0, w, h);
        s.font = labelFont;
        const n = Math.max(1, channels);
        s.globalAlpha = 0.3;
        s.fillStyle = theme.grid;
        for (let c = 0; c < n; ++c) {
          const c0 = (vertical ? x0 : y0) + c * slot + gap / 2;
          span(s, 0, 1, c0, c0 + slot - gap);
        }
        s.globalAlpha = 1;
        s.fillStyle = theme.textMuted;
        s.strokeStyle = theme.grid;
        s.lineWidth = 1;
        s.beginPath();
        if (vertical) {
          s.textAlign = "right";
          s.textBaseline = "middle";
          for (let i = 0; i < tickUnits.length; ++i) {
            const y = Math.round(y1 - tickUnits[i] * length) + 0.5;
            s.moveTo(x0 - 4, y);
            s.lineTo(x0 - 1, y);
            s.fillText(tickLabels[i], x0 - 6, y);
          }
        } else {
          s.textAlign = "center";
          s.textBaseline = "top";
          for (let i = 0; i < tickUnits.length; ++i) {
            const x = Math.round(x0 + tickUnits[i] * length) + 0.5;
            s.moveTo(x, y1 + 1);
            s.lineTo(x, y1 + 4);
            s.fillText(tickLabels[i], Math.min(w - 10, Math.max(10, x)), y1 + 4);
          }
        }
        s.stroke();
        if (channels === 0) {
          s.textAlign = "center";
          s.textBaseline = "middle";
          s.fillText("Waiting for frames\u2026", w / 2, h / 2);
        }
      }
      function draw() {
        const t = now();
        const dt = Math.min(0.1, Math.max(0, (t - lastFrame) / 1e3));
        lastFrame = t;
        if (surface.syncPixelRatio()) layoutDirty = true;
        if (layoutDirty) layout();
        if (pendingFrames > 0) {
          for (let c = 0; c < channels; ++c) {
            targetRms[c] = amplitudeToDb(Math.sqrt(sumSq[c] / pendingFrames));
            targetPeak[c] = amplitudeToDb(blockPeak[c]);
            clipNow[c] = blockPeak[c] >= 1 ? 1 : 0;
            sumSq[c] = 0;
            blockPeak[c] = 0;
          }
          pendingFrames = 0;
        }
        const fresh = (t - lastData) / 1e3 < STALE_SECONDS;
        const fallRate = -minDb / decay;
        let moving = fresh;
        for (let c = 0; c < channels; ++c) {
          if (stepMeterChannel(meter, c, fresh ? targetRms[c] : minDb, fresh ? targetPeak[c] : minDb, clipNow[c] === 1, dt, fallRate, decay, minDb)) moving = true;
          clipNow[c] = 0;
        }
        if (scaleDirty && sg) drawScale(sg);
        g.setTransform(1, 0, 0, 1, 0, 0);
        g.globalAlpha = 1;
        g.drawImage(scale, 0, 0);
        surface.begin();
        const hotU = dbToUnit(HOT_DB, minDb, 0);
        g.font = labelFont;
        for (let c = 0; c < channels; ++c) {
          const c0 = (vertical ? x0 : y0) + c * slot + gap / 2;
          const c1 = c0 + slot - gap;
          const peakU = dbToUnit(meter.peak[c], minDb, 0);
          const rmsU = dbToUnit(meter.rms[c], minDb, 0);
          g.globalAlpha = 0.35;
          bar(peakU, hotU, c0, c1);
          g.globalAlpha = 1;
          bar(rmsU, hotU, c0, c1);
          const holdU = dbToUnit(meter.hold[c], minDb, 0);
          if (holdU > 0) {
            g.fillStyle = theme.text;
            span(g, Math.max(0, holdU - 2 / Math.max(1, length)), holdU, c0, c1);
          }
          g.globalAlpha = meter.clipLeft[c] > 0 ? 1 : 0.3;
          g.fillStyle = meter.clipLeft[c] > 0 ? theme.series[1] ?? theme.accent : theme.grid;
          if (vertical) g.fillRect(c0, y0 - 8, c1 - c0, 5);
          else g.fillRect(x1 + 3, c0, 5, c1 - c0);
          g.globalAlpha = 1;
          if (showReadout) {
            const hold = meter.hold[c];
            const key = hold > minDb ? Math.round(hold * 10) : -2147483647;
            if (key !== readoutKeys[c]) {
              readoutKeys[c] = key;
              readouts[c] = hold > minDb ? (key / 10).toFixed(1) : "-\u221E";
            }
            g.fillStyle = theme.textMuted;
            if (vertical) {
              g.textAlign = "center";
              g.textBaseline = "top";
              g.fillText(readouts[c], (c0 + c1) / 2, y1 + 3);
            } else {
              g.textAlign = "left";
              g.textBaseline = "middle";
              g.fillText(readouts[c], x1 + 12, (c0 + c1) / 2);
            }
          }
        }
        animating = moving;
        if (animating) ctx.requestFrame(draw);
      }
      function wake() {
        if (!animating) lastFrame = now();
        ctx.requestFrame(draw);
      }
      readSettings(ctx.settings);
      labelFont = font(10, theme.fontFamily);
      const off = ctx.onValues("frames", (values) => {
        const value = values[0];
        const data = sampleArray(value);
        if (!value || !data || data.length === 0) return;
        const shape = value.shape;
        const n = shape.length >= 2 ? Math.max(1, shape[shape.length - 1]) : 1;
        if (n !== channels) setChannels(n);
        pendingFrames += accumulateBlock(data, n, sumSq, blockPeak);
        lastData = now();
        wake();
      });
      ctx.requestFrame(draw);
      return {
        resize(width, height) {
          surface.setSize(width, height);
          layoutDirty = true;
          wake();
        },
        settingsChanged(settings) {
          readSettings(settings);
          wake();
        },
        themeChanged(next) {
          theme = next;
          labelFont = font(10, theme.fontFamily);
          scaleDirty = true;
          wake();
        },
        destroy() {
          off();
          surface.destroy();
        }
      };
    }
  });

  // src/builtin/color.ts
  function hexByte(hex, i, short) {
    return short ? parseInt(hex[i] + hex[i], 16) : parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  function channel(text, scale) {
    const value = parseFloat(text);
    if (!isFinite(value)) return NaN;
    return text.endsWith("%") ? value / 100 * scale : value;
  }
  function parseColor(css) {
    const s = css.trim().toLowerCase();
    if (s === "transparent") return [0, 0, 0, 0];
    if (s[0] === "#") {
      const hex = s.slice(1);
      if (!/^[0-9a-f]+$/.test(hex)) return null;
      if (hex.length === 3 || hex.length === 4) {
        return [hexByte(hex, 0, true), hexByte(hex, 1, true), hexByte(hex, 2, true), hex.length === 4 ? hexByte(hex, 3, true) : 255];
      }
      if (hex.length === 6 || hex.length === 8) {
        return [hexByte(hex, 0, false), hexByte(hex, 1, false), hexByte(hex, 2, false), hex.length === 8 ? hexByte(hex, 3, false) : 255];
      }
      return null;
    }
    const match = /^rgba?\(([^)]*)\)$/.exec(s);
    if (!match) return null;
    const parts = match[1].split(/[\s,/]+/).filter(Boolean);
    if (parts.length < 3 || parts.length > 4) return null;
    const r = channel(parts[0], 255);
    const g = channel(parts[1], 255);
    const b = channel(parts[2], 255);
    const a = parts.length === 4 ? channel(parts[3], 1) * 255 : 255;
    if (!(isFinite(r) && isFinite(g) && isFinite(b) && isFinite(a))) return null;
    const clamp = (v) => Math.max(0, Math.min(255, Math.round(v)));
    return [clamp(r), clamp(g), clamp(b), clamp(a)];
  }
  var probe = null;
  function resolveColor(css) {
    const parsed = parseColor(css);
    if (parsed) return parsed;
    if (typeof document !== "undefined") {
      if (!probe) probe = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
      if (probe) {
        probe.clearRect(0, 0, 1, 1);
        probe.fillStyle = "#808080";
        probe.fillStyle = css;
        probe.fillRect(0, 0, 1, 1);
        const d = probe.getImageData(0, 0, 1, 1).data;
        return [d[0], d[1], d[2], d[3]];
      }
    }
    return [128, 128, 128, 255];
  }
  function gradientLut(stops, size = 256, positions) {
    const lut = new Uint8ClampedArray(size * 4);
    const n = stops.length;
    if (n === 0) return lut;
    for (let i = 0; i < size; ++i) {
      const t = size > 1 ? i / (size - 1) : 0;
      let k = 0;
      while (k < n - 2 && t > (positions ? positions[k + 1] : (k + 1) / (n - 1))) ++k;
      const t0 = positions ? positions[k] : k / Math.max(1, n - 1);
      const t1 = positions ? positions[Math.min(k + 1, n - 1)] : (k + 1) / Math.max(1, n - 1);
      const a = stops[k];
      const b = stops[Math.min(k + 1, n - 1)];
      const f = t1 > t0 ? Math.max(0, Math.min(1, (t - t0) / (t1 - t0))) : 0;
      lut[i * 4] = a[0] + (b[0] - a[0]) * f;
      lut[i * 4 + 1] = a[1] + (b[1] - a[1]) * f;
      lut[i * 4 + 2] = a[2] + (b[2] - a[2]) * f;
      lut[i * 4 + 3] = a[3] + (b[3] - a[3]) * f;
    }
    return lut;
  }
  var VIRIDIS = [
    [68, 1, 84, 255],
    [72, 36, 117, 255],
    [65, 68, 135, 255],
    [53, 95, 141, 255],
    [42, 120, 142, 255],
    [33, 145, 140, 255],
    [34, 168, 132, 255],
    [68, 191, 112, 255],
    [122, 209, 81, 255],
    [189, 223, 38, 255],
    [253, 231, 37, 255]
  ];

  // src/builtin/spectrogram.ts
  var COLORMAPS = ["theme", "viridis"];
  var MAX_IMAGE_ROWS = 2048;
  function renderColumn(map, history, offset, pixels, start, stride, lut, minDb, maxDb) {
    const rows = map.rows;
    const top = (lut.length >> 2) - 1;
    for (let y = 0, o = start; y < rows; ++y, o += stride) {
      const v = rowValue(map, history, offset, rows - 1 - y);
      const i = v <= DB_FLOOR ? 0 : (dbToUnit(v, minDb, maxDb) * top + 0.5 | 0) << 2;
      pixels[o] = lut[i];
      pixels[o + 1] = lut[i + 1];
      pixels[o + 2] = lut[i + 2];
      pixels[o + 3] = lut[i + 3];
    }
  }
  function numericArray(value) {
    if (!value) return null;
    const array = value.array;
    if (array instanceof Float32Array || array instanceof Float64Array) return array;
    return null;
  }
  function rowsOf(value) {
    const shape = value.shape;
    if (shape.length >= 2) return { rows: shape[0], length: shape[shape.length - 1] };
    return { rows: 1, length: shape[0] ?? 0 };
  }
  var spectrogramView = defineView({
    id: "spectrogram",
    title: "Spectrogram",
    description: "Scrolling heatmap of spectra: each input row becomes one column, newest on the right.",
    inputs: [
      {
        name: "spectrum",
        accepts: ["f32[?]", "f64[?]"],
        delivery: "every",
        // each row is a column of the history
        description: "Power spectrum per row (linear power; log10 power with inputIsLog10)"
      },
      {
        name: "freqs",
        accepts: ["f32[?]", "f64[?]"],
        delivery: "latest",
        optional: true,
        description: "Frequency of each bin in Hz (labels the frequency axis)"
      }
    ],
    settings: {
      columns: { type: "number", default: 300, min: 10, max: 4e3, description: "History length (rows shown as columns)" },
      logFrequency: { type: "boolean", default: true, description: "Logarithmic frequency axis" },
      dbRange: { type: "number", default: 60, min: 1, max: 300, description: "Shown dynamic range in dB below the loudest value in view" },
      inputIsLog10: { type: "boolean", default: false, description: "Input is log10(power) instead of linear power" },
      colormap: { type: "string", default: "theme", enum: [...COLORMAPS], description: "theme: background to accent to text; or viridis" }
    },
    size: { width: 420, height: 220 },
    mount(element, ctx) {
      const surface = createSurface(element, ctx.size.width, ctx.size.height);
      const g = surface.g;
      const image = document.createElement("canvas");
      const ig = image.getContext("2d");
      const bar = document.createElement("canvas");
      bar.width = 1;
      bar.height = 256;
      const barg = bar.getContext("2d");
      if (!ig || !barg) throw new Error("2D canvas is not available");
      const barPixels = barg.createImageData(1, 256);
      const map = createRowMap();
      let theme = ctx.theme;
      let columns = 0;
      let logFrequency = true;
      let dbRange = 60;
      let inputIsLog10 = false;
      let colormap = "theme";
      let bins = 0;
      let history = new Float32Array(0);
      let colMax = new Float32Array(0);
      let head = 0;
      let filled = 0;
      let freqs = new Float64Array(0);
      let freqCount = 0;
      let lut = new Uint8ClampedArray(0);
      let pixels = null;
      let imageRows = 0;
      let layoutDirty = true;
      let rebake = true;
      let dirtyColumns = 0;
      let bakedTop = NaN;
      let hasData = false;
      const plot = { x: 0, y: 0, w: 0, h: 0 };
      let showBar = false;
      let tickY = new Float32Array(0);
      let tickLabels = [];
      let topLabel = "";
      let bottomLabel = "";
      let labelFont = "";
      function resetHistory() {
        history = new Float32Array(columns * bins);
        colMax = new Float32Array(columns).fill(DB_FLOOR);
        head = columns - 1;
        filled = 0;
        bakedTop = NaN;
        layoutDirty = true;
      }
      function readSettings(settings) {
        const nextColumns = Math.round(settings.columns);
        const nextLog10 = settings.inputIsLog10;
        const nextColormap = settings.colormap;
        const nextLogFrequency = settings.logFrequency;
        dbRange = settings.dbRange;
        const reset = nextColumns !== columns || nextLog10 !== inputIsLog10;
        const recolor = nextColormap !== colormap;
        if (nextLogFrequency !== logFrequency) layoutDirty = true;
        columns = nextColumns;
        inputIsLog10 = nextLog10;
        colormap = nextColormap;
        logFrequency = nextLogFrequency;
        if (reset) resetHistory();
        if (recolor) applyTheme();
        rebake = true;
      }
      function applyTheme() {
        labelFont = font(10, theme.fontFamily);
        lut = colormap === "viridis" ? gradientLut(VIRIDIS) : gradientLut([resolveColor(theme.background), resolveColor(theme.accent), resolveColor(theme.text)], 256, [0, 0.6, 1]);
        const d = barPixels.data;
        for (let y = 0; y < 256; ++y) {
          const i = 255 - y << 2;
          d[y * 4] = lut[i];
          d[y * 4 + 1] = lut[i + 1];
          d[y * 4 + 2] = lut[i + 2];
          d[y * 4 + 3] = 255;
        }
        barg.putImageData(barPixels, 0, 0);
        rebake = true;
      }
      function layout() {
        layoutDirty = false;
        rebake = true;
        const useFreqs = freqCount === bins && bins > 1;
        const left = useFreqs ? 36 : 6;
        showBar = surface.width >= 220;
        const right = showBar ? 46 : 6;
        plot.x = left;
        plot.y = 6;
        plot.w = Math.max(0, surface.width - left - right);
        plot.h = Math.max(0, surface.height - 12);
        const rows = Math.max(1, Math.min(MAX_IMAGE_ROWS, Math.round(plot.h * surface.dpr)));
        if (rows !== imageRows || !pixels || pixels.width !== columns) {
          imageRows = rows;
          image.width = Math.max(1, columns);
          image.height = rows;
          pixels = ig.createImageData(Math.max(1, columns), rows);
        }
        if (bins > 0) buildRowMap(map, imageRows, bins, useFreqs ? freqs : null, logFrequency);
        tickLabels = [];
        if (useFreqs && map.uMax > map.uMin) {
          const fMin = logFrequency ? Math.pow(10, map.uMin) : map.uMin;
          const fMax = logFrequency ? Math.pow(10, map.uMax) : map.uMax;
          const ticks = frequencyTicks(fMin, fMax, logFrequency, Math.max(2, Math.floor(plot.h / 18)));
          tickY = new Float32Array(ticks.length);
          for (let i = 0; i < ticks.length; ++i) {
            tickY[i] = plot.y + plot.h * (1 - frequencyToUnit(map, ticks[i]));
            tickLabels.push(formatFrequency(ticks[i]));
          }
        }
      }
      function currentTop() {
        let top = DB_FLOOR;
        for (let i = 0; i < columns; ++i) if (colMax[i] > top) top = colMax[i];
        return top;
      }
      function renderSlot(slot) {
        const top = bakedTop;
        renderColumn(map, history, slot * bins, pixels.data, slot * 4, columns * 4, lut, top - dbRange, top);
      }
      function renderAll() {
        rebake = false;
        dirtyColumns = 0;
        if (!pixels) return;
        pixels.data.fill(0);
        bakedTop = currentTop();
        if (bins > 0) {
          for (let age = 0; age < filled; ++age) renderSlot((head - age + columns) % columns);
        }
        ig.putImageData(pixels, 0, 0);
        topLabel = bakedTop > DB_FLOOR ? `${Math.round(bakedTop)} dB` : "";
        bottomLabel = bakedTop > DB_FLOOR ? `${Math.round(bakedTop - dbRange)}` : "";
      }
      function flushColumns() {
        const n = Math.min(dirtyColumns, columns);
        dirtyColumns = 0;
        if (n <= 0 || !pixels) return;
        const start = head - n + 1;
        if (start >= 0) {
          ig.putImageData(pixels, 0, 0, start, 0, n, imageRows);
        } else {
          ig.putImageData(pixels, 0, 0, 0, 0, head + 1, imageRows);
          ig.putImageData(pixels, 0, 0, columns + start, 0, -start, imageRows);
        }
      }
      function ingest(src, offset) {
        head = (head + 1) % columns;
        const base = head * bins;
        let max = DB_FLOOR;
        for (let k = 0; k < bins; ++k) {
          const v = src[offset + k];
          const db = inputIsLog10 ? log10PowerToDb(v) : powerToDb(v);
          history[base + k] = db;
          if (db > max) max = db;
        }
        colMax[head] = max;
        if (filled < columns) ++filled;
        if (!rebake && !layoutDirty) {
          renderSlot(head);
          ++dirtyColumns;
        }
      }
      function draw() {
        if (surface.syncPixelRatio()) layoutDirty = true;
        if (layoutDirty) layout();
        if (!rebake && filled > 0) {
          const top = currentTop();
          if (!(top <= bakedTop + 0.5 && top >= bakedTop - 3)) rebake = true;
        }
        if (rebake) renderAll();
        else flushColumns();
        surface.begin();
        const width = surface.width;
        const height = surface.height;
        g.fillStyle = theme.background;
        g.fillRect(0, 0, width, height);
        if (plot.w <= 0 || plot.h <= 0) return;
        g.font = labelFont;
        if (filled > 0 && columns > 0) {
          g.imageSmoothingEnabled = false;
          const colW = plot.w / columns;
          const older = columns - head - 1;
          if (older > 0) g.drawImage(image, head + 1, 0, older, imageRows, plot.x, plot.y, older * colW, plot.h);
          g.drawImage(image, 0, 0, head + 1, imageRows, plot.x + older * colW, plot.y, (head + 1) * colW, plot.h);
        } else {
          g.fillStyle = theme.textMuted;
          g.textAlign = "center";
          g.textBaseline = "middle";
          g.fillText(hasData ? "No spectrum rows" : "Waiting for spectrum\u2026", plot.x + plot.w / 2, plot.y + plot.h / 2);
        }
        g.strokeStyle = theme.grid;
        g.lineWidth = 1;
        g.strokeRect(plot.x - 0.5, plot.y - 0.5, plot.w + 1, plot.h + 1);
        if (tickLabels.length > 0) {
          g.fillStyle = theme.textMuted;
          g.textAlign = "right";
          g.textBaseline = "middle";
          g.beginPath();
          for (let i = 0; i < tickLabels.length; ++i) {
            const y = Math.round(tickY[i]) + 0.5;
            g.moveTo(plot.x - 4, y);
            g.lineTo(plot.x, y);
            g.fillText(tickLabels[i], plot.x - 6, Math.min(plot.y + plot.h - 5, Math.max(plot.y + 5, y)));
          }
          g.stroke();
        }
        if (showBar) {
          const x = plot.x + plot.w + 6;
          g.imageSmoothingEnabled = true;
          g.drawImage(bar, x, plot.y, 6, plot.h);
          g.strokeRect(x - 0.5, plot.y - 0.5, 7, plot.h + 1);
          g.fillStyle = theme.textMuted;
          g.textAlign = "left";
          g.textBaseline = "top";
          g.fillText(topLabel, x + 10, plot.y);
          g.textBaseline = "bottom";
          g.fillText(bottomLabel, x + 10, plot.y + plot.h);
        }
      }
      readSettings(ctx.settings);
      applyTheme();
      const offSpectrum = ctx.onValues("spectrum", (values) => {
        const value = values[0];
        const src = numericArray(value);
        if (!src) return;
        const { rows, length } = rowsOf(value);
        if (length <= 0 || rows <= 0 || src.length < rows * length) return;
        hasData = true;
        if (length !== bins) {
          bins = length;
          resetHistory();
        }
        for (let r = Math.max(0, rows - columns); r < rows; ++r) ingest(src, r * length);
        ctx.requestFrame(draw);
      });
      const offFreqs = ctx.onValues("freqs", (values) => {
        const value = values[0];
        const src = numericArray(value);
        if (!src) return;
        const { rows, length } = rowsOf(value);
        if (length <= 0 || rows <= 0 || src.length < rows * length) return;
        const offset = (rows - 1) * length;
        let same = length === freqCount;
        for (let k = 0; same && k < length; ++k) same = freqs[k] === src[offset + k];
        if (same) return;
        if (freqs.length < length) freqs = new Float64Array(length);
        for (let k = 0; k < length; ++k) freqs[k] = src[offset + k];
        freqCount = length;
        layoutDirty = true;
        ctx.requestFrame(draw);
      });
      ctx.requestFrame(draw);
      return {
        resize(width, height) {
          surface.setSize(width, height);
          layoutDirty = true;
          ctx.requestFrame(draw);
        },
        settingsChanged(settings) {
          readSettings(settings);
          ctx.requestFrame(draw);
        },
        themeChanged(next) {
          theme = next;
          applyTheme();
          ctx.requestFrame(draw);
        },
        destroy() {
          offSpectrum();
          offFreqs();
          surface.destroy();
        }
      };
    }
  });

  // src/builtin/index.ts
  var builtinViews = [spectrogramView, levelMeterView];
  return __toCommonJS(index_exports);
})();
