import os
import sys
import platform
import psutil


def get_device_info():
    """Gather comprehensive system information including GPU, CPU, RAM, disk, and Python details."""
    info = {}

    # CPU details
    info["cpu_count_physical"] = psutil.cpu_count(logical=False)
    info["cpu_count_logical"] = psutil.cpu_count(logical=True)
    info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
    try:
        freq = psutil.cpu_freq()
        if freq:
            info["cpu_freq_current_mhz"] = round(freq.current, 1)
            info["cpu_freq_max_mhz"] = round(freq.max, 1) if freq.max else None
    except Exception:
        info["cpu_freq_current_mhz"] = None
        info["cpu_freq_max_mhz"] = None

    # RAM details
    mem = psutil.virtual_memory()
    info["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
    info["ram_available_gb"] = round(mem.available / (1024 ** 3), 2)
    info["ram_used_gb"] = round(mem.used / (1024 ** 3), 2)
    info["ram_percent"] = mem.percent

    # Disk usage
    try:
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        info["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
        info["disk_used_gb"] = round(disk.used / (1024 ** 3), 2)
        info["disk_free_gb"] = round(disk.free / (1024 ** 3), 2)
        info["disk_percent"] = disk.percent
    except Exception:
        info["disk_total_gb"] = None
        info["disk_percent"] = None

    # GPU details
    gpu_info = _detect_gpu()
    info["gpu_available"] = gpu_info["available"]
    info["gpu_name"] = gpu_info.get("name")
    info["gpu_vram_mb"] = gpu_info.get("vram_mb")

    # Python version
    info["python_version"] = sys.version
    info["platform"] = platform.platform()
    info["architecture"] = platform.machine()

    # Model files check
    info["model_files"] = _check_model_files()

    return info


def _detect_gpu():
    """Attempt to detect GPU information."""
    # Try NVIDIA via pynvml
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode("utf-8")
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram_mb = round(mem_info.total / (1024 ** 2))
        pynvml.nvmlShutdown()
        return {"available": True, "name": name, "vram_mb": vram_mb}
    except Exception:
        pass

    # Try PyTorch CUDA
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram_mb = round(torch.cuda.get_device_properties(0).total_mem / (1024 ** 2))
            return {"available": True, "name": name, "vram_mb": vram_mb}
    except Exception:
        pass

    return {"available": False, "name": None, "vram_mb": None}


def _check_model_files():
    """Check for common model files in the project directory."""
    model_extensions = (".pt", ".pth", ".onnx", ".bin", ".h5", ".pkl", ".safetensors")
    model_dirs = ["models", "checkpoints", "weights", ".", "app/models"]
    found = []
    base = os.path.dirname(os.path.abspath(__file__))

    for mdir in model_dirs:
        full_dir = os.path.join(base, mdir)
        if os.path.isdir(full_dir):
            for fname in os.listdir(full_dir):
                if any(fname.endswith(ext) for ext in model_extensions):
                    size_mb = round(os.path.getsize(os.path.join(full_dir, fname)) / (1024 ** 2), 2)
                    found.append({"file": os.path.join(mdir, fname), "size_mb": size_mb})

    return found if found else "No model files found"
