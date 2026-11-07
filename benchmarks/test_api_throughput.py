"""Benchmarks for REST API endpoint throughput."""


def test_get_graphs(benchmark, client):
    """GET /node-flow/graphs — lightweight list operation."""
    def do_request():
        r = client.get("/node-flow/graphs")
        assert r.status_code == 200

    benchmark(do_request)


def test_get_catalog_nodes(benchmark, client):
    """GET /node-flow/catalog/nodes — iterates all node definitions."""
    def do_request():
        r = client.get("/node-flow/catalog/nodes")
        assert r.status_code == 200

    benchmark(do_request)


def test_get_node_list(benchmark, client, node_flow):
    """GET /node-flow/graphs/{g}/nodes — list nodes in a loaded graph."""
    graph_name = next(iter(node_flow.graph_names))

    def do_request():
        r = client.get(f"/node-flow/graphs/{graph_name}/nodes")
        assert r.status_code == 200

    benchmark(do_request)


def test_get_edges(benchmark, client, node_flow):
    """GET /node-flow/graphs/{g}/edges — list edges in a loaded graph."""
    graph_name = next(iter(node_flow.graph_names))

    def do_request():
        r = client.get(f"/node-flow/graphs/{graph_name}/edges")
        assert r.status_code == 200

    benchmark(do_request)


def test_get_graph_inputs(benchmark, client, node_flow):
    """GET /node-flow/graphs/{g}/inputs — list graph-level inputs."""
    graph_name = next(iter(node_flow.graph_names))

    def do_request():
        r = client.get(f"/node-flow/graphs/{graph_name}/inputs")
        assert r.status_code == 200

    benchmark(do_request)


def test_get_graph_outputs(benchmark, client, node_flow):
    """GET /node-flow/graphs/{g}/outputs — list graph-level outputs."""
    graph_name = next(iter(node_flow.graph_names))

    def do_request():
        r = client.get(f"/node-flow/graphs/{graph_name}/outputs")
        assert r.status_code == 200

    benchmark(do_request)
