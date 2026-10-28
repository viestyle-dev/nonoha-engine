window.BENCHMARK_DATA = {
  "lastUpdate": 1793156666204,
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
          "id": "8a373aaf79d7c91ee2e3a7eebf9c7d1be581c797",
          "message": "publish",
          "timestamp": "2026-10-28T12:02:48+09:00",
          "tree_id": "8a6a8de5dbdca598f765bf12d9f873f66184053a",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/8a373aaf79d7c91ee2e3a7eebf9c7d1be581c797"
        },
        "date": 1793156665567,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 876.7130710583516,
            "unit": "iter/sec",
            "range": "stddev: 0.00006183682341680318",
            "extra": "mean: 1.1406240342610825 msec\nrounds: 934"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 112.50299787756772,
            "unit": "iter/sec",
            "range": "stddev: 0.0001220802208096077",
            "extra": "mean: 8.888652025862084 msec\nrounds: 116"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 848.0715212228332,
            "unit": "iter/sec",
            "range": "stddev: 0.00006583781298669447",
            "extra": "mean: 1.1791458326039548 msec\nrounds: 914"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 782.0574886490891,
            "unit": "iter/sec",
            "range": "stddev: 0.00010211990068345226",
            "extra": "mean: 1.2786783766080683 msec\nrounds: 855"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 784.1686843031583,
            "unit": "iter/sec",
            "range": "stddev: 0.00004782234263350718",
            "extra": "mean: 1.2752358261904293 msec\nrounds: 840"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 803.1373007896914,
            "unit": "iter/sec",
            "range": "stddev: 0.00003750968441328114",
            "extra": "mean: 1.2451171163594839 msec\nrounds: 868"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 153.0501541222577,
            "unit": "iter/sec",
            "range": "stddev: 0.00030314481193186184",
            "extra": "mean: 6.533805900000544 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 766.0045878980118,
            "unit": "iter/sec",
            "range": "stddev: 0.00004231535232116547",
            "extra": "mean: 1.3054752096773907 msec\nrounds: 992"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 330385.60148407647,
            "unit": "iter/sec",
            "range": "stddev: 5.232027488037711e-7",
            "extra": "mean: 3.0267662861457865 usec\nrounds: 175809"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 133896.31237649015,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010433559735564108",
            "extra": "mean: 7.468465577963016 usec\nrounds: 143658"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 97052.19921417048,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013027495614414625",
            "extra": "mean: 10.303733538209107 usec\nrounds: 103467"
          }
        ]
      }
    ]
  }
}