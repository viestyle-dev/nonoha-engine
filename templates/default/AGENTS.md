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

## Key Files

| File | Purpose |
| --- | --- |
| `plugins/user-nodes/user_nodes/nodes.py` | Your custom node implementations |
| `plugins/user-nodes/user_nodes/__init__.py` | Node registration |
| `plugins/manifest.json` | Plugin enable/disable configuration |
| `flows/default.vnf/app/index.html` | Custom app UI |
| `flows/default.vnf/graphs/app.vng/graph.json` | App backend graph definition |
| `flows/default.vnf/graphs/app.vng/editors/nonoha-editor/models/settings.json` | Editor node layout |

## Technical Reference

For detailed implementation patterns, data types, API reference, and plugin structure:

See `nonoha-engine/AGENTS.md` — the comprehensive engine development guide.

## Architecture

- Engine: Python 3.11, FastAPI, numpy-based data flow
- All data flows as numpy arrays with batch dimensions (scalar 5.0 = np.array([5.0]))
- Nodes: 2-phase init (`__init__` for setup, `activate()` for runtime)
- Custom app communicates via WebSocket binary protocol
- App connects to `app.vng` graph; use GraphProxy for cross-graph data
  (the target graph must be listed before the referencing graph in `flow.json`)
