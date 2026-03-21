"""
Bruce AI — Brain Installer

Installs the LLM brain for Bruce. Tries multiple approaches:
1. Ollama + Mistral 7B (best local option)
2. OpenAI API configuration (best quality, needs API key)
3. Anthropic API configuration (alternative)
4. HuggingFace local model (fallback)

Usage:
  python scripts/install_brain.py              # Auto-detect best option
  python scripts/install_brain.py --ollama     # Force Ollama install
  python scripts/install_brain.py --openai     # Configure OpenAI API
  python scripts/install_brain.py --anthropic  # Configure Anthropic API
  python scripts/install_brain.py --check      # Check what's available
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_FILE = Path("data/brain_config.json")
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)


def check_ollama():
    """Check if Ollama is installed and running."""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return {"installed": True, "version": result.stdout.strip()}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check common paths on Windows
    for path in [
        os.path.expanduser("~/AppData/Local/Programs/Ollama/ollama.exe"),
        "C:/Program Files/Ollama/ollama.exe",
        "C:/ProgramData/chocolatey/bin/ollama.exe",
    ]:
        if os.path.exists(path):
            return {"installed": True, "path": path}

    return {"installed": False}


def check_ollama_running():
    """Check if Ollama server is running."""
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return {"running": True, "models": models}
    except Exception:
        pass
    return {"running": False, "models": []}


def check_openai():
    """Check if OpenAI API key is configured."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        try:
            import requests
            r = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            if r.status_code == 200:
                return {"available": True, "key_set": True}
        except Exception:
            pass
        return {"available": False, "key_set": True, "note": "Key set but API unreachable"}
    return {"available": False, "key_set": False}


def check_anthropic():
    """Check if Anthropic API key is configured."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return {"available": bool(key), "key_set": bool(key)}


def install_ollama():
    """Guide Ollama installation."""
    print("\n=== Installing Ollama ===\n")

    setup_path = os.path.expanduser("~/Downloads/OllamaSetup.exe")
    if os.path.exists(setup_path):
        print(f"  Ollama installer found at: {setup_path}")
        print(f"  Size: {os.path.getsize(setup_path) / 1024 / 1024:.0f} MB")
        print()
        print("  To install:")
        print(f"  1. Double-click: {setup_path}")
        print("  2. Wait 30 seconds for installation")
        print("  3. Open a NEW terminal and run: ollama pull mistral")
        print("  4. Then run: python scripts/install_brain.py --check")
    else:
        print("  Download Ollama from: https://ollama.com/download")
        print("  Or run: curl -L -o ~/Downloads/OllamaSetup.exe https://ollama.com/download/OllamaSetup.exe")

    print()
    print("  After Ollama is installed and running:")
    print("  ollama pull mistral          # Download Mistral 7B (~4.1GB)")
    print("  ollama pull qwen2.5:7b       # Alternative: Qwen 2.5 7B")
    print("  ollama pull deepseek-r1:8b   # Alternative: DeepSeek R1 8B")


def configure_openai():
    """Configure OpenAI API."""
    print("\n=== Configuring OpenAI API ===\n")

    key = input("  Enter your OpenAI API key (sk-...): ").strip()
    if not key.startswith("sk-"):
        print("  Invalid key format. Should start with 'sk-'")
        return False

    # Save to .env
    env_path = Path(".env")
    env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    if "OPENAI_API_KEY" not in env_content:
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"\nOPENAI_API_KEY={key}\n")
        print("  Added OPENAI_API_KEY to .env")
    else:
        lines = env_content.split("\n")
        lines = [f"OPENAI_API_KEY={key}" if l.startswith("OPENAI_API_KEY") else l for l in lines]
        env_path.write_text("\n".join(lines), encoding="utf-8")
        print("  Updated OPENAI_API_KEY in .env")

    save_config({"provider": "openai", "model": "gpt-4o-mini", "api_key_set": True})
    print("  Brain configured: OpenAI GPT-4o-mini")
    print("  Estimated cost: ~$0.15/M input tokens, ~$0.60/M output tokens")
    return True


def configure_anthropic():
    """Configure Anthropic API."""
    print("\n=== Configuring Anthropic API ===\n")

    key = input("  Enter your Anthropic API key (sk-ant-...): ").strip()
    if not key.startswith("sk-ant-"):
        print("  Invalid key format. Should start with 'sk-ant-'")
        return False

    env_path = Path(".env")
    env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    if "ANTHROPIC_API_KEY" not in env_content:
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"\nANTHROPIC_API_KEY={key}\n")
        print("  Added ANTHROPIC_API_KEY to .env")

    save_config({"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "api_key_set": True})
    print("  Brain configured: Anthropic Claude 3.5 Sonnet")
    return True


def save_config(config: dict):
    """Save brain configuration."""
    config["configured_at"] = str(Path.cwd())
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def check_all():
    """Check all available brain options."""
    print("\n" + "=" * 60)
    print("  Bruce AI — Brain Status Check")
    print("=" * 60)

    # Ollama
    ollama = check_ollama()
    ollama_running = check_ollama_running()
    if ollama_running["running"]:
        models = ollama_running["models"]
        print(f"\n  [LIVE] Ollama: Running with {len(models)} model(s)")
        for m in models:
            print(f"         - {m}")
        if any("mistral" in m for m in models):
            save_config({"provider": "ollama", "model": "mistral", "status": "ready"})
            print("\n  >>> BRAIN READY: Ollama + Mistral <<<")
        else:
            print("\n  Run: ollama pull mistral")
    elif ollama["installed"]:
        print(f"\n  [OK  ] Ollama: Installed but not running")
        print("         Start it with: ollama serve")
    else:
        print(f"\n  [MISS] Ollama: Not installed")
        print("         Install from: https://ollama.com/download")

    # OpenAI
    openai = check_openai()
    if openai.get("available"):
        print(f"\n  [LIVE] OpenAI: API connected")
        save_config({"provider": "openai", "model": "gpt-4o-mini", "status": "ready"})
    elif openai.get("key_set"):
        print(f"\n  [WARN] OpenAI: Key set but API unreachable")
    else:
        print(f"\n  [MISS] OpenAI: No API key (set OPENAI_API_KEY)")

    # Anthropic
    anthropic = check_anthropic()
    if anthropic.get("available"):
        print(f"\n  [OK  ] Anthropic: API key configured")
    else:
        print(f"\n  [MISS] Anthropic: No API key (set ANTHROPIC_API_KEY)")

    # Current config
    if CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        print(f"\n  Current brain config: {config.get('provider', 'none')} / {config.get('model', 'none')}")
    else:
        print(f"\n  No brain configured yet.")

    print("\n" + "=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bruce AI Brain Installer")
    parser.add_argument("--ollama", action="store_true", help="Install/configure Ollama")
    parser.add_argument("--openai", action="store_true", help="Configure OpenAI API")
    parser.add_argument("--anthropic", action="store_true", help="Configure Anthropic API")
    parser.add_argument("--check", action="store_true", help="Check available brains")
    args = parser.parse_args()

    if args.check or not any([args.ollama, args.openai, args.anthropic]):
        check_all()
        if not any([args.ollama, args.openai, args.anthropic, args.check]):
            print("\n  Options:")
            print("  python scripts/install_brain.py --ollama     # Local LLM (free, private)")
            print("  python scripts/install_brain.py --openai     # OpenAI API (best quality)")
            print("  python scripts/install_brain.py --anthropic  # Anthropic API (alternative)")
            print()

    if args.ollama:
        install_ollama()
    if args.openai:
        configure_openai()
    if args.anthropic:
        configure_anthropic()


if __name__ == "__main__":
    main()
