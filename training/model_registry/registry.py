"""
Model Registry — versioned artifacts + metadata + champion/challenger.
"""
import os, json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

REGISTRY_PATH = "training/model_registry/registry.json"

def load_registry() -> Dict[str, Any]:
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {"models": {}, "champion": None}

def save_registry(reg: Dict[str, Any]):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2)

def register_model(model_id: str, version: str, algorithm: str, metrics: Dict[str, float], training_cutoff: str = "", feature_version: str = "feature-v8", dataset_version: str = "dataset-v14"):
    reg = load_registry()
    key = f"{model_id}-v{version}"
    reg["models"][key] = {
        "model_id": model_id,
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_cutoff": training_cutoff,
        "feature_version": feature_version,
        "dataset_version": dataset_version,
        "algorithm": algorithm,
        "metrics": metrics,
        "status": "candidate",
    }
    save_registry(reg)
    return reg["models"][key]

def promote_champion(model_key: str):
    reg = load_registry()
    if model_key not in reg["models"]:
        raise ValueError(f"Unknown model {model_key}")
    # demote previous
    for k, v in reg["models"].items():
        if v.get("status") == "champion":
            v["status"] = "archived"
    reg["models"][model_key]["status"] = "champion"
    reg["champion"] = model_key
    save_registry(reg)
    return reg["models"][model_key]
