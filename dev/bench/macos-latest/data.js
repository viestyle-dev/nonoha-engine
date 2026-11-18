window.BENCHMARK_DATA = {
  "lastUpdate": 1795013540164,
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
      },
      {
        "commit": {
          "author": {
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "06039ad2bfa1bb769cf6310478738298f4ecc937",
          "message": "feat: inspector (#1)\n\n* feat: inspector\n\n* feat: update version to 1.1.0.dev0 and add custom views for plugins\n\n* Implement environment value management and request guarding\n\n- Add a new catalog module for node definitions in JSON format.\n- Enhance the router to include endpoints for managing environment values.\n- Introduce RequestGuard middleware to reject requests from foreign origins and rebound hosts.\n- Update runtime configuration to support additional environment settings.\n- Create tests for environment value parsing, writing, and request guarding functionality.\n- Document the handling of environment values and access restrictions in AGENTS.md.\n\n* feat: update AGENTS.md and node.py for output dispatch handling and documentation improvements\n\n* feat: update AGENTS.md and nodes.py to clarify time input types for Clock node\n\n* feat: update user-nodes plugin manifest and spectrum-bars view\n\n- Added \"delivery\": \"latest\" to the manifest.json for user-nodes to specify that only the latest spectrum is drawn.\n- Introduced a minimum value of 0 for the max setting in the spectrum-bars view to ensure valid input.\n- Updated comments in spectrum-bars.js for clarity on how the view interacts with the host and handles settings.\n- Modified the test setup in test_inspector_ws.py to reflect the new schema version in the manifest.json.\n\n* feat: enhance output value fetching logic to handle empty responses\n\n* Add comprehensive tests for graph endpoint, environment settings, and plugin host\n\n- Introduced tests for the graph endpoint to ensure proper message handling and error logging.\n- Enhanced environment settings tests to cover various platform-specific directory resolutions and file writing behaviors.\n- Added tests for the PluginHost to verify static file serving from plugins and handling of built-in plugins.\n- Updated file reading methods across tests to ensure UTF-8 encoding is consistently applied.\n- Improved request guard tests to validate behavior with loopback addresses and non-web origins.\n- Bumped version for nonoha-core and nonoha-engine to 1.1.0.dev0 in lock file.\n\n* feat: enhance inspector and outbox functionality, improve documentation, and update tests\n\n* feat: improve Outbox message handling and add test for unreadable control frames\n\n* chore: update subproject commit reference in nonoha-core\n\n* feat: update macOS target to macos-15 for Apple Silicon compatibility",
          "timestamp": "2026-11-18T23:49:58+09:00",
          "tree_id": "55299b758d2d9647798a9971be504b6b111fb953",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/06039ad2bfa1bb769cf6310478738298f4ecc937"
        },
        "date": 1795013539118,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 539.5785208183119,
            "unit": "iter/sec",
            "range": "stddev: 0.0015792728368256021",
            "extra": "mean: 1.8532983827514558 msec\nrounds: 1403"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 88.46854147697064,
            "unit": "iter/sec",
            "range": "stddev: 0.00403235662624145",
            "extra": "mean: 11.303452993630636 msec\nrounds: 157"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 567.8284139607464,
            "unit": "iter/sec",
            "range": "stddev: 0.0011265621740782553",
            "extra": "mean: 1.7610953862360421 msec\nrounds: 1424"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 687.8756538026711,
            "unit": "iter/sec",
            "range": "stddev: 0.000699827033401371",
            "extra": "mean: 1.4537511168942565 msec\nrounds: 1172"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 977.2178287516847,
            "unit": "iter/sec",
            "range": "stddev: 0.00018043884297943945",
            "extra": "mean: 1.023313298814265 msec\nrounds: 1265"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 389.91069041124206,
            "unit": "iter/sec",
            "range": "stddev: 0.0014958842403289807",
            "extra": "mean: 2.5646898753796457 msec\nrounds: 1316"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 156.81959572510078,
            "unit": "iter/sec",
            "range": "stddev: 0.0022554531333993265",
            "extra": "mean: 6.376754099997584 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1177.6222595939944,
            "unit": "iter/sec",
            "range": "stddev: 0.0005273589289433886",
            "extra": "mean: 849.1687311895473 usec\nrounds: 1648"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 498429.46895517135,
            "unit": "iter/sec",
            "range": "stddev: 0.0000043844134029017445",
            "extra": "mean: 2.0063019188978197 usec\nrounds: 78691"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 99801.58655792894,
            "unit": "iter/sec",
            "range": "stddev: 0.00005252485066121965",
            "extra": "mean: 10.019880790367585 usec\nrounds: 110096"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 186508.88118499724,
            "unit": "iter/sec",
            "range": "stddev: 0.00001285599914839643",
            "extra": "mean: 5.361674970362966 usec\nrounds: 133334"
          }
        ]
      }
    ]
  }
}