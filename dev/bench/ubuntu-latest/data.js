window.BENCHMARK_DATA = {
  "lastUpdate": 1795151713391,
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
          "id": "8cba8a5e19d64c30eec8eaf87628375508fc8be7",
          "message": "Merge pull request #2 from viestyle-dev/feature/inspector-tuning\n\nfix: update subproject commit reference in nonoha-core",
          "timestamp": "2026-11-19T13:38:10+09:00",
          "tree_id": "42b7e553dba291b31d16e0f37b10273bfc0183da",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/8cba8a5e19d64c30eec8eaf87628375508fc8be7"
        },
        "date": 1795063143480,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 975.0052208568262,
            "unit": "iter/sec",
            "range": "stddev: 0.00007638541267017319",
            "extra": "mean: 1.025635533644844 msec\nrounds: 1070"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 117.63645138288634,
            "unit": "iter/sec",
            "range": "stddev: 0.00043826209971503617",
            "extra": "mean: 8.500766456692686 msec\nrounds: 127"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 946.2349764114878,
            "unit": "iter/sec",
            "range": "stddev: 0.00008916747191101127",
            "extra": "mean: 1.056819949514455 msec\nrounds: 1030"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 850.5568003036332,
            "unit": "iter/sec",
            "range": "stddev: 0.0001320492017079816",
            "extra": "mean: 1.1757004348716258 msec\nrounds: 975"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 866.0436995873445,
            "unit": "iter/sec",
            "range": "stddev: 0.00009757922892581409",
            "extra": "mean: 1.1546761444907265 msec\nrounds: 962"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 878.737730949883,
            "unit": "iter/sec",
            "range": "stddev: 0.00008510145656572315",
            "extra": "mean: 1.1379959739739829 msec\nrounds: 999"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 159.9677530604814,
            "unit": "iter/sec",
            "range": "stddev: 0.00023447061186021963",
            "extra": "mean: 6.2512598999994395 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 853.7037717625745,
            "unit": "iter/sec",
            "range": "stddev: 0.000034234596090088115",
            "extra": "mean: 1.1713665009765382 msec\nrounds: 1024"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 516352.9208696932,
            "unit": "iter/sec",
            "range": "stddev: 2.0293641478984775e-7",
            "extra": "mean: 1.936659907560303 usec\nrounds: 54307"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 179037.958940215,
            "unit": "iter/sec",
            "range": "stddev: 8.795178546348732e-7",
            "extra": "mean: 5.585407730960133 usec\nrounds: 194025"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 166653.11467293723,
            "unit": "iter/sec",
            "range": "stddev: 0.000001152204600092154",
            "extra": "mean: 6.000487911447297 usec\nrounds: 188112"
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
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "distinct": true,
          "id": "b7ab88d2e3b286b08f7eb335baf9881a75654797",
          "message": "fix: update version 1.1.0 and enhance README for clarity",
          "timestamp": "2026-11-20T02:57:15+09:00",
          "tree_id": "840b5a5db0fa7a8176d45d97c5b54e4aff4df95e",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/b7ab88d2e3b286b08f7eb335baf9881a75654797"
        },
        "date": 1795111092580,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 854.6259878011621,
            "unit": "iter/sec",
            "range": "stddev: 0.00013178600381869287",
            "extra": "mean: 1.170102494276901 msec\nrounds: 961"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 100.09280135638363,
            "unit": "iter/sec",
            "range": "stddev: 0.0011026321819664479",
            "extra": "mean: 9.990728468468655 msec\nrounds: 111"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 863.2090456361907,
            "unit": "iter/sec",
            "range": "stddev: 0.00008375649227749907",
            "extra": "mean: 1.1584679343379602 msec\nrounds: 929"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 805.6645216054461,
            "unit": "iter/sec",
            "range": "stddev: 0.00008316641193422922",
            "extra": "mean: 1.241211413911217 msec\nrounds: 877"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 806.3990221506424,
            "unit": "iter/sec",
            "range": "stddev: 0.00008998591875999954",
            "extra": "mean: 1.2400808688148326 msec\nrounds: 869"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 821.9675524832514,
            "unit": "iter/sec",
            "range": "stddev: 0.00009589100683481029",
            "extra": "mean: 1.2165930357942885 msec\nrounds: 894"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 136.7588545341079,
            "unit": "iter/sec",
            "range": "stddev: 0.00026073745851105083",
            "extra": "mean: 7.312140799999156 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 739.1667695862504,
            "unit": "iter/sec",
            "range": "stddev: 0.000176932266107374",
            "extra": "mean: 1.3528746707048958 msec\nrounds: 908"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 388067.86498636845,
            "unit": "iter/sec",
            "range": "stddev: 3.4858505904542023e-7",
            "extra": "mean: 2.5768688681170575 usec\nrounds: 134699"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 174407.62497373245,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011921724972238766",
            "extra": "mean: 5.733694270251143 usec\nrounds: 184843"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 136870.6087323075,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011642378324274222",
            "extra": "mean: 7.306170471966023 usec\nrounds: 144886"
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
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "distinct": true,
          "id": "ddff59b10649a63cca4824bbab2feed05f50de4b",
          "message": "fix: update version to 1.2.0 and enhance property declaration guidelines in documentation",
          "timestamp": "2026-11-20T14:14:13+09:00",
          "tree_id": "beb68c6839f56f85589b0359a4826e2b561561e4",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/ddff59b10649a63cca4824bbab2feed05f50de4b"
        },
        "date": 1795151712781,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 1908.58737374518,
            "unit": "iter/sec",
            "range": "stddev: 0.00003285678735876456",
            "extra": "mean: 523.947718483394 usec\nrounds: 2110"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 181.53688414492225,
            "unit": "iter/sec",
            "range": "stddev: 0.0003175209584050996",
            "extra": "mean: 5.508522440000085 msec\nrounds: 200"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 1790.2874229795138,
            "unit": "iter/sec",
            "range": "stddev: 0.00006279563816890067",
            "extra": "mean: 558.5695275319168 usec\nrounds: 2034"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 1651.8880360349985,
            "unit": "iter/sec",
            "range": "stddev: 0.00008763613011755326",
            "extra": "mean: 605.3679052003334 usec\nrounds: 1846"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 1619.0335864798567,
            "unit": "iter/sec",
            "range": "stddev: 0.00007635960229225188",
            "extra": "mean: 617.6524121245841 usec\nrounds: 1798"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 1663.6381573176668,
            "unit": "iter/sec",
            "range": "stddev: 0.00007417308365188915",
            "extra": "mean: 601.0922480957817 usec\nrounds: 1838"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 246.71494730158926,
            "unit": "iter/sec",
            "range": "stddev: 0.0002575724314576151",
            "extra": "mean: 4.0532606999995835 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1350.0812551447355,
            "unit": "iter/sec",
            "range": "stddev: 0.0000732151375592577",
            "extra": "mean: 740.6961589825162 usec\nrounds: 1887"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 718732.7398498405,
            "unit": "iter/sec",
            "range": "stddev: 1.2702590210516851e-7",
            "extra": "mean: 1.3913377595804515 usec\nrounds: 77048"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 315595.18572375743,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024825274358923",
            "extra": "mean: 3.1686161425646926 usec\nrounds: 186637"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 258308.42043438365,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010525454008038089",
            "extra": "mean: 3.8713410825646055 usec\nrounds: 140057"
          }
        ]
      }
    ]
  }
}