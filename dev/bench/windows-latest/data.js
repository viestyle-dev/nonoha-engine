window.BENCHMARK_DATA = {
  "lastUpdate": 1793156804381,
  "repoUrl": "https://github.com/viestyle-dev/nonoha-engine",
  "entries": {
    "nonoha-engine Benchmark (windows-latest)": [
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
        "date": 1793156798579,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 718.0216667937984,
            "unit": "iter/sec",
            "range": "stddev: 0.00007948309827073322",
            "extra": "mean: 1.3927156327542691 msec\nrounds: 806"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 168.8931150955825,
            "unit": "iter/sec",
            "range": "stddev: 0.000598416741117964",
            "extra": "mean: 5.9209044692796695 msec\nrounds: 179"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 721.6078227274671,
            "unit": "iter/sec",
            "range": "stddev: 0.00008723828173385517",
            "extra": "mean: 1.3857942895079651 msec\nrounds: 753"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 651.8185164840569,
            "unit": "iter/sec",
            "range": "stddev: 0.00018168150619925192",
            "extra": "mean: 1.5341693657216924 msec\nrounds: 741"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 606.1915881688009,
            "unit": "iter/sec",
            "range": "stddev: 0.00010880971879853843",
            "extra": "mean: 1.6496434782620883 msec\nrounds: 713"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 671.3365053634761,
            "unit": "iter/sec",
            "range": "stddev: 0.00014772808439207107",
            "extra": "mean: 1.489565950921406 msec\nrounds: 652"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 215.9360829181054,
            "unit": "iter/sec",
            "range": "stddev: 0.0002255817220632449",
            "extra": "mean: 4.631000000028962 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1198.6911182991876,
            "unit": "iter/sec",
            "range": "stddev: 0.0009308732652984688",
            "extra": "mean: 834.2432714600333 usec\nrounds: 1724"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 524253.52778384637,
            "unit": "iter/sec",
            "range": "stddev: 8.319677239577717e-7",
            "extra": "mean: 1.9074740502512546 usec\nrounds: 57804"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 139018.7828660928,
            "unit": "iter/sec",
            "range": "stddev: 0.000014421470709026547",
            "extra": "mean: 7.1932725879439685 usec\nrounds: 172414"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 146426.70072491484,
            "unit": "iter/sec",
            "range": "stddev: 0.000008420806876646583",
            "extra": "mean: 6.8293555413684714 usec\nrounds: 166667"
          }
        ]
      }
    ]
  }
}