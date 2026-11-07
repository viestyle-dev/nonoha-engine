import asyncio
import threading
import time
from contextlib import contextmanager
from unittest.mock import MagicMock

import numpy as np
import openpyxl

from nonoha_engine.node_flow.nodes.record_nodes import (
    RecordingStatus,
    RecordNode,
    ReplayFileLoadingStatus,
    ReplayNode,
    RotatingRecordNode,
)


@contextmanager
def background_event_loop():
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    try:
        yield loop
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join()


def setup_parent_graph(node, data_dir):
    mock_persist = MagicMock()
    mock_persist.data_dir_path = data_dir
    mock_graph = MagicMock()
    mock_graph.persist = mock_persist
    node.parent_graph = mock_graph


def activate_node(node, loop):
    node._main_loop = loop
    node._activated.set()


# -- RecordNode --


class TestRecordNodeConstruction:
    def test_ports(self):
        node = RecordNode("test")
        assert "values" in node.inputs
        assert "start" in node.inputs
        assert "stop" in node.inputs
        assert "preamble" in node.inputs
        assert "recording_status" in node.outputs

    def test_initial_state(self):
        node = RecordNode("test")
        assert node._recording_status == RecordingStatus.STOPPED


class TestRecordNodeLifecycle:
    def test_start_record_stop(self, tmp_path):
        node = RecordNode("test")
        file_path = tmp_path / "test.csv"

        with background_event_loop() as loop:
            activate_node(node, loop)

            # Start recording (absolute path)
            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            assert node._recording_status == RecordingStatus.RECORDING

            # Send values
            node.inputs["values"].dispatch(
                [np.array([1.0], dtype=np.float32), np.array([2.0], dtype=np.float32)]
            )
            time.sleep(0.2)

            # Stop
            node.inputs["stop"].dispatch([np.array([0])])

            # Wait for worker to finish
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)

            # Let call_soon_threadsafe callbacks run
            time.sleep(0.2)

        assert file_path.exists()
        lines = file_path.read_text().strip().split("\n")
        assert lines[0] == "header1,header2"
        assert len(lines) >= 2

    def test_empty_headers_no_header_row(self, tmp_path):
        node = RecordNode("test")
        node.set_properties({"headers": "", "allow_overwrite": True})
        file_path = tmp_path / "no_header.csv"

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            node.inputs["values"].dispatch(
                [np.array([1.0], dtype=np.float32), np.array([2.0], dtype=np.float32)]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        lines = file_path.read_text().strip().split("\n")
        # No header row — first line is data
        assert "header" not in lines[0]
        assert len(lines) >= 1

    def test_recording_status_transitions(self, tmp_path):
        node = RecordNode("test")
        file_path = tmp_path / "status_test.csv"

        with background_event_loop() as loop:
            activate_node(node, loop)

            assert node._recording_status == RecordingStatus.STOPPED

            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            assert node._recording_status == RecordingStatus.RECORDING

            node.inputs["stop"].dispatch([np.array([0])])
            assert node._recording_status == RecordingStatus.STOPPING

            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)


class TestRecordNodeActivation:
    def test_worker_waits_for_activation(self, tmp_path):
        node = RecordNode("test")
        node.set_properties({"allow_overwrite": True})
        file_path = tmp_path / "wait_test.csv"

        # Start before activation
        node.inputs["start"].dispatch(
            [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
        )

        # Worker thread should be running but blocked
        assert node._save_worker_thread is not None
        assert node._save_worker_thread.is_alive()
        time.sleep(0.1)
        assert not file_path.exists()

        # Now activate
        with background_event_loop() as loop:
            activate_node(node, loop)
            time.sleep(0.3)

            # Worker should have proceeded — file created
            assert file_path.exists()

            # Cleanup
            node._quit_save.set()
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)

    def test_finalize_before_activation(self, tmp_path):
        node = RecordNode("test")
        file_path = tmp_path / "finalize_test.csv"

        # Start before activation
        node.inputs["start"].dispatch(
            [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
        )
        assert node._save_worker_thread is not None
        assert node._save_worker_thread.is_alive()

        # Finalize without activating — should not hang
        node.finalize()
        assert not node._save_worker_thread.is_alive()


class TestRecordNodePreamble:
    def _run_session(self, node, file_path, preamble=None):
        with background_event_loop() as loop:
            activate_node(node, loop)

            if preamble is not None:
                node.inputs["preamble"].dispatch(
                    [np.array([preamble], dtype=np.dtypes.StringDType())]
                )
            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            node.inputs["values"].dispatch(
                [np.array([1.0], dtype=np.float32), np.array([2.0], dtype=np.float32)]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

    def test_preamble_written_before_header(self, tmp_path):
        node = RecordNode("test")
        file_path = tmp_path / "preamble.csv"

        self._run_session(
            node, file_path, preamble="session_id: sX\ndata_use_consent: true"
        )

        lines = file_path.read_text().strip().split("\n")
        assert lines[0] == "# session_id: sX"
        assert lines[1] == "# data_use_consent: true"
        assert lines[2] == "header1,header2"
        assert len(lines) >= 4

    def test_preamble_keeps_existing_hash_and_skips_blank_lines(self, tmp_path):
        node = RecordNode("test")
        file_path = tmp_path / "hash.csv"

        self._run_session(node, file_path, preamble="# already commented\n\nplain")

        lines = file_path.read_text().strip().split("\n")
        assert lines[0] == "# already commented"
        assert lines[1] == "# plain"
        assert lines[2] == "header1,header2"

    def test_empty_preamble_output_unchanged(self, tmp_path):
        node = RecordNode("test")
        file_path = tmp_path / "no_preamble.csv"

        self._run_session(node, file_path, preamble=None)

        lines = file_path.read_text().strip().split("\n")
        assert lines[0] == "header1,header2"

    def test_preamble_in_text_format(self, tmp_path):
        node = RecordNode("test")
        node.set_properties({
            "headers": "msg",
            "value_type_list": "str",
            "format": "text",
            "allow_overwrite": True,
        })
        file_path = tmp_path / "preamble.txt"

        with background_event_loop() as loop:
            activate_node(node, loop)
            node.inputs["preamble"].dispatch(
                [np.array(["meta: x"], dtype=np.dtypes.StringDType())]
            )
            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            node.inputs["values"].dispatch(
                [np.array(["hello"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        lines = file_path.read_text().strip().split("\n")
        assert lines[0] == "# meta: x"
        assert lines[1] == "msg"
        assert lines[2] == "hello"

    def test_preambled_csv_readable_by_replay(self, tmp_path):
        """End-to-end: a preambled recording loads through ReplayNode's
        comment="#" path with the metadata lines transparently skipped."""
        node = RecordNode("test")
        node.set_properties({"headers": "col1,col2", "allow_overwrite": True})
        file_path = tmp_path / "roundtrip.csv"

        self._run_session(node, file_path, preamble="session_id: sX")

        replay = make_replay_node(tmp_path, "roundtrip.csv", "f32,f32")
        with background_event_loop() as loop:
            replay._main_loop = loop
            load_replay_file(replay, loop)

        assert replay._df is not None
        values = replay._get_values_from_df(0, 1)
        np.testing.assert_allclose(values[0], [1.0])
        np.testing.assert_allclose(values[1], [2.0])


# -- RotatingRecordNode --


class TestRotatingRecordNodeConstruction:
    def test_ports(self):
        node = RotatingRecordNode("test")
        assert "values" in node.inputs
        assert "start" in node.inputs
        assert "stop" in node.inputs
        assert "recording_status" in node.outputs
        assert "current_file" in node.outputs

    def test_default_properties(self):
        node = RotatingRecordNode("test")
        assert node.properties["max_file_size_kb"] == 1024
        assert node.properties["max_file_count"] == 10
        assert node.properties["file_name"] == "output.log"


class TestRotatingRecordNodeLifecycle:
    def test_start_record_stop(self, tmp_path):
        node = RotatingRecordNode("test")
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch([np.array([1])])
            assert node._recording_status == RecordingStatus.RECORDING
            time.sleep(0.2)

            # Send string values
            node.inputs["values"].dispatch(
                [np.array(["hello", "world"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)

            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        log_file = data_dir / "output.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "hello" in content

    def test_append_on_restart(self, tmp_path):
        """start/stop/start should append to the same file, not create a new one."""
        node = RotatingRecordNode("test")
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            # First session
            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.1)
            node.inputs["values"].dispatch(
                [np.array(["first"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.1)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

            # Second session
            node._recording_status = RecordingStatus.STOPPED
            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.1)
            node.inputs["values"].dispatch(
                [np.array(["second"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.1)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        log_file = data_dir / "output.log"
        content = log_file.read_text()
        assert "first" in content
        assert "second" in content
        # Only one output.log file, no date-stamped copies
        all_log = [f for f in data_dir.iterdir() if f.suffix == ".log"]
        assert len(all_log) == 1

    def test_empty_headers_no_header_row(self, tmp_path):
        node = RotatingRecordNode("test")
        node.set_properties({"headers": ""})
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.1)
            node.inputs["values"].dispatch(
                [np.array(["hello"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        log_file = data_dir / "output.log"
        lines = log_file.read_text().strip().split("\n")
        assert lines[0] == "hello"

    def test_rotation(self, tmp_path):
        node = RotatingRecordNode("test")
        node.set_properties({"max_file_size_kb": 1, "max_file_count": 10})
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.2)

            # Send enough data to exceed 1KB
            long_line = "x" * 200
            for _ in range(20):
                node.inputs["values"].dispatch(
                    [np.array([long_line], dtype=np.dtypes.StringDType())]
                )
                time.sleep(0.05)

            time.sleep(0.5)

            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)

        # Current file + at least one backup
        assert (data_dir / "output.log").exists()
        assert (data_dir / "output.log.1").exists()

    def test_cleanup(self, tmp_path):
        node = RotatingRecordNode("test")
        node.set_properties({
            "max_file_size_kb": 1,
            "max_file_count": 2,
        })
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.2)

            # Send enough data to trigger multiple rotations
            long_line = "x" * 200
            for _ in range(30):
                node.inputs["values"].dispatch(
                    [np.array([long_line], dtype=np.dtypes.StringDType())]
                )
                time.sleep(0.05)

            time.sleep(0.5)

            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)

        # max_file_count=2: output.log + output.log.1
        all_log_files = [f for f in data_dir.iterdir() if f.name.startswith("output.log")]
        assert len(all_log_files) <= 2

    def test_multi_column_recording(self, tmp_path):
        """Test recording multiple PortValue columns (like RecordNode)."""
        node = RotatingRecordNode("test")
        node.set_properties({
            "headers": "x,y",
            "value_type_list": "f32,f32",
            "format": "csv",
        })
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.2)

            node.inputs["values"].dispatch(
                [np.array([1.5], dtype=np.float32), np.array([2.5], dtype=np.float32)]
            )
            time.sleep(0.2)

            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        log_file = data_dir / "output.log"
        lines = log_file.read_text().strip().split("\n")
        assert lines[0] == "x,y"
        assert len(lines) >= 2


class TestRotatingRecordNodeActivation:
    def test_worker_waits_for_activation(self, tmp_path):
        node = RotatingRecordNode("test")
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        # Start before activation
        node.inputs["start"].dispatch([np.array([1])])

        assert node._save_worker_thread is not None
        assert node._save_worker_thread.is_alive()
        time.sleep(0.1)
        assert not data_dir.exists() or len(list(data_dir.iterdir())) == 0

        # Now activate
        with background_event_loop() as loop:
            activate_node(node, loop)
            time.sleep(0.3)

            assert data_dir.exists()
            assert (data_dir / "output.log").exists()

            node._quit_save.set()
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)

    def test_finalize_before_activation(self, tmp_path):
        node = RotatingRecordNode("test")
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        node.inputs["start"].dispatch([np.array([1])])
        assert node._save_worker_thread is not None
        assert node._save_worker_thread.is_alive()

        # Finalize without activating — should not hang
        node.finalize()
        assert not node._save_worker_thread.is_alive()


class TestRecordNodeFormat:
    def test_csv_format_escapes_commas(self, tmp_path):
        node = RecordNode("test")
        node.set_properties({
            "headers": "message",
            "value_type_list": "str",
            "format": "csv",
            "allow_overwrite": True,
        })
        file_path = tmp_path / "escape_test.csv"

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            node.inputs["values"].dispatch(
                [np.array(["hello, world"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        content = file_path.read_text()
        assert "message" in content
        assert '"hello, world"' in content

    def test_csv_format_escapes_quotes(self, tmp_path):
        node = RecordNode("test")
        node.set_properties({
            "headers": "msg",
            "value_type_list": "str",
            "format": "csv",
            "allow_overwrite": True,
        })
        file_path = tmp_path / "quote_test.csv"

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            node.inputs["values"].dispatch(
                [np.array(['say "hi"'], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        content = file_path.read_text()
        assert '"say ""hi"""' in content

    def test_text_format_single_column(self, tmp_path):
        node = RecordNode("test")
        node.set_properties({
            "headers": "",
            "value_type_list": "str",
            "format": "text",
            "allow_overwrite": True,
        })
        file_path = tmp_path / "text_test.txt"

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch(
                [np.array([str(file_path)], dtype=np.dtypes.StringDType())]
            )
            node.inputs["values"].dispatch(
                [np.array(["hello, world"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        content = file_path.read_text().strip()
        # No quoting in text mode — raw value
        assert content == "hello, world"

    def test_text_format_rejects_multi_column(self):
        node = RecordNode("test")
        try:
            node.set_properties({
                "value_type_list": "f32,f32",
                "format": "text",
            })
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "single column" in str(e).lower() or "1 column" in str(e).lower()


class TestRotatingRecordNodeFormat:
    def test_csv_format_escapes_commas(self, tmp_path):
        node = RotatingRecordNode("test")
        node.set_properties({
            "headers": "message",
            "value_type_list": "str",
            "format": "csv",
        })
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.2)
            node.inputs["values"].dispatch(
                [np.array(["hello, world"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        content = (data_dir / "output.log").read_text()
        assert "message" in content
        assert '"hello, world"' in content

    def test_text_format_single_column(self, tmp_path):
        node = RotatingRecordNode("test")
        node.set_properties({
            "headers": "",
            "value_type_list": "str",
            "format": "text",
        })
        data_dir = tmp_path / "data"
        setup_parent_graph(node, data_dir)

        with background_event_loop() as loop:
            activate_node(node, loop)

            node.inputs["start"].dispatch([np.array([1])])
            time.sleep(0.2)
            node.inputs["values"].dispatch(
                [np.array(["hello, world"], dtype=np.dtypes.StringDType())]
            )
            time.sleep(0.2)
            node.inputs["stop"].dispatch([np.array([0])])
            if node._save_worker_thread is not None:
                node._save_worker_thread.join(timeout=2)
            time.sleep(0.2)

        content = (data_dir / "output.log").read_text().strip()
        assert content == "hello, world"

    def test_text_format_rejects_multi_column(self):
        node = RotatingRecordNode("test")
        try:
            node.set_properties({
                "value_type_list": "f32,f32",
                "format": "text",
            })
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "single column" in str(e).lower() or "1 column" in str(e).lower()


class TestRotateFiles:
    def test_cascade_rename(self, tmp_path):
        """log.csv -> log.csv.1, log.csv.1 -> log.csv.2, etc."""
        (tmp_path / "log.csv").write_text("current")
        (tmp_path / "log.csv.1").write_text("backup1")
        (tmp_path / "log.csv.2").write_text("backup2")

        RotatingRecordNode._rotate_files(tmp_path, "log.csv", max_count=5)

        assert not (tmp_path / "log.csv").exists()
        assert (tmp_path / "log.csv.1").read_text() == "current"
        assert (tmp_path / "log.csv.2").read_text() == "backup1"
        assert (tmp_path / "log.csv.3").read_text() == "backup2"

    def test_deletes_oldest_at_limit(self, tmp_path):
        """With max_count=3: log.csv + log.csv.1 + log.csv.2 max. Oldest deleted."""
        (tmp_path / "log.csv").write_text("current")
        (tmp_path / "log.csv.1").write_text("backup1")
        (tmp_path / "log.csv.2").write_text("backup2")

        RotatingRecordNode._rotate_files(tmp_path, "log.csv", max_count=3)

        # .2 was at limit (max_count-1=2), so deleted
        # .1 -> .2, current -> .1
        assert not (tmp_path / "log.csv").exists()
        assert (tmp_path / "log.csv.1").read_text() == "current"
        assert (tmp_path / "log.csv.2").read_text() == "backup1"
        assert not (tmp_path / "log.csv.3").exists()

    def test_no_files_exist(self, tmp_path):
        """Rotation with no existing files should not error."""
        RotatingRecordNode._rotate_files(tmp_path, "log.csv", max_count=5)
        assert len(list(tmp_path.iterdir())) == 0


# -- ReplayNode --


def make_replay_node(tmp_path, file_name, value_type_list):
    node = ReplayNode("test")
    setup_parent_graph(node, tmp_path)
    node.set_properties({"value_type_list": value_type_list, "file_name": file_name})
    return node


def load_replay_file(node, loop, timeout=5.0):
    # _on_input_load uses asyncio.create_task, so it must run in the loop thread
    loop.call_soon_threadsafe(node._on_input_load, [np.array([1])])
    deadline = time.time() + timeout
    while node._file_loading_status != ReplayFileLoadingStatus.LOADED:
        assert time.time() < deadline, "file load timed out"
        time.sleep(0.01)


class TestReplayNodeCommentHandling:
    def test_csv_comment_lines_skipped(self, tmp_path):
        (tmp_path / "data.csv").write_text(
            "# recorded metadata\ncol1,col2\n1.0,2.0\n# midway comment\n3.0,4.0\n"
        )
        node = make_replay_node(tmp_path, "data.csv", "f32,f32")

        with background_event_loop() as loop:
            node._main_loop = loop
            load_replay_file(node, loop)

        assert node._df is not None
        assert node._df.shape == (2, 2)
        values = node._get_values_from_df(0, 2)
        np.testing.assert_allclose(values[0], [1.0, 3.0])
        np.testing.assert_allclose(values[1], [2.0, 4.0])

    def test_csv_without_comments(self, tmp_path):
        (tmp_path / "data.csv").write_text("col1,col2\n1.0,2.0\n3.0,4.0\n5.0,6.0\n")
        node = make_replay_node(tmp_path, "data.csv", "f32,f32")

        with background_event_loop() as loop:
            node._main_loop = loop
            load_replay_file(node, loop)

        assert node._df is not None
        assert node._df.shape == (3, 2)
        values = node._get_values_from_df(0, 3)
        np.testing.assert_allclose(values[0], [1.0, 3.0, 5.0])
        np.testing.assert_allclose(values[1], [2.0, 4.0, 6.0])

    def test_csv_int_columns_with_comments(self, tmp_path):
        (tmp_path / "data.csv").write_text("col1,col2\n1,2\n# comment\n3,4\n")
        node = make_replay_node(tmp_path, "data.csv", "i32,i32")

        with background_event_loop() as loop:
            node._main_loop = loop
            load_replay_file(node, loop)

        values = node._get_values_from_df(0, 2)
        assert values[0].dtype == np.int32
        np.testing.assert_array_equal(values[0], [1, 3])
        np.testing.assert_array_equal(values[1], [2, 4])

    def test_xlsx_comment_row_skipped(self, tmp_path):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["col1", "col2"])
        ws.append([1.0, 2.0])
        ws.append(["# comment", None])
        ws.append([3.0, 4.0])
        wb.save(tmp_path / "data.xlsx")
        node = make_replay_node(tmp_path, "data.xlsx", "f32,f32")

        with background_event_loop() as loop:
            node._main_loop = loop
            load_replay_file(node, loop)

        assert node._df is not None
        assert node._df.shape == (2, 2)
        values = node._get_values_from_df(0, 2)
        np.testing.assert_allclose(values[0], [1.0, 3.0])
        np.testing.assert_allclose(values[1], [2.0, 4.0])

    def test_clock_replays_past_comment_line(self, tmp_path):
        (tmp_path / "data.csv").write_text(
            "col1,col2\n1.0,10.0\n2.0,20.0\n# midway comment\n3.0,30.0\n4.0,40.0\n"
        )
        node = make_replay_node(tmp_path, "data.csv", "f32,f32")
        dispatched = []
        node._output_values.subscribe(
            id(dispatched), lambda values: dispatched.append(values)
        )

        with background_event_loop() as loop:
            node._main_loop = loop
            load_replay_file(node, loop)

            node._on_input_clock([np.array([0.0, 0.0])])
            node._on_input_clock([np.array([0.0, 0.0])])

        assert node._stream_position == 4
        col1 = np.concatenate([values[0] for values in dispatched])
        col2 = np.concatenate([values[1] for values in dispatched])
        np.testing.assert_allclose(col1, [1.0, 2.0, 3.0, 4.0])
        np.testing.assert_allclose(col2, [10.0, 20.0, 30.0, 40.0])
