window.BENCHMARK_DATA = {
  "lastUpdate": 1793156727219,
  "repoUrl": "https://github.com/viestyle-dev/nonoha-engine",
  "entries": {
    "nonoha-engine Benchmark (macos-latest)": [
      {
        "commit": {
          "author": {
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "committer": {
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "distinct": true,
          "id": "8a373aaf79d7c91ee2e3a7eebf9c7d1be581c797",
          "message": "publish",
          "timestamp": "2026-10-28T12:02:48+09:00",
          "tree_id": "8a6a8de5dbdca598f765bf12d9f873f66184053a",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/8a373aaf79d7c91ee2e3a7eebf9c7d1be581c797"
        },
        "date": 1793156725399,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 1272.823623503641,
            "unit": "iter/sec",
            "range": "stddev: 0.00007181505841052922",
            "extra": "mean: 785.6548083601305 usec\nrounds: 1555"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 173.194613684816,
            "unit": "iter/sec",
            "range": "stddev: 0.0010256206209781247",
            "extra": "mean: 5.773851615384677 msec\nrounds: 221"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 1154.2073341849127,
            "unit": "iter/sec",
            "range": "stddev: 0.0004547540456367134",
            "extra": "mean: 866.3954649934607 usec\nrounds: 1514"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 1032.706780092451,
            "unit": "iter/sec",
            "range": "stddev: 0.0002650768475983324",
            "extra": "mean: 968.3290739221029 usec\nrounds: 1461"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 821.168761809012,
            "unit": "iter/sec",
            "range": "stddev: 0.0010682684453620392",
            "extra": "mean: 1.2177764748345126 msec\nrounds: 1510"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 907.4965303335077,
            "unit": "iter/sec",
            "range": "stddev: 0.0007618877859745328",
            "extra": "mean: 1.1019325877009107 msec\nrounds: 1431"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 267.4711700182686,
            "unit": "iter/sec",
            "range": "stddev: 0.00029235922200296274",
            "extra": "mean: 3.738720699998055 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1420.3026416861842,
            "unit": "iter/sec",
            "range": "stddev: 0.0003213613855532932",
            "extra": "mean: 704.0752939900185 usec\nrounds: 1847"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 624179.4510699328,
            "unit": "iter/sec",
            "range": "stddev: 0.00000502391365417684",
            "extra": "mean: 1.6021033667254942 usec\nrounds: 77167"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 95325.43765753064,
            "unit": "iter/sec",
            "range": "stddev: 0.000006267187213100897",
            "extra": "mean: 10.490379321337432 usec\nrounds: 177778"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 163169.88240613916,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033513774589914694",
            "extra": "mean: 6.128581973914419 usec\nrounds: 110096"
          }
        ]
      }
    ]
  }
}