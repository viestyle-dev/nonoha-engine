"""Custom nodes for the nonoha-engine template workspace.

These nodes demonstrate the core motivation for user_nodes: instead of wiring
15+ basic nodes into a complex graph, write one powerful custom node that
encapsulates domain-specific logic monolithically.

Synthesizer — Replaces ~15 basic nodes (WaveGenerator × N harmonics + Add + Multiply...)
SpectrumAnalyzer — Replaces ~10 basic nodes (Fft + array slicing + Sum × 3 bands...)

Both are used in app.vng alongside built-in nodes (Clock, EmaFilter) to create
an interactive signal lab demo.
"""

import math
import numpy as np
from nonoha_core.node import BaseNode, NodeDoc
from nonoha_core.port import StaticTypeInputPort, StaticTypeOutputPort
from nonoha_core.data_type import DataType, PortValueType, PropertyDataType


class SynthesizerNode(BaseNode):
    """Multi-harmonic waveform synthesizer.

    Generates complex waveforms by summing a fundamental frequency with
    configurable harmonics. Supports sine, square, sawtooth, and triangle waves.

    Without this node, you'd need:
    - 1 WaveGenerator per harmonic (up to 8)
    - 8 Multiply nodes for amplitude scaling (1/n decay)
    - 7 Add nodes to mix harmonics
    - Additional nodes for wave type selection and normalization
    Total: ~15+ basic nodes replaced by this single node.

    Input ports:
        time    — Time array from Clock node (f32)
        frequency — Base frequency from app (f32, default 440)
        harmonics — Number of harmonics from app (f32, default 4)
        waveform_type — Wave shape: 0=sine, 1=square, 2=saw, 3=triangle (f32)

    Output ports:
        waveform — Generated waveform samples (f32)
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Multi-harmonic waveform synthesizer (sine/square/saw/triangle)",
            category="Custom",
            inputs={
                "time": "Time array from Clock",
                "frequency": "Base frequency (Hz)",
                "harmonics": "Number of harmonics",
                "waveform_type": "0=sine 1=square 2=saw 3=tri",
            },
            outputs={"waveform": "Generated waveform"},
        )

    PROPERTIES = {
        "frequency": {"description": "Base frequency in Hz", "data_type": "f64", "default_value": 440.0},
        "harmonics": {"description": "Number of harmonics (1-8)", "data_type": "i32", "default_value": 4},
        "waveform_type": {"description": "0=sine 1=square 2=saw 3=triangle", "data_type": "i32", "default_value": 0},
    }

    def __init__(self, name: str):
        super().__init__(name, "Synthesizer")

        f32 = PortValueType(DataType.Float32)

        # Input: time values from Clock node
        self._in_time = StaticTypeInputPort("time", [f32])
        self._in_time.subscribe(id(self), self._on_time)
        self.inputs[self._in_time.name] = self._in_time

        # Input: control parameters from app (via graph input ports)
        self._in_freq = StaticTypeInputPort("frequency", [f32])
        self._in_freq.subscribe(id(self), self._on_frequency)
        self.inputs[self._in_freq.name] = self._in_freq

        self._in_harmonics = StaticTypeInputPort("harmonics", [f32])
        self._in_harmonics.subscribe(id(self), self._on_harmonics)
        self.inputs[self._in_harmonics.name] = self._in_harmonics

        self._in_wave_type = StaticTypeInputPort("waveform_type", [f32])
        self._in_wave_type.subscribe(id(self), self._on_wave_type)
        self.inputs[self._in_wave_type.name] = self._in_wave_type

        # Output: synthesized waveform
        self._out_waveform = StaticTypeOutputPort("waveform", [f32])
        self.outputs[self._out_waveform.name] = self._out_waveform

        # Internal state for live parameter updates from app
        self._freq = 440.0
        self._n_harmonics = 4
        self._wave_type = 0

    def _on_frequency(self, values: list[np.ndarray]):
        """Update frequency from app slider (graph input port)."""
        self._freq = float(values[0][0])

    def _on_harmonics(self, values: list[np.ndarray]):
        """Update harmonic count from app slider."""
        self._n_harmonics = max(1, min(8, int(values[0][0])))

    def _on_wave_type(self, values: list[np.ndarray]):
        """Update waveform type from app selector."""
        self._wave_type = int(values[0][0]) % 4

    def _on_time(self, values: list[np.ndarray]):
        """Main processing: generate waveform from time array.

        This callback fires every time Clock dispatches a new batch of time values.
        The entire synthesis happens here — fundamental + harmonics + wave shaping.
        """
        t = values[0]  # Time array, e.g., shape (20,) from Clock with pack_size=20
        freq = self._freq
        n_harm = self._n_harmonics
        wave_type = self._wave_type

        # Phase array for fundamental frequency
        # (2π * frequency * time) gives us the phase at each sample
        phase = 2.0 * np.pi * freq * t

        # ── Additive synthesis with harmonics ──
        # Each harmonic n has frequency (n * f0) and amplitude (1/n)
        # This produces rich, natural-sounding timbres
        waveform = np.zeros_like(t, dtype=np.float32)

        for n in range(1, n_harm + 1):
            harmonic_phase = phase * n
            amplitude = 1.0 / n  # Natural harmonic decay

            if wave_type == 0:
                # Sine: pure tone per harmonic
                waveform += amplitude * np.sin(harmonic_phase)
            elif wave_type == 1:
                # Square wave approximation: odd harmonics only
                if n % 2 == 1:
                    waveform += (amplitude * 4.0 / np.pi) * np.sin(harmonic_phase)
            elif wave_type == 2:
                # Sawtooth approximation: all harmonics with alternating sign
                sign = (-1.0) ** (n + 1)
                waveform += sign * (amplitude * 2.0 / np.pi) * np.sin(harmonic_phase)
            elif wave_type == 3:
                # Triangle approximation: odd harmonics with alternating sign
                if n % 2 == 1:
                    k = (n - 1) // 2
                    sign = (-1.0) ** k
                    waveform += sign * (1.0 / (n * n)) * (8.0 / (np.pi * np.pi)) * np.sin(harmonic_phase)

        # Normalize to [-1, 1] range to prevent clipping
        peak = np.max(np.abs(waveform))
        if peak > 0:
            waveform = waveform / peak

        self._out_waveform.dispatch([waveform.astype(np.float32)])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        if "frequency" in properties:
            self._freq = float(properties["frequency"])
            self.properties["frequency"] = self._freq
        if "harmonics" in properties:
            self._n_harmonics = max(1, min(8, int(properties["harmonics"])))
            self.properties["harmonics"] = self._n_harmonics
        if "waveform_type" in properties:
            self._wave_type = int(properties["waveform_type"]) % 4
            self.properties["waveform_type"] = self._wave_type
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)


class SpectrumAnalyzerNode(BaseNode):
    """Real-time FFT spectrum analyzer with frequency band decomposition.

    Performs spectral analysis on incoming signal data, producing a frequency
    spectrum and 3-band energy breakdown (bass/mid/high).

    Without this node, you'd need:
    - Fft node for FFT computation
    - Abs node for magnitude
    - Multiple array slicing nodes for band separation
    - 3 Sum nodes for band energy
    - Additional nodes for log scaling and normalization
    Total: ~10+ basic nodes replaced by this single node.

    Input ports:
        signal — Time-domain signal array (f32)

    Output ports:
        spectrum — Magnitude spectrum (f32, half-spectrum)
        bands   — 3-band energy [bass, mid, high] (f32 × 3 values)
    """

    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="FFT spectrum analyzer with bass/mid/high band decomposition",
            category="Custom",
            inputs={"signal": "Time-domain signal"},
            outputs={
                "spectrum": "Magnitude spectrum",
                "bands": "Band energy: bass, mid, high",
            },
        )

    PROPERTIES = {
        "fft_size": {"description": "FFT window size", "data_type": "i32", "default_value": 256},
        "bass_cutoff": {"description": "Bass/mid boundary (0-1)", "data_type": "f64", "default_value": 0.15},
        "mid_cutoff": {"description": "Mid/high boundary (0-1)", "data_type": "f64", "default_value": 0.5},
    }

    def __init__(self, name: str):
        super().__init__(name, "SpectrumAnalyzer")

        f32 = PortValueType(DataType.Float32)

        # Input: time-domain signal
        self._in_signal = StaticTypeInputPort("signal", [f32])
        self._in_signal.subscribe(id(self), self._on_signal)
        self.inputs[self._in_signal.name] = self._in_signal

        # Output: frequency spectrum (half-spectrum magnitudes)
        self._out_spectrum = StaticTypeOutputPort("spectrum", [f32])
        self.outputs[self._out_spectrum.name] = self._out_spectrum

        # Output: 3-band energy levels [bass, mid, high]
        self._out_bands = StaticTypeOutputPort(
            "bands",
            [f32, f32, f32],
            value_name_list=["bass", "mid", "high"],
        )
        self.outputs[self._out_bands.name] = self._out_bands

        # Accumulation buffer for FFT windowing
        self._buffer = np.array([], dtype=np.float32)
        self._fft_size = 256

    def _on_signal(self, values: list[np.ndarray]):
        """Accumulate samples and run FFT when buffer is full.

        Clock dispatches small batches (e.g., 20 samples at 600Hz).
        We accumulate until we have enough for an FFT window, then analyze.
        """
        signal = values[0].astype(np.float32)
        self._buffer = np.concatenate([self._buffer, signal])

        fft_size = int(self.properties["fft_size"])
        if len(self._buffer) < fft_size:
            return  # Wait for more samples

        # Take the most recent fft_size samples
        window = self._buffer[-fft_size:]
        self._buffer = self._buffer[-fft_size:]  # Keep tail for overlap

        # ── FFT analysis ──
        # Apply Hanning window to reduce spectral leakage
        windowed = window * np.hanning(fft_size).astype(np.float32)

        # Real FFT (output is half-spectrum since input is real)
        fft_result = np.fft.rfft(windowed)
        magnitudes = np.abs(fft_result).astype(np.float32)

        # Convert to decibel-like scale for better visualization
        # Add small epsilon to avoid log(0)
        spectrum_db = 20.0 * np.log10(magnitudes + 1e-10)
        # Normalize to 0-1 range for display
        spec_min = -60.0  # Floor at -60dB
        spec_max = np.max(spectrum_db) if len(spectrum_db) > 0 else 0.0
        spec_range = max(spec_max - spec_min, 1.0)
        spectrum_norm = np.clip((spectrum_db - spec_min) / spec_range, 0.0, 1.0).astype(np.float32)

        self._out_spectrum.dispatch([spectrum_norm])

        # ── 3-band energy decomposition ──
        n_bins = len(magnitudes)
        bass_cutoff = self.properties["bass_cutoff"]
        mid_cutoff = self.properties["mid_cutoff"]

        bass_end = int(n_bins * bass_cutoff)
        mid_end = int(n_bins * mid_cutoff)

        # RMS energy per band, normalized
        total_energy = np.sum(magnitudes ** 2) + 1e-10
        bass = float(np.sqrt(np.sum(magnitudes[:bass_end] ** 2) / total_energy))
        mid = float(np.sqrt(np.sum(magnitudes[bass_end:mid_end] ** 2) / total_energy))
        high = float(np.sqrt(np.sum(magnitudes[mid_end:] ** 2) / total_energy))

        self._out_bands.dispatch([
            np.array([bass], dtype=np.float32),
            np.array([mid], dtype=np.float32),
            np.array([high], dtype=np.float32),
        ])

    def set_properties(self, properties: dict[str, PropertyDataType]):
        if "fft_size" in properties:
            self.properties["fft_size"] = int(properties["fft_size"])
        if "bass_cutoff" in properties:
            self.properties["bass_cutoff"] = float(properties["bass_cutoff"])
        if "mid_cutoff" in properties:
            self.properties["mid_cutoff"] = float(properties["mid_cutoff"])
        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)
