from collections import OrderedDict
from typing import Iterable

from graph_transpiler.backend.fallback.allocator import MemoryLayout
from graph_transpiler.backend.fallback.kernel import Kernel
from graph_transpiler.backend.interface.graph_descriptor import IGraphDescriptor
from graph_transpiler.graph import traverse
from graph_transpiler.graph.variable import Variable
from graph_transpiler.graph.variables.attributes.constant import Constant
from graph_transpiler.util import json

source_header = """
dnn_fallback_kernel={
"""

source_footer = """
};
"""


class GraphDescriptor(json.SerializableMixin, IGraphDescriptor):
    kernels: Iterable[Kernel]
    constants_layout: MemoryLayout
    variables_layout: MemoryLayout
    inputs: Iterable[Variable]
    outputs: Iterable[Variable]
    constants_encoding: str

    def __init__(self,
                 kernels: Iterable[Kernel],
                 constants_layout: MemoryLayout,
                 variables_layout: MemoryLayout,
                 inputs: Iterable[Variable],
                 outputs: Iterable[Variable],
                 constants_encoding: str):
        self.kernels = kernels
        self.constants_layout = constants_layout
        self.variables_layout = variables_layout
        self.inputs = inputs
        self.outputs = outputs
        self.constants_encoding = constants_encoding

    def concat_kernel_sources(self):
        sources = OrderedDict()
        sources["header"] = source_header

        for kernel in self.kernels:
            for func_name, source in kernel.func_sources.items():
                if func_name in sources:
                    assert sources[func_name] == source
                else:
                    sources[func_name] = source

        sources["footer"] = source_footer
        combined_source = "\n".join(sources.values())

        return combined_source

    def _to_serializable_(self):
        return {
            "kernel_source": self.concat_kernel_sources(),
            "exec_infos": [kernel.exec_info for kernel in self.kernels],
            "weight_allocation": self.constants_layout,
            "weight_encoding": self.constants_encoding,
            "variable_allocation": self.variables_layout,
            "inputs": [v.parameters["name"] for v in self.inputs if not traverse.check_attribute_match(v, Constant)],
            "outputs": [v.parameters["name"] for v in self.outputs]
        }