# Security Policy

## Reporting a Vulnerability

Please use GitHub's **Private Vulnerability Reporting**
(Security tab → "Report a vulnerability") on this repository.
Do not open public issues for security reports.

## Threat model

- **Graph definitions can execute code.** nonoha-core (bundled as a
  submodule) includes script nodes that compile and execute Python code
  embedded in graph definitions. **Loading an untrusted graph
  (.vnf / graph.json / graph.vjb) is equivalent to running untrusted
  Python code.** Only load graphs from sources you trust.
- **Plugins are arbitrary Python packages.** The engine imports and
  executes every plugin enabled in the plugins directory. Only install
  plugins from sources you trust.
- **The API has no authentication.** The engine binds to 127.0.0.1 by
  default, and its REST/WebSocket API is unauthenticated. Do not bind it
  to interfaces reachable from untrusted networks (`--host 0.0.0.0`)
  without an authenticating proxy in front of it.

## Supported versions

Security fixes target the latest minor release.
