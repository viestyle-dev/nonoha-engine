window.BENCHMARK_DATA = {
  "lastUpdate": 1795013451563,
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
        "date": 1795013451119,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 1033.4925716737978,
            "unit": "iter/sec",
            "range": "stddev: 0.00006822720863500287",
            "extra": "mean: 967.5928278617865 usec\nrounds: 1127"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 104.68519149846846,
            "unit": "iter/sec",
            "range": "stddev: 0.00025930118899112877",
            "extra": "mean: 9.552449450451931 msec\nrounds: 111"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 976.4262276077098,
            "unit": "iter/sec",
            "range": "stddev: 0.0000737069846018332",
            "extra": "mean: 1.0241429119023635 msec\nrounds: 1067"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 889.1079261289927,
            "unit": "iter/sec",
            "range": "stddev: 0.00008275027842562735",
            "extra": "mean: 1.1247228492876116 msec\nrounds: 982"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 876.9342082518293,
            "unit": "iter/sec",
            "range": "stddev: 0.00012486189501517003",
            "extra": "mean: 1.1403364021954425 msec\nrounds: 1002"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 911.3265284305174,
            "unit": "iter/sec",
            "range": "stddev: 0.00006671093421770973",
            "extra": "mean: 1.0973015366097105 msec\nrounds: 997"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 130.1550087585557,
            "unit": "iter/sec",
            "range": "stddev: 0.0001986957462705524",
            "extra": "mean: 7.683146499994109 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 836.9802204340716,
            "unit": "iter/sec",
            "range": "stddev: 0.00003339161751357845",
            "extra": "mean: 1.194771364467112 msec\nrounds: 985"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 444538.0858042483,
            "unit": "iter/sec",
            "range": "stddev: 2.858322458937981e-7",
            "extra": "mean: 2.2495260404759705 usec\nrounds: 46301"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 166717.39255465995,
            "unit": "iter/sec",
            "range": "stddev: 9.397615994297904e-7",
            "extra": "mean: 5.9981744236561285 usec\nrounds: 176679"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 150103.9972310069,
            "unit": "iter/sec",
            "range": "stddev: 9.44579026772527e-7",
            "extra": "mean: 6.662047769860658 usec\nrounds: 159745"
          }
        ]
      }
    ]
  }
}