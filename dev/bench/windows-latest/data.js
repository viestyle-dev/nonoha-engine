window.BENCHMARK_DATA = {
  "lastUpdate": 1795151838326,
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
        "date": 1795013613121,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 429.4217434728936,
            "unit": "iter/sec",
            "range": "stddev: 0.00016062186329103307",
            "extra": "mean: 2.3287130081318836 msec\nrounds: 492"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 93.26034674974957,
            "unit": "iter/sec",
            "range": "stddev: 0.0001505597757959921",
            "extra": "mean: 10.722670833332337 msec\nrounds: 96"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 413.5681413110656,
            "unit": "iter/sec",
            "range": "stddev: 0.00012609960651280172",
            "extra": "mean: 2.41798122270702 msec\nrounds: 458"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 386.7807482344157,
            "unit": "iter/sec",
            "range": "stddev: 0.0001835320627339114",
            "extra": "mean: 2.585444090908918 msec\nrounds: 440"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 382.5679858171263,
            "unit": "iter/sec",
            "range": "stddev: 0.00015502661288589856",
            "extra": "mean: 2.613914485981104 msec\nrounds: 428"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 380.89208927130534,
            "unit": "iter/sec",
            "range": "stddev: 0.00014304919059845558",
            "extra": "mean: 2.625415513126372 msec\nrounds: 419"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 112.66856625869971,
            "unit": "iter/sec",
            "range": "stddev: 0.00021278142906091743",
            "extra": "mean: 8.875589999999534 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 686.3057113575071,
            "unit": "iter/sec",
            "range": "stddev: 0.00006899351935332363",
            "extra": "mean: 1.4570766109785218 msec\nrounds: 838"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 332409.7151197378,
            "unit": "iter/sec",
            "range": "stddev: 8.050864337838784e-7",
            "extra": "mean: 3.0083356608268463 usec\nrounds: 175439"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 92217.33561147808,
            "unit": "iter/sec",
            "range": "stddev: 0.000002834119157714169",
            "extra": "mean: 10.843948085998836 usec\nrounds: 99010"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 115699.49900153723,
            "unit": "iter/sec",
            "range": "stddev: 0.000002115492197267768",
            "extra": "mean: 8.643079776747467 usec\nrounds: 123457"
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
        "date": 1795063297276,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 441.0615609213627,
            "unit": "iter/sec",
            "range": "stddev: 0.00013727367498378158",
            "extra": "mean: 2.267257200811229 msec\nrounds: 493"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 94.14052851656095,
            "unit": "iter/sec",
            "range": "stddev: 0.0002613980043334661",
            "extra": "mean: 10.622417525774594 msec\nrounds: 97"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 421.4523336519215,
            "unit": "iter/sec",
            "range": "stddev: 0.00013149635942529567",
            "extra": "mean: 2.3727475687105875 msec\nrounds: 473"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 399.6336028930744,
            "unit": "iter/sec",
            "range": "stddev: 0.00011837161383441928",
            "extra": "mean: 2.502292081448314 msec\nrounds: 442"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 408.6195533844264,
            "unit": "iter/sec",
            "range": "stddev: 0.00017150179355574727",
            "extra": "mean: 2.447264189188732 msec\nrounds: 444"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 419.70344719478834,
            "unit": "iter/sec",
            "range": "stddev: 0.00014220362348289097",
            "extra": "mean: 2.382634707157625 msec\nrounds: 461"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 116.34373523899269,
            "unit": "iter/sec",
            "range": "stddev: 0.00020216680022038823",
            "extra": "mean: 8.59521999999231 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 723.0627827072061,
            "unit": "iter/sec",
            "range": "stddev: 0.00009121872982610365",
            "extra": "mean: 1.383005769230603 msec\nrounds: 884"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 332776.8479200224,
            "unit": "iter/sec",
            "range": "stddev: 9.129718717623277e-7",
            "extra": "mean: 3.005016743954297 usec\nrounds: 178572"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 92053.76400970235,
            "unit": "iter/sec",
            "range": "stddev: 0.000002357583906221696",
            "extra": "mean: 10.86321684678316 usec\nrounds: 99010"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 117295.5392053896,
            "unit": "iter/sec",
            "range": "stddev: 0.000002425500365186156",
            "extra": "mean: 8.52547340482366 usec\nrounds: 126583"
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
        "date": 1795111272922,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 591.4596201257878,
            "unit": "iter/sec",
            "range": "stddev: 0.00008739626856385219",
            "extra": "mean: 1.6907324963068933 msec\nrounds: 677"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 103.73346944645402,
            "unit": "iter/sec",
            "range": "stddev: 0.0004772313722877811",
            "extra": "mean: 9.640090178572384 msec\nrounds: 112"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 549.35569109408,
            "unit": "iter/sec",
            "range": "stddev: 0.0001282542605610793",
            "extra": "mean: 1.8203142630750406 msec\nrounds: 631"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 513.8013794729651,
            "unit": "iter/sec",
            "range": "stddev: 0.00009737706324285244",
            "extra": "mean: 1.946277374781975 msec\nrounds: 579"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 499.6324854060535,
            "unit": "iter/sec",
            "range": "stddev: 0.0001107662132163783",
            "extra": "mean: 2.0014711397064096 msec\nrounds: 544"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 585.9659844575053,
            "unit": "iter/sec",
            "range": "stddev: 0.00010568260859677964",
            "extra": "mean: 1.7065837037039147 msec\nrounds: 540"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 127.22986237558709,
            "unit": "iter/sec",
            "range": "stddev: 0.0002013863310478975",
            "extra": "mean: 7.859789999992017 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 977.6891339621374,
            "unit": "iter/sec",
            "range": "stddev: 0.00004438714485993393",
            "extra": "mean: 1.0228200000008658 msec\nrounds: 1165"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 453794.96282074915,
            "unit": "iter/sec",
            "range": "stddev: 2.8289385658404745e-7",
            "extra": "mean: 2.2036383872225227 usec\nrounds: 47620"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 114237.07686432189,
            "unit": "iter/sec",
            "range": "stddev: 0.000001579174073095968",
            "extra": "mean: 8.753725388016441 usec\nrounds: 119048"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 149242.75738127675,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016386541918701032",
            "extra": "mean: 6.7004926573773895 usec\nrounds: 158731"
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
        "date": 1795151836737,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graphs",
            "value": 880.7064381373981,
            "unit": "iter/sec",
            "range": "stddev: 0.00007012455938229464",
            "extra": "mean: 1.1354521287648303 msec\nrounds: 963"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_catalog_nodes",
            "value": 163.58192363976588,
            "unit": "iter/sec",
            "range": "stddev: 0.0001753187359462442",
            "extra": "mean: 6.113144886363871 msec\nrounds: 176"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_node_list",
            "value": 825.4991138884869,
            "unit": "iter/sec",
            "range": "stddev: 0.00014525447269101097",
            "extra": "mean: 1.2113883384920092 msec\nrounds: 969"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_edges",
            "value": 726.5958264033076,
            "unit": "iter/sec",
            "range": "stddev: 0.00015664283760583159",
            "extra": "mean: 1.376280957943372 msec\nrounds: 856"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_inputs",
            "value": 784.6931834302253,
            "unit": "iter/sec",
            "range": "stddev: 0.00009978738585486818",
            "extra": "mean: 1.27438344198248 msec\nrounds: 767"
          },
          {
            "name": "benchmarks/test_api_throughput.py::test_get_graph_outputs",
            "value": 715.2858722253012,
            "unit": "iter/sec",
            "range": "stddev: 0.00018072670809376085",
            "extra": "mean: 1.3980424314672042 msec\nrounds: 839"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_load_benchmark_vnf",
            "value": 202.7694248037549,
            "unit": "iter/sec",
            "range": "stddev: 0.00020510211249671662",
            "extra": "mean: 4.931710000005296 msec\nrounds: 10"
          },
          {
            "name": "benchmarks/test_graph_operations.py::test_create_100_nodes",
            "value": 1294.87866576146,
            "unit": "iter/sec",
            "range": "stddev: 0.0000483387668993001",
            "extra": "mean: 772.2731298626693 usec\nrounds: 1671"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_small",
            "value": 606501.677547576,
            "unit": "iter/sec",
            "range": "stddev: 1.790442639611807e-7",
            "extra": "mean: 1.648800056157719 usec\nrounds: 64103"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_f32_large",
            "value": 166905.11545369218,
            "unit": "iter/sec",
            "range": "stddev: 9.019970481964033e-7",
            "extra": "mean: 5.991428107411423 usec\nrounds: 178572"
          },
          {
            "name": "benchmarks/test_serialization_roundtrip.py::test_roundtrip_multi_value",
            "value": 204431.23628197747,
            "unit": "iter/sec",
            "range": "stddev: 6.354006764013381e-7",
            "extra": "mean: 4.89162037165726 usec\nrounds: 106383"
          }
        ]
      }
    ]
  }
}