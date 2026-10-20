from nonoha_core.node_registry import NodeRegistry
from .nodes import SynthesizerNode, SpectrumAnalyzerNode


def register_nodes(registry: NodeRegistry):
    """Register all custom nodes with the engine."""
    registry.register_node("Synthesizer", SynthesizerNode)
    registry.register_node("SpectrumAnalyzer", SpectrumAnalyzerNode)
