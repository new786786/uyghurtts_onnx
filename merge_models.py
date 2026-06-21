"""克隆仓库后运行此脚本，自动合并所有模型分片为原始文件"""
import os
import glob

BASE = os.path.dirname(os.path.abspath(__file__))

MERGE_MAP = [
    ("model_parts/vec-768-layer-12.onnx.part*", "vec-768-layer-12.onnx"),
    ("model_parts/22k_hawagul.onnx.part*", "22k_hawagul.onnx"),
    ("clone_onnx/model_parts/1.onnx.part*", "clone_onnx/1.onnx"),
    ("clone_onnx/model_parts/added_1_onnx_v2.index.part*", "clone_onnx/added_1_onnx_v2.index"),
    ("clone_onnx/model_parts/2.onnx.part*", "clone_onnx/2.onnx"),
    ("clone_onnx/model_parts/added_2_onnx_v2.index.part*", "clone_onnx/added_2_onnx_v2.index"),
    ("tts_onnx/model_parts/model.onnx.part*", "tts_onnx/model.onnx"),
    ("tts_onnx/model_parts/hawahan.onnx.part*", "tts_onnx/hawahan.onnx"),
    ("tts_onnx/model_parts/xjsdn.onnx.part*", "tts_onnx/xjsdn.onnx"),
]

for pattern, target in MERGE_MAP:
    parts = sorted(glob.glob(os.path.join(BASE, pattern)))
    if not parts:
        print(f"SKIP: {pattern} (no parts found)")
        continue
    out = os.path.join(BASE, target)
    total = 0
    with open(out, "wb") as f:
        for p in parts:
            data = open(p, "rb").read()
            f.write(data)
            total += len(data)
    print(f"Merged {len(parts)} parts -> {target} ({total / 1024 / 1024:.1f} MB)")

print("\nAll models merged. Ready to use.")
