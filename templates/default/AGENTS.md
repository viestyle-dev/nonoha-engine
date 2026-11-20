# AGENTS.md

## Workspace Overview

This is a nonoha-engine workspace — a visual node-based data processing environment.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the engine
uv run nonoha-engine/main.py --vnf flows/default.vnf --plugins ./plugins

# Open in browser
# Editor: http://localhost:8000/editor?engine-uri=localhost:8000
# Custom App: http://localhost:8000/app
```

## What You Can Build

### Custom Nodes (Python)

Create processing nodes in `plugins/user-nodes/user_nodes/nodes.py`.
See working examples: Synthesizer (multi-harmonic waveform synthesis) and SpectrumAnalyzer (FFT + band decomposition).

Declare every property of a node in its `PROPERTIES`, with `description`, `data_type` and `default_value` (as the examples do). The property then gets an input port `@name`, so another node's output can set it. Types: real `f64`, integer `i32`, `bool`, text `str`.

To discover all available built-in nodes:

```bash
uv run nonoha-engine/main.py --plugins ./plugins catalog -o catalog.json
```

**Important: Before planning or implementing any new node, always run the catalog command first to understand the full set of available nodes (113+). This prevents reinventing existing functionality.**

### Custom App (HTML/JS)

Edit `flows/default.vnf/app/index.html` to build a web UI that connects to the engine.
Uses `nonoha-client.iife.js` (IIFE bundle of nonoha-client-js, global `NonohaClient`) for engine
communication; `nonoha-views.iife.js` (global `NonohaViews`) shows plugin views.

Key API methods (via `NonohaClient` global):

```javascript
const client = new NonohaClient.GraphClient(`${host}:${port}`, 'app');
client.connect();
client.addOutputCallback((data) => { /* data.portName, data.values */ });
// One port; outputs are sent when they change, so `current` starts from the value it holds now.
client.subscribeOutput('name', (values) => { /* ... */ }, { current: true });
client.addClosedCallback((wasClean) => { /* reconnect logic */ });
client.dispatchInput({ portName: 'name', values: [{ dataType, shape, array }] });
```

### Custom Views (ES modules)

A view is a read-only display of port values. The editor shows it as a
"View" node (add menu → Views); the app shows it with `NonohaViews`. It never
writes to a graph: graph inputs come from the editor's input nodes or the app.
Views live in `plugins/user-nodes/user_nodes/static/views/` as plain ES modules with no
imports (the browser loads them directly; see the example `spectrum-bars.js`):

```js
export default {
  sdk: 1,
  id: "my-view", title: "My view", description: "...",
  inputs: [{ name: "values", accepts: ["f32[?]"], delivery: "latest", description: "..." }],
  settings: { gain: { type: "number", default: 1, min: 0, max: 10 } },
  size: { width: 420, height: 300 },
  suits: [{ node: "MyNode", port: "out" }],   // node outputs to suggest this view for
  mount(el, ctx) {               // ctx: onValues, requestFrame, settings, theme, size
    const canvas = el.appendChild(document.createElement("canvas"))
    let latest = 0
    ctx.onValues("values", values => { latest = values[0].array[0]; ctx.requestFrame(draw) })
    function draw() { /* draw latest * ctx.settings.gain with ctx.theme colors */ }
    return { resize(w, h) {}, settingsChanged(s) {}, destroy() { canvas.remove() } }
  },
}
```

- `accepts`: nonoha types without the batch dimension, `?` for any size
  (`u8[?x?x3]`), `f32[*]` for any rank, or `any`. An input takes one value of
  any of these types.
- `delivery`: what the view needs. `"every"` (default) is a stream (meters,
  history, events): every value from now on. `"latest"` is a state (an image,
  the current spectrum): the current value first, values in between may be
  skipped.
- Values from an output port are whole. Values from an internal port (a
  dashed edge, sampled by the inspector) fit a byte budget: a `"latest"`
  input keeps the newest items, and an item too large arrives strided.
  `ctx.onValues(input, (values, info) => …)` tells it: `info.steps` (per
  value, the stride of each non-batch dimension; empty when whole) and
  `info.gap` (items were lost before these).
- `ctx.settings` arrive resolved: numbers kept within `min`..`max`, `enum`
  strings validated, defaults filled.
- Draw only inside `ctx.requestFrame`, copy what you keep (values are valid
  during the callback), and use `ctx.theme` colors.
- `manifest.json` next to the modules lists them as data. Generate it from
  the modules, e.g. with nonoha-views' tool (in nonoha-editor; without
  `--write` it compares):
  `node <nonoha-views>/bin/view-manifest.mjs --write plugins/user-nodes/user_nodes/static/views`

Show views in the app (`flows/default.vnf/app/` loads both IIFEs):

```js
const gateway = `${location.hostname}:${location.port}`
const graph = new NonohaClient.GraphClient(gateway, 'app')
graph.connect()
NonohaClient.fetchPlugins(gateway)
  .then(plugins => NonohaViews.loadViewCatalog({
    plugins,
    staticUrl: (plugin, path) => NonohaClient.pluginStaticUrl(gateway, plugin, path),
  }))
  .then(catalog => NonohaViews.mountView(catalog.get('user_nodes/my-view'), document.getElementById('stage'), {
    bindings: { values: 'my_output' },   // view input -> output port of `graph`
    outputs: graph,                      // the app opens and closes its clients
  }))
  .then(view => { /* view.host.setSettings({...}) later; view.unmount() to remove */ })
```

The contract's reference is nonoha-views' README (in nonoha-editor).

### Monitoring in the Editor

With the inspector (engine 1.1+), output ports glow while values flow;
click a port name to peek, pin the peek as a display node, or preview an
output inside its node (eye icon in the node toolbar). A display node can
connect straight to an engine node output (dashed, sampled); select the
dashed edge → "Make output port" when an app needs every value.

### API Keys and Per-machine Values

Keys and other per-machine values are **environment values**: the graph
stores only a name, the value lives in this workspace's `.env` (never
published, exported or built; it is in `.gitignore`). Nodes read them with
`nonoha_core.environment.get(name)` when they use them and declare the names
in `describe()` (`NodeDoc.env`). Set values in nonoha Hub or with `nonoha ws
env set` while the engine is stopped, or in the editor (menu > Environment
settings) while it runs. Values that differ per machine but are not secret
(a camera index) are graph properties. Details: "Environment Values" in
`nonoha-engine/AGENTS.md`.

### Access

The engine has no login. It refuses requests from other web sites and
rebound host names; tunnels and VPN host names need `--allow-host NAME`.
With `--host 0.0.0.0` anyone on the network can edit graphs and run code.

## Key Files

| File | Purpose |
| --- | --- |
| `plugins/user-nodes/user_nodes/nodes.py` | Your custom node implementations |
| `plugins/user-nodes/user_nodes/__init__.py` | Node registration |
| `plugins/manifest.json` | Plugin enable/disable configuration |
| `flows/default.vnf/app/index.html` | Custom app UI |
| `flows/default.vnf/graphs/app.vng/graph.json` | App backend graph definition |
| `flows/default.vnf/graphs/app.vng/editors/nonoha-editor/models/settings.json` | Editor node layout (positions, display nodes, waypoints) |
| `plugins/user-nodes/user_nodes/static/views/` | Custom views for the editor and apps |
| `.env` | This machine's environment values (API keys); never committed, published or built |

## Technical Reference

For detailed implementation patterns, data types, API reference, and plugin structure:

See `nonoha-engine/AGENTS.md` — the comprehensive engine development guide.

## Architecture

- Engine: Python 3.11, FastAPI, numpy-based data flow
- All data flows as numpy arrays with batch dimensions (scalar 5.0 = np.array([5.0]))
- A dispatched value is valid during the dispatch only: senders may reuse their output buffers, so copy a received value (`values[0].copy()`) to keep it past the callback
- Nodes: 2-phase init (`__init__` for setup, `activate()` for runtime)
- Custom app communicates via WebSocket binary protocol
- App connects to `app.vng` graph; use GraphProxy for cross-graph data
  (the target graph must be listed before the referencing graph in `flow.json`)
