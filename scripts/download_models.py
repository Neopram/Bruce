"""Download LLM models for Bruce AI.
Usage: python scripts/download_models.py [--model phi3|deepseek|tinyllama|all] [--quantized] [--api-only]
"""

import argparse
import json
import os
import sys
from pathlib import Path

MODELS = {
    "phi3": {
        "repo_id": "microsoft/Phi-3-mini-4k-instruct",
        "display_name": "Phi-3 Mini 4K Instruct",
        "quantized_repo": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "description": "Microsoft Phi-3 Mini -- compact yet powerful reasoning model",
    },
    "deepseek": {
        "repo_id": "deepseek-ai/deepseek-coder-1.3b-base",
        "display_name": "DeepSeek Coder 1.3B Base",
        "quantized_repo": "TheBloke/deepseek-coder-1.3b-base-GPTQ",
        "description": "DeepSeek Coder -- optimized for code generation tasks",
    },
    "tinyllama": {
        "repo_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "display_name": "TinyLlama 1.1B Chat v1.0",
        "quantized_repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GPTQ",
        "description": "TinyLlama -- lightweight chat model for fast inference",
    },
}

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


def ensure_huggingface_hub():
    """Check that huggingface_hub is installed."""
    try:
        import huggingface_hub  # noqa: F401
        return True
    except ImportError:
        print("[ERROR] huggingface_hub is not installed.")
        print("  Install it with:  pip install huggingface_hub")
        return False


def download_model(model_key: str, quantized: bool = False) -> bool:
    """Download a single model using huggingface_hub.snapshot_download().

    Returns True on success, False on failure (fallback config is written).
    """
    from huggingface_hub import snapshot_download

    info = MODELS[model_key]
    repo = info["quantized_repo"] if quantized else info["repo_id"]
    tag = " (quantized)" if quantized else ""
    dest = MODELS_DIR / model_key

    print(f"\n{'='*60}")
    print(f"Downloading {info['display_name']}{tag}")
    print(f"  Repo : {repo}")
    print(f"  Dest : {dest}")
    print(f"{'='*60}\n")

    dest.mkdir(parents=True, exist_ok=True)

    try:
        snapshot_download(
            repo_id=repo,
            local_dir=str(dest),
            local_dir_use_symlinks=False,
        )
        print(f"\n[OK] {info['display_name']} downloaded successfully.")
        if verify_model(dest, model_key):
            print(f"[OK] Verification passed for {model_key}.")
            return True
        else:
            print(f"[WARN] Verification issues for {model_key} -- model may still work.")
            return True
    except Exception as exc:
        print(f"\n[ERROR] Download failed for {repo}: {exc}")
        write_fallback_config(dest, model_key, str(exc))
        return False


def verify_model(model_dir: Path, model_key: str) -> bool:
    """Run basic verification on a downloaded model directory."""
    config_path = model_dir / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            arch = cfg.get("architectures", cfg.get("model_type", "unknown"))
            print(f"  Model architecture: {arch}")
            return True
        except json.JSONDecodeError:
            print("  [WARN] config.json exists but is not valid JSON.")
            return False

    # Some quantized repos may not have config.json -- check for weight files
    weight_exts = {".bin", ".safetensors", ".gguf", ".ggml"}
    weights = [f for f in model_dir.iterdir() if f.suffix in weight_exts]
    if weights:
        print(f"  Found {len(weights)} weight file(s).")
        return True

    print("  [WARN] No config.json or weight files found.")
    return False


def write_fallback_config(model_dir: Path, model_key: str, error_msg: str):
    """Write a fallback config.json telling the system to use API instead."""
    model_dir.mkdir(parents=True, exist_ok=True)
    fallback = {
        "bruce_ai_fallback": True,
        "model": model_key,
        "source": "api",
        "reason": f"Local download failed: {error_msg}",
        "instructions": "Use OpenAI or Anthropic API as a fallback for this model.",
        "api_options": [
            {"provider": "openai", "model": "gpt-4o-mini"},
            {"provider": "anthropic", "model": "claude-3-haiku-20240307"},
        ],
    }
    path = model_dir / "config.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fallback, f, indent=2)
    print(f"[FALLBACK] Wrote API-fallback config to {path}")


def create_api_only_config():
    """Create configs for all models pointing to API providers."""
    print("\n[API-ONLY] Creating API-fallback configurations for all models ...\n")
    for key, info in MODELS.items():
        dest = MODELS_DIR / key
        dest.mkdir(parents=True, exist_ok=True)
        config = {
            "bruce_ai_fallback": True,
            "model": key,
            "display_name": info["display_name"],
            "source": "api",
            "reason": "User chose --api-only mode; no local weights downloaded.",
            "instructions": "Use OpenAI or Anthropic API as a fallback for this model.",
            "api_options": [
                {"provider": "openai", "model": "gpt-4o-mini"},
                {"provider": "anthropic", "model": "claude-3-haiku-20240307"},
            ],
        }
        path = dest / "config.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"  [OK] {info['display_name']} -> {path}")

    print("\n[DONE] All models configured for API-only mode.")


def main():
    parser = argparse.ArgumentParser(
        description="Download LLM models for Bruce AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/download_models.py --model phi3
  python scripts/download_models.py --model all --quantized
  python scripts/download_models.py --api-only
        """,
    )
    parser.add_argument(
        "--model",
        choices=["phi3", "deepseek", "tinyllama", "all"],
        default="all",
        help="Which model to download (default: all)",
    )
    parser.add_argument(
        "--quantized",
        action="store_true",
        help="Download quantized (GPTQ/GGUF) variant if available",
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Skip downloads; create config files that point to OpenAI/Anthropic APIs",
    )

    args = parser.parse_args()

    # --api-only takes precedence
    if args.api_only:
        create_api_only_config()
        return

    if not ensure_huggingface_hub():
        sys.exit(1)

    targets = list(MODELS.keys()) if args.model == "all" else [args.model]

    results = {}
    for key in targets:
        success = download_model(key, quantized=args.quantized)
        results[key] = "OK" if success else "FALLBACK (API)"

    # Print summary
    print(f"\n{'='*60}")
    print("Download Summary")
    print(f"{'='*60}")
    for key, status in results.items():
        print(f"  {MODELS[key]['display_name']:40s} {status}")
    print(f"{'='*60}")
    print(f"Models directory: {MODELS_DIR}")


if __name__ == "__main__":
    main()
