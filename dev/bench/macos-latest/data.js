window.BENCHMARK_DATA = {
  "lastUpdate": 1794065077092,
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
          "id": "e2c954a5d2f2b12236cf1c4990c38d28e48577d3",
          "message": "publish",
          "timestamp": "2026-11-07T23:53:32+09:00",
          "tree_id": "2af8f13cbe59ae4d73d7e3949a7544649b200136",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/e2c954a5d2f2b12236cf1c4990c38d28e48577d3"
        },
        "date": 1794065076084,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 1226.0789057143766,
            "unit": "iter/sec",
            "range": "stddev: 0.0005577736563786986",
            "extra": "mean: 815.6081923759617 usec\nrounds: 1679"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 166.5291332623359,
            "unit": "iter/sec",
            "range": "stddev: 0.002717829240256281",
            "extra": "mean: 6.004955291664699 msec\nrounds: 216"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 1194.1323609858912,
            "unit": "iter/sec",
            "range": "stddev: 0.0006413947523211397",
            "extra": "mean: 837.4281048496056 usec\nrounds: 1650"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 1068.91142372795,
            "unit": "iter/sec",
            "range": "stddev: 0.0008519322734292231",
            "extra": "mean: 935.5312122237281 usec\nrounds: 1489"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 1160.8284791571803,
            "unit": "iter/sec",
            "range": "stddev: 0.00015819537004996585",
            "extra": "mean: 861.4537099624315 usec\nrounds: 1586"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 1137.3729842325629,
            "unit": "iter/sec",
            "range": "stddev: 0.0007748554789817",
            "extra": "mean: 879.2190546663505 usec\nrounds: 1500"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 217.09516294859574,
            "unit": "iter/sec",
            "range": "stddev: 0.0003235736162003295",
            "extra": "mean: 4.606274899992968 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1473.151244065046,
            "unit": "iter/sec",
            "range": "stddev: 0.00009661080142610602",
            "extra": "mean: 678.8169266589206 usec\nrounds: 1718"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 558192.1231203077,
            "unit": "iter/sec",
            "range": "stddev: 0.00001302646994093356",
            "extra": "mean: 1.791497870679417 usec\nrounds: 71008"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 117855.34559393198,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023940947488435496",
            "extra": "mean: 8.484977876569792 usec\nrounds: 190477"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 163462.92222917403,
            "unit": "iter/sec",
            "range": "stddev: 0.00004371073884203189",
            "extra": "mean: 6.117595270920253 usec\nrounds: 101689"
          }
        ]
      }
    ]
  }
}