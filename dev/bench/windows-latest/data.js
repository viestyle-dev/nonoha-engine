window.BENCHMARK_DATA = {
  "lastUpdate": 1794065156283,
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
          "id": "e2c954a5d2f2b12236cf1c4990c38d28e48577d3",
          "message": "publish",
          "timestamp": "2026-11-07T23:53:32+09:00",
          "tree_id": "2af8f13cbe59ae4d73d7e3949a7544649b200136",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/e2c954a5d2f2b12236cf1c4990c38d28e48577d3"
        },
        "date": 1794065154237,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 457.23501672016397,
            "unit": "iter/sec",
            "range": "stddev: 0.00011653261527203836",
            "extra": "mean: 2.1870590909095178 msec\nrounds: 506"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 83.88215887223367,
            "unit": "iter/sec",
            "range": "stddev: 0.0005778355198045712",
            "extra": "mean: 11.921486206896088 msec\nrounds: 87"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 369.29289243665295,
            "unit": "iter/sec",
            "range": "stddev: 0.0006500729861106585",
            "extra": "mean: 2.7078777319591554 msec\nrounds: 485"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 373.46641186473653,
            "unit": "iter/sec",
            "range": "stddev: 0.0004156207824865228",
            "extra": "mean: 2.677616964285891 msec\nrounds: 448"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 363.13097565033195,
            "unit": "iter/sec",
            "range": "stddev: 0.0002398091459199861",
            "extra": "mean: 2.753827315912938 msec\nrounds: 421"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 391.4748829715421,
            "unit": "iter/sec",
            "range": "stddev: 0.00017440314625346122",
            "extra": "mean: 2.5544422988503555 msec\nrounds: 435"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 98.28859891577008,
            "unit": "iter/sec",
            "range": "stddev: 0.0015829785699354644",
            "extra": "mean: 10.174119999990694 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 738.254977124746,
            "unit": "iter/sec",
            "range": "stddev: 0.00008363709955238302",
            "extra": "mean: 1.354545558087075 msec\nrounds: 878"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 289868.78443071496,
            "unit": "iter/sec",
            "range": "stddev: 0.000001135271021973583",
            "extra": "mean: 3.449836801033752 usec\nrounds: 156251"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 78084.254985936,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033079610334710006",
            "extra": "mean: 12.806679146520805 usec\nrounds: 83334"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 84622.18257273125,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037567544521137922",
            "extra": "mean: 11.81723242768547 usec\nrounds: 90910"
          }
        ]
      }
    ]
  }
}