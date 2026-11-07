window.BENCHMARK_DATA = {
  "lastUpdate": 1794065018556,
  "repoUrl": "https://github.com/viestyle-dev/nonoha-engine",
  "entries": {
    "nonoha-engine Benchmark (ubuntu-latest)": [
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
        "date": 1794065018211,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 892.2690443708418,
            "unit": "iter/sec",
            "range": "stddev: 0.00011779702054820086",
            "extra": "mean: 1.120738196969639 msec\nrounds: 990"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 109.07964852963248,
            "unit": "iter/sec",
            "range": "stddev: 0.0005079851417064752",
            "extra": "mean: 9.167612964285825 msec\nrounds: 112"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 895.96430046535,
            "unit": "iter/sec",
            "range": "stddev: 0.00005402215442682872",
            "extra": "mean: 1.1161158982345787 msec\nrounds: 963"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 768.4579526550206,
            "unit": "iter/sec",
            "range": "stddev: 0.00012889892441278133",
            "extra": "mean: 1.301307373480881 msec\nrounds: 905"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 836.5408083396068,
            "unit": "iter/sec",
            "range": "stddev: 0.000042606701663218825",
            "extra": "mean: 1.1953989453124616 msec\nrounds: 896"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 810.1028010626982,
            "unit": "iter/sec",
            "range": "stddev: 0.00030007682530084614",
            "extra": "mean: 1.2344112360655877 msec\nrounds: 915"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 140.6517970242904,
            "unit": "iter/sec",
            "range": "stddev: 0.0002746043140034039",
            "extra": "mean: 7.109756300001635 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 736.1588850250818,
            "unit": "iter/sec",
            "range": "stddev: 0.00003961297996523259",
            "extra": "mean: 1.3584024051627508 msec\nrounds: 891"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 314002.35103661125,
            "unit": "iter/sec",
            "range": "stddev: 4.2027776017502875e-7",
            "extra": "mean: 3.1846895308226673 usec\nrounds: 163881"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 134438.30920408058,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010362459474685537",
            "extra": "mean: 7.43835597100508 usec\nrounds: 140194"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 94612.40785332186,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013346209095066435",
            "extra": "mean: 10.56943822368738 usec\nrounds: 98630"
          }
        ]
      }
    ]
  }
}