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
    def _read_smi(self): 
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, 
            text = True, 
            timeout=5, 
            check=True
        ).stdout
        gpus = []
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 6: 
                continue

            index, name, (utils, used, total, temp) = parts[0],",".join(parts[1:-4]), parts[-4:]
            used, total = _num(used),_num(total)
            if used is None and total is None: 
                continue

            gpu = {
                "index":int(index), 
                'name':name, 
                'mem_used_gb': used / 1024, 
                'mem_total_gb':total / 1024
            }

            if _num(utils) is not None: 
                gpu['utils'] = _num(utils)
            if _num(temp) is not None: 
                gpu['temp'] = _num(temp)

            gpus.append(gpu)

        return gpus
    


#one measurement (what measure () give you)

class Measurement:
    def __init__(self, name, keep_samples = False): 
        self.name, self.keep_samples = name, keep_samples   
        self.stats, self.samples, self.alerts, self.gpus = None, [],[], {}
        self._t0, self._agg, self._n = time.perf_counter(), {}, 0


    def _add(self, flat, gpus, timestamp): 
        self._n += 1
        for key, value  in flat.items(): 
            if value is None:
                continue

            total, peak, count = self._agg.get(key, (0.0, float('-inf'), 0))
            self._agg[key] = (total + value, max(peak, value),count + 1 )

        for g in gpus: 
            self.gpus[g['index']] = {'name':g['name'], 'mem_total_gb':round(g['mem_total_gb'],2)}

        if self.keep_samples: 
            self.samples.append(
                {
                    "t":round(time.perf_counter() - self._t0, 3), **flat
                }
            )


    def _finish(self): 
        self.stats = {
            "name": self.name, "seconds": round(time.perf_counter() - self._t0, 2), "samples": self._n,
            "metrics": {k: {"avg": round(t / c, 2), "peak": round(p, 2)} for k, (t, p, c) in sorted(self._agg.items())},
            "gpus": [{"index": i, **info} for i, info in sorted(self.gpus.items())],
            "alerts": list(self.alerts),
        }

        if self.keep_samples: 
            self.stats['samples_data'] = self.samples


    def report(self):
        return ResourceMonitor.format(self.stats)




# the monitor
class ResourceMonitor:
    def __init__(self, interval=1.0, disk_path=".", track=(), limits=None, on_alert=None,
                 keep_samples=False, gpu=True, keep_records=200):
        """
        interval:     seconds between samples while measuring.
        disk_path:    which disk to watch (the one holding this path).
        track:        process names (substring, e.g. "ollama") or PIDs to watch, with their child processes.
        limits:       {"cpu": 90, "ram": 90, "swap": 50, "disk": 95, "gpu_util": 98, "gpu_mem": 90, "gpu_temp": 85}
                      An alert fires when a value crosses its limit, and again only after it dropped below.
        on_alert:     function(metric, value, limit), called from the sampling thread.
        keep_samples: also keep every sample (for charts); off by default to save memory.
        """
        if interval < 0.1:
            raise ValueError("interval must be at least 0.1 seconds")
        self.limits = dict(limits or {})
        unknown = set(self.limits) - set(LIMIT_KEYS)
        if unknown:
            raise ValueError(f"Unknown limits {sorted(unknown)}. Use: {sorted(LIMIT_KEYS)}")

        self.interval, self.disk_path, self.on_alert, self.keep_samples = interval, disk_path, on_alert, keep_samples
        self._track_names = [str(t).lower() for t in track if not isinstance(t, int)]
        self._track_pids = {t for t in track if isinstance(t, int)}
        self._procs = {}                                   # pid -> Process, kept so cpu_percent has history
        self.gpu = GPUReader() if gpu else GPUReader.__new__(GPUReader)
        if not gpu:
            self.gpu.source, self.gpu.last_error = None, None

        self._me = psutil.Process()
        self._lock = threading.Lock()
        self._sessions, self._thread, self._stop = [], None, None
        self._breached = set()
        self.alerts = deque(maxlen=200)
        self.records = deque(maxlen=keep_records)
        self.last_error = None
        psutil.cpu_percent(None)                           # the first reading is meaningless; prime it
        self._me.cpu_percent(None)

    # ---------- readings ----------
    def snapshot(self):
        """One reading of everything. CPU numbers are averages since the previous reading."""
        vm, sw, du = psutil.virtual_memory(), psutil.swap_memory(), psutil.disk_usage(self.disk_path)
        with self._me.oneshot():
            me = {"rss_gb": self._me.memory_info().rss / _GB, "cpu_percent": self._me.cpu_percent(None)}
        return {
            "time": time.time(),
            "cpu": {"percent": psutil.cpu_percent(None), "cores": psutil.cpu_count(),
                    "load_avg": os.getloadavg()[0] if hasattr(os, "getloadavg") else None},
            "ram": {"used_gb": vm.used / _GB, "available_gb": vm.available / _GB,
                    "total_gb": vm.total / _GB, "percent": vm.percent},
            "swap": {"used_gb": sw.used / _GB, "percent": sw.percent},
            "disk": {"path": str(self.disk_path), "free_gb": du.free / _GB, "total_gb": du.total / _GB,
                     "percent": du.percent},
            "process": me,                                 # this Python process; cpu 100 = one full core
            "tracked": self._read_tracked(),
            "gpus": self.gpu.read(),
        }

    def _read_tracked(self):
        if not (self._track_names or self._track_pids):
            return None
        found = {}
        for p in psutil.process_iter(["pid", "name"]):
            pid, name = p.info["pid"], (p.info["name"] or "").lower()
            if pid == os.getpid():
                continue
            if pid in self._track_pids or any(n in name for n in self._track_names):
                found[pid] = p
                try:
                    for child in p.children(recursive=True):
                        found.setdefault(child.pid, child)
                except psutil.Error:
                    pass
        self._procs = {pid: self._procs.get(pid, p) for pid, p in found.items()}
        rss, cpu = 0.0, 0.0
        for p in self._procs.values():
            try:
                rss += p.memory_info().rss
                cpu += p.cpu_percent(None)
            except psutil.Error:                           # process ended or is not readable
                pass
        return {"pids": sorted(self._procs), "rss_gb": rss / _GB, "cpu_percent": cpu}

    @staticmethod
    def _flat(s):
        f = {"cpu_percent": s["cpu"]["percent"], "load_avg": s["cpu"]["load_avg"],
             "ram_percent": s["ram"]["percent"], "ram_used_gb": s["ram"]["used_gb"],
             "swap_percent": s["swap"]["percent"], "disk_percent": s["disk"]["percent"],
             "proc_rss_gb": s["process"]["rss_gb"], "proc_cpu_percent": s["process"]["cpu_percent"]}
        if s["tracked"]:
            f["tracked_rss_gb"], f["tracked_cpu_percent"] = s["tracked"]["rss_gb"], s["tracked"]["cpu_percent"]
        utils, mems, temps = [], [], []
        for g in s["gpus"]:
            i = g["index"]
            pct = 100 * g["mem_used_gb"] / g["mem_total_gb"] if g["mem_total_gb"] else None
            f[f"gpu{i}_mem_used_gb"], f[f"gpu{i}_mem_percent"] = g["mem_used_gb"], pct
            mems.append(pct)
            if "util" in g:
                f[f"gpu{i}_util"] = g["util"]
                utils.append(g["util"])
            if "temp" in g:
                f[f"gpu{i}_temp"] = g["temp"]
                temps.append(g["temp"])
        for key, values in (("gpu_util_max", utils), ("gpu_mem_percent_max", mems), ("gpu_temp_max", temps)):
            values = [v for v in values if v is not None]
            if values:
                f[key] = max(values)
        return f

    def system_info(self):
        gpus = self.gpu.read()
        return {"platform": platform.platform(), "cpu_cores": psutil.cpu_count(),
                "ram_gb": round(psutil.virtual_memory().total / _GB, 1),
                "gpus": [{"name": g["name"], "mem_gb": round(g["mem_total_gb"], 1)} for g in gpus],
                "gpu_source": self.gpu.source}

    # ---------- limits ----------
    def check(self):
        """One reading now: which limits are exceeded right now. No callbacks, no memory of earlier alerts."""
        flat = self._flat(self.snapshot())
        exceeded = []
        for name, limit in self.limits.items():
            value = flat.get(LIMIT_KEYS[name])
            if value is not None and value > limit:
                exceeded.append({"metric": name, "value": round(value, 1), "limit": limit})
        return exceeded

    def _new_alerts(self, flat):
        """Alerts for limits crossed since the last reading (re-armed once the value drops below the limit)."""
        fired = []
        with self._lock:
            for name, limit in self.limits.items():
                value = flat.get(LIMIT_KEYS[name])
                if value is None:
                    continue
                if value > limit and name not in self._breached:
                    self._breached.add(name)
                    alert = {"time": time.time(), "metric": name, "value": round(value, 1), "limit": limit}
                    fired.append(alert)
                    self.alerts.append(alert)
                elif value <= limit:
                    self._breached.discard(name)
        return fired

    # ---------- measuring ----------
    def start(self, name="monitor"):
        """Start measuring. Pair with stop(). Several measurements can run at the same time."""
        m = Measurement(name, self.keep_samples)
        with self._lock:
            self._sessions.append(m)
            if self._thread is None:
                self._stop = threading.Event()
                self._thread = threading.Thread(target=self._loop, args=(self._stop,), daemon=True)
                self._thread.start()
        psutil.cpu_percent(None)                           # new baseline: CPU readings average since the last reading
        self._me.cpu_percent(None)
        self._record(self.snapshot(), first=True)          # a first reading, so even a very short block has data
        return m

    def stop(self, m):
        """Stop a measurement. Returns its stats dict (also in m.stats)."""
        self._record(self.snapshot())                      # a last reading
        thread = None
        with self._lock:
            self._sessions.remove(m)
            if not self._sessions and self._thread is not None:
                self._stop.set()
                thread, self._thread = self._thread, None
        if thread:
            thread.join(timeout=self.interval + 2)
        m._finish()
        self.records.append(m.stats)
        return m.stats

    @contextmanager
    def measure(self, name="block"):
        """with monitor.measure("ingest") as m: ...      then m.stats / m.report()"""
        m = self.start(name)
        try:
            yield m
        finally:
            self.stop(m)

    def watch(self, name=None):
        """Decorator: @monitor.watch("answer"). Results are appended to monitor.records."""
        def decorator(fn):
            def wrapper(*args, **kwargs):
                with self.measure(name or fn.__name__):
                    return fn(*args, **kwargs)
            wrapper.__name__, wrapper.__doc__ = fn.__name__, fn.__doc__
            return wrapper
        return decorator

    def _loop(self, stop_event):
        while not stop_event.wait(self.interval):
            try:
                self._record(self.snapshot())
            except Exception as e:                         # keep sampling whatever happens
                self.last_error = e

    def _record(self, snap, first=False):
        flat = self._flat(snap)
        if first:                                          # right after a baseline reset, CPU numbers mean nothing
            for key in ("cpu_percent", "proc_cpu_percent", "tracked_cpu_percent"):
                if key in flat:
                    flat[key] = None
        fired = self._new_alerts(flat)
        with self._lock:
            for m in self._sessions:
                m._add(flat, snap["gpus"], snap["time"])
                m.alerts.extend(fired)
        for alert in fired:
            if self.on_alert:
                try:
                    self.on_alert(alert["metric"], alert["value"], alert["limit"])
                except Exception as e:                     # a broken callback must not stop the sampler
                    self.last_error = e

    # ---------- check before you start ----------
    def require(self, ram_gb=None, gpu_gb=None, disk_gb=None):
        """Raise InsufficientResources unless that much is free right now. Add 20-30% headroom to model sizes,
        because the context window and runtime need memory on top of the weights."""
        problems, free = [], {}
        if ram_gb is not None:
            free["ram_gb"] = psutil.virtual_memory().available / _GB
            if free["ram_gb"] < ram_gb:
                problems.append(f"RAM: need {ram_gb} GB, {free['ram_gb']:.1f} GB available")
        if gpu_gb is not None:
            gpus = self.gpu.read()
            if not gpus:
                problems.append("GPU: no NVIDIA GPU detected")
            else:
                free["gpu_gb"] = max(g["mem_total_gb"] - g["mem_used_gb"] for g in gpus)
                if free["gpu_gb"] < gpu_gb:
                    problems.append(f"GPU: need {gpu_gb} GB, {free['gpu_gb']:.1f} GB free on the emptiest GPU")
        if disk_gb is not None:
            free["disk_gb"] = psutil.disk_usage(self.disk_path).free / _GB
            if free["disk_gb"] < disk_gb:
                problems.append(f"Disk: need {disk_gb} GB, {free['disk_gb']:.1f} GB free")
        if problems:
            raise InsufficientResources("; ".join(problems))
        return free

    # ---------- output ----------
    @staticmethod
    def format(stats):
        m = stats["metrics"]

        def span(key, unit, digits=1):
            if key not in m:
                return None
            return f"avg {m[key]['avg']:.{digits}f}{unit}  peak {m[key]['peak']:.{digits}f}{unit}"

        lines = [f"{stats['name']}   {stats['seconds']}s, {stats['samples']} samples"]
        rows = [("cpu", span("cpu_percent", "%")), ("ram", span("ram_percent", "%")),
                ("ram used", span("ram_used_gb", " GB")), ("swap", span("swap_percent", "%")),
                ("this process", span("proc_rss_gb", " GB", 2)), ("  its cpu", span("proc_cpu_percent", "%")),
                ("tracked", span("tracked_rss_gb", " GB", 2)), ("  their cpu", span("tracked_cpu_percent", "%")),
                ("disk", span("disk_percent", "%"))]
        for g in stats["gpus"]:
            i = g["index"]
            rows += [(f"gpu{i}", f"{g['name']}, {g['mem_total_gb']} GB"),
                     ("  util", span(f"gpu{i}_util", "%")), ("  memory", span(f"gpu{i}_mem_used_gb", " GB", 2)),
                     ("  temp", span(f"gpu{i}_temp", " C", 0))]
        lines += [f"  {label:<18}{text}" for label, text in rows if text]
        for a in stats["alerts"]:
            lines.append(f"  ALERT {a['metric']} reached {a['value']} (limit {a['limit']})")
        return "\n".join(lines)

    def save_json(self, path):
        Path(path).write_text(json.dumps(list(self.records), indent=2, default=str), encoding="utf-8")