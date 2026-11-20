import json
import os 
import platform
import shutil
import subprocess
import threading
import time
from collections import deque
from contextlib import contextmanager
from pathlib import Path
import psutil


_GB = 1024 ** 3

#friendly limit names -> keys in the flat reading 
LIMIT_KEYS = {
    "cpu":"cpu_percent", 
    "ram":"ram_parcent", 
    "swap":'swap_percent', 
    "disk":"disk_percent", 
    "gpu_util":"gpu_util_max", 
    "gpu_mem":"gpu_mem_percent_max", 
    "gpu_temp":"gpu_temp_max"
}



class ResourceError(Exception):
    """Base class for resource problem"""


class InsufficientResources(ResourceError): 
    """Not enough free RAM, GPU memory or disk."""


def _num(text): 
    try: 
        return float(text)
    except (TypeError, ValueError):
        return None



#GPU Nvidia only
class GPUReader: 
    """Reads NVIDIA GPUs through pynvml (pip install nvidia-ml-py), or the nvidia-smi command as a fallback.
    AMD GPUs and Apple Silicon GPUs are not supported (Apple's memory is shared, so watch RAM there)."""

    def __init__(self): 
        self.source,self._nvml, self.last_error = None, None, None

        try: 
            import pynvml
            pynvml.nvmlInit()
            self._nvml, self.source = pynvml, "pynvml"
        except Exception: 
            if shutil.which("nvidia-smi"): 
                self.source = "nvidia-smi"


    @property
    def available(self): 
        return self.source is not None


    def read(self):
        """List of {"index", "name", "mem_used_gb", "mem_total_gb", "util"?, "temp"?}. [] if none or on error."""
        if not self.source:
            return []

        try: 
            return self._read_nvml() if self.source == "pynvml" else self._read_smi()
        except Exception as e: 
            self.last_error = e
            return []


    def read_nvml(self): 
        nv, gpus = self._nvml, []

        for i in range(nv.nvmlDeviceGetCount()):
            handle = nv.nvmlDeviceGetHandleByIndex(i)
            name = nv.nvmlDeviceGetName(handle)
            mem = nv.nvmlDeviceGetMemoryInfo(handle)
            gpu = {
                "index":i, 
                "name":name.decode() if isinstance(name, bytes) else name, 
                "mem_used_gb":mem.used/_GB, 
                "mem_total_gb":mem.total / _GB
            }

            try: 
                gpu["util"] = float(nv.nvmlDeviceGetUtilizationRates(handle).gpu)

            except Exception:
                pass    

            try:
                gpu["temp"] = float(nv.nvmlDeviceGetTemperature(handle, nv.NVML_TEMPERATURE_GPU))
            except Exception:
                pass

            gpus.append(gpu)
        return gpus


    #adding soon