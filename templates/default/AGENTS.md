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

To discover all available built-in nodes:

```bash
uv run nonoha-engine/main.py --plugins ./plugins catalog -o catalog.json
```

**Important: Before planning or implementing any new node, always run the catalog command first to understand the full set of available nodes (113+). This prevents reinventing existing functionality.**

### Custom App (HTML/JS)

Edit `flows/default.vnf/app/index.html` to build a web UI that connects to the engine.
Uses `nonoha-client.iife.js` (IIFE bundle of nonoha-client-js) for WebSocket communication.

Key API methods (via `NonohaClient` global):

```javascript
const client = new NonohaClient.GraphClient(`${host}:${port}`, 'app');
client.connect();
client.addOutputCallback((data) => { /* data.portName, data.values */ });
client.addClosedCallback((wasClean) => { /* reconnect logic */ });
client.dispatchInput({ portName: 'name', values: [{ dataType, shape, array }] });
```

### Custom Views (ES modules)

Ship your own displays with the plugin: `plugins/user-nodes/static/views/`
holds a `manifest.json` and plain-JS view modules (see the example
`spectrum-bars.js`). The editor shows them as "View" nodes (add menu → Views);
apps show them with `NonohaClient.mountView`. Details: "Plugin Views" in
`nonoha-engine/AGENTS.md`.

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
| `plugins/user-nodes/static/views/` | Custom views for the editor and apps |
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
