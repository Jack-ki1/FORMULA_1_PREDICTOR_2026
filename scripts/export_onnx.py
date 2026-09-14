"""
Export ML model to ONNX for minimal Python deployment.
Per 2026 research: pickle is tied to Python version, ONNX runs on any runtime (CPU/GPU/WASM),
cuts cold-start and enables browser inference. For F1 Predictor, XGBoost/LightGBM can be exported.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def export_xgboost_to_onnx():
    """Example: export XGBoost model to ONNX (requires ` skl2onnx` + `onnxruntime`)."""
    try:
        import xgboost as xgb
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
        import pickle

        # Load existing model if exists (example path)
        model_path = "cache/model_cache/xgboost_model.pkl"
        if not os.path.exists(model_path):
            print(f"[ONNX] No model at {model_path} — train first via backend/app/engine/ml_models.py")
            print("[ONNX] Skipping export (demo). To enable:")
            print("  pip install skl2onnx onnxruntime")
            print("  python scripts/export_onnx.py")
            return

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        initial_type = [("float_input", FloatTensorType([None, 20]))]
        onnx_model = convert_sklearn(model, initial_types=initial_type)
        out_path = "cache/model_cache/xgboost_model.onnx"
        with open(out_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"[ONNX] Exported {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")
        print("[ONNX] Runtime test: import onnxruntime; sess = onnxruntime.InferenceSession(out_path)")

    except ImportError as e:
        print(f"[ONNX] Missing deps: {e}")
        print("  pip install skl2onnx onnx onnxruntime")
    except Exception as e:
        print(f"[ONNX] Export failed: {e}")

if __name__ == "__main__":
    export_xgboost_to_onnx()
