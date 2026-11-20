window.BENCHMARK_DATA = {
  "lastUpdate": 1795182342208,
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
        "date": 1795063224312,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 696.7406793213311,
            "unit": "iter/sec",
            "range": "stddev: 0.0019080488678107522",
            "extra": "mean: 1.4352542196532323 msec\nrounds: 1557"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 118.48518773938585,
            "unit": "iter/sec",
            "range": "stddev: 0.007648925008718765",
            "extra": "mean: 8.439873532542737 msec\nrounds: 169"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 631.0079060828012,
            "unit": "iter/sec",
            "range": "stddev: 0.0015790718643431012",
            "extra": "mean: 1.5847661976342644 msec\nrounds: 1437"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 548.1615175820376,
            "unit": "iter/sec",
            "range": "stddev: 0.0007571412912710914",
            "extra": "mean: 1.8242798298046166 msec\nrounds: 1228"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 664.5190239843328,
            "unit": "iter/sec",
            "range": "stddev: 0.0016146956752022832",
            "extra": "mean: 1.5048478130907157 msec\nrounds: 1482"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 688.2767925824817,
            "unit": "iter/sec",
            "range": "stddev: 0.0010358215423327583",
            "extra": "mean: 1.4529038473720761 msec\nrounds: 1389"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 213.85113364961998,
            "unit": "iter/sec",
            "range": "stddev: 0.0005490417854715752",
            "extra": "mean: 4.676150099996335 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1248.0433190610784,
            "unit": "iter/sec",
            "range": "stddev: 0.00024476508361379165",
            "extra": "mean: 801.2542391175291 usec\nrounds: 1631"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 663309.5980250579,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019527795664402474",
            "extra": "mean: 1.5075916328926735 usec\nrounds: 78952"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 84362.86661460806,
            "unit": "iter/sec",
            "range": "stddev: 0.00009797013369740264",
            "extra": "mean: 11.853556429848041 usec\nrounds: 114824"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 190466.14560633196,
            "unit": "iter/sec",
            "range": "stddev: 0.00001954766836010002",
            "extra": "mean: 5.250276876326705 usec\nrounds: 142858"
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
        "date": 1795111196005,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 454.90864289943545,
            "unit": "iter/sec",
            "range": "stddev: 0.0011051063008931106",
            "extra": "mean: 2.198243571778137 msec\nrounds: 1226"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 81.3298804626504,
            "unit": "iter/sec",
            "range": "stddev: 0.004003375349882619",
            "extra": "mean: 12.295603956521685 msec\nrounds: 161"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 388.04674942507717,
            "unit": "iter/sec",
            "range": "stddev: 0.0012117288287432503",
            "extra": "mean: 2.577009088419324 msec\nrounds: 1278"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 445.68825386905115,
            "unit": "iter/sec",
            "range": "stddev: 0.0010712139872529915",
            "extra": "mean: 2.243720787610913 msec\nrounds: 1130"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 586.9058372154794,
            "unit": "iter/sec",
            "range": "stddev: 0.0007359680906763877",
            "extra": "mean: 1.7038508336267495 msec\nrounds: 1136"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 510.05189515706786,
            "unit": "iter/sec",
            "range": "stddev: 0.0015060052306466397",
            "extra": "mean: 1.9605848140061415 msec\nrounds: 1328"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 119.3668771287812,
            "unit": "iter/sec",
            "range": "stddev: 0.0029357585495200307",
            "extra": "mean: 8.377533399999493 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 759.1130297739035,
            "unit": "iter/sec",
            "range": "stddev: 0.0008580287186651723",
            "extra": "mean: 1.3173268812127266 msec\nrounds: 1549"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 356961.6998624276,
            "unit": "iter/sec",
            "range": "stddev: 0.0000070405793877415814",
            "extra": "mean: 2.8014209938640464 usec\nrounds: 78180"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 79694.63931166641,
            "unit": "iter/sec",
            "range": "stddev: 0.00003365454238691491",
            "extra": "mean: 12.547895424800688 usec\nrounds: 105264"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 148236.7443321237,
            "unit": "iter/sec",
            "range": "stddev: 0.000011418426329913341",
            "extra": "mean: 6.745965748947541 usec\nrounds: 132609"
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
        "date": 1795151772601,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 896.1192503196563,
            "unit": "iter/sec",
            "range": "stddev: 0.0002924345694787103",
            "extra": "mean: 1.1159229082996356 msec\nrounds: 1494"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 134.57509262347165,
            "unit": "iter/sec",
            "range": "stddev: 0.00323803415537681",
            "extra": "mean: 7.430795554404003 msec\nrounds: 193"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 919.6155540252624,
            "unit": "iter/sec",
            "range": "stddev: 0.00025052882959216387",
            "extra": "mean: 1.0874109247314114 msec\nrounds: 1674"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 944.3381577654005,
            "unit": "iter/sec",
            "range": "stddev: 0.00038920238804758577",
            "extra": "mean: 1.0589427015914645 msec\nrounds: 1508"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 1123.8544139883575,
            "unit": "iter/sec",
            "range": "stddev: 0.00010716205800832728",
            "extra": "mean: 889.794965925506 usec\nrounds: 1350"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 1013.8213021758884,
            "unit": "iter/sec",
            "range": "stddev: 0.00027636045218348474",
            "extra": "mean: 986.3671219511518 usec\nrounds: 1394"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 257.6793802154094,
            "unit": "iter/sec",
            "range": "stddev: 0.00046122481958840467",
            "extra": "mean: 3.8807916999957115 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1672.5407721663046,
            "unit": "iter/sec",
            "range": "stddev: 0.00003658640342307925",
            "extra": "mean: 597.8927489491226 usec\nrounds: 1904"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 871541.651880089,
            "unit": "iter/sec",
            "range": "stddev: 1.799075354369117e-7",
            "extra": "mean: 1.147392092899754 usec\nrounds: 94118"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 131785.74603727637,
            "unit": "iter/sec",
            "range": "stddev: 0.000026930608113417713",
            "extra": "mean: 7.58807405253937 usec\nrounds: 110084"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 271909.60822512675,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020523441859765247",
            "extra": "mean: 3.677692769032468 usec\nrounds: 157904"
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
          "id": "81410c92cc8f6bda860074c73e263b12ade9f1ed",
          "message": "fix: update version to 1.2.1 and adjust waypoint position description in documentation",
          "timestamp": "2026-11-20T22:43:20+09:00",
          "tree_id": "e80f2416c2f60b99cbb4910b46f55a63cbd4b205",
          "url": "https://github.com/viestyle-dev/nonoha-engine/commit/81410c92cc8f6bda860074c73e263b12ade9f1ed"
        },
        "date": 1795182340617,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 719.193843509133,
            "unit": "iter/sec",
            "range": "stddev: 0.001443411774528361",
            "extra": "mean: 1.390445717834209 msec\nrounds: 1570"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 130.62492249735004,
            "unit": "iter/sec",
            "range": "stddev: 0.001151957711019518",
            "extra": "mean: 7.655506934523056 msec\nrounds: 168"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 747.6784577781689,
            "unit": "iter/sec",
            "range": "stddev: 0.0006741199534096847",
            "extra": "mean: 1.3374733344219116 msec\nrounds: 1531"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 755.3264342035912,
            "unit": "iter/sec",
            "range": "stddev: 0.00071507925864755",
            "extra": "mean: 1.3239308922828714 msec\nrounds: 1244"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 921.5643310872175,
            "unit": "iter/sec",
            "range": "stddev: 0.0007351389817276466",
            "extra": "mean: 1.085111441781007 msec\nrounds: 1460"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 1009.590701585538,
            "unit": "iter/sec",
            "range": "stddev: 0.0003939102597069894",
            "extra": "mean: 990.5004061839358 usec\nrounds: 1423"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 142.22929803494733,
            "unit": "iter/sec",
            "range": "stddev: 0.0043150226085082585",
            "extra": "mean: 7.030900200001611 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1247.308400500415,
            "unit": "iter/sec",
            "range": "stddev: 0.0006774157731860836",
            "extra": "mean: 801.7263409745369 usec\nrounds: 1745"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 656680.6162769883,
            "unit": "iter/sec",
            "range": "stddev: 6.797830785406633e-7",
            "extra": "mean: 1.5228102904413992 usec\nrounds: 78432"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 96356.0861065629,
            "unit": "iter/sec",
            "range": "stddev: 0.0000187735221604845",
            "extra": "mean: 10.378171638209464 usec\nrounds: 109087"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 146816.2357232053,
            "unit": "iter/sec",
            "range": "stddev: 0.000013368577041176496",
            "extra": "mean: 6.81123579469313 usec\nrounds: 132609"
          }
        ]
      }
    ]
  }
}