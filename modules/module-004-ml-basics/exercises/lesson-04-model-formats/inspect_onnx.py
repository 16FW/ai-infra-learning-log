
import onnx

model = onnx.load("tiny.onnx")

# ONNX 그래프 유효성 검사
onnx.checker.check_model(model)

graph = model.graph

print("=== Nodes ===")
print("Node count:", len(graph.node))

for node in graph.node:
    print(
        f"Op: {node.op_type}, "
        f"Name: {node.name}, "
        f"Inputs: {list(node.input)}, "
        f"Outputs: {list(node.output)}"
    )


def print_value_info(title, values):
    print(f"\n=== {title} ===")

    for value in values:
        shape = []

        for dim in value.type.tensor_type.shape.dim:
            if dim.dim_param:
                shape.append(dim.dim_param)
            else:
                shape.append(dim.dim_value)

        print(
            f"Name: {value.name}, "
            f"Shape: {shape}, "
            f"Type: {value.type.tensor_type.elem_type}"
        )


print_value_info("Inputs", graph.input)
print_value_info("Outputs", graph.output)

print("\n=== Opset ===")
for opset in model.opset_import:
    print("Domain:", opset.domain, "Version:", opset.version)
