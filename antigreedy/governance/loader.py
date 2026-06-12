"""PolicyLoader — discovers/hot-reloads Policy modules from a directory.

WSL note (day-0 spike result): inotify does NOT fire on /mnt/* 9p mounts, so the
watcher defaults to force_polling. Freeze mode (eng decision 13): bench/gate runs
freeze the policy set — reloads are ignored with a warning, and policy_set_hash
proves which policies produced which data.
"""
from __future__ import annotations
import hashlib
import importlib.util
import logging
import sys
import threading
from pathlib import Path

from antigreedy.governance.chain import PolicyChain
from antigreedy.governance.policy import Policy

logger = logging.getLogger("antigreedy.loader")


class PolicyLoader:
    def __init__(self, policy_dir: str | Path) -> None:
        self.dir = Path(policy_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._policies: dict[str, Policy] = {}
        self._sources: dict[str, str] = {}  # stem -> file content (for hashing)
        self._frozen = False
        self._watch_thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.reload_all()

    # ---- public ----
    @property
    def chain(self) -> PolicyChain:
        with self._lock:
            return PolicyChain(list(self._policies.values()))

    def policy_names(self) -> list[str]:
        with self._lock:
            return sorted(p.name for p in self._policies.values())

    def policy_set_hash(self) -> str:
        """Hash of the loaded policy sources — stamped on every verdict event."""
        with self._lock:
            h = hashlib.sha256()
            for stem in sorted(self._sources):
                h.update(stem.encode())
                h.update(self._sources[stem].encode())
            return h.hexdigest()[:16]

    def freeze(self) -> None:
        """Bench/gate mode: ignore reloads until thaw()."""
        with self._lock:
            self._frozen = True

    def thaw(self) -> None:
        with self._lock:
            self._frozen = False

    def reload_all(self) -> None:
        for path in sorted(self.dir.glob("*.py")):
            if not path.name.startswith("_"):
                self.load_file(path)
        with self._lock:
            present = {p.stem for p in self.dir.glob("*.py") if not p.name.startswith("_")}
            for stem in list(self._policies):
                if stem not in present:
                    self._unload(stem)

    def load_file(self, path: str | Path) -> None:
        path = Path(path)
        if path.name.startswith("_") or path.suffix != ".py":
            return
        with self._lock:
            if self._frozen:
                logger.warning("policy set FROZEN (bench mode) — ignoring reload of %s", path.name)
                return
        stem = path.stem
        mod_name = f"_antigreedy_policy__{stem}"
        try:
            source = path.read_text()
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if spec is None or spec.loader is None:
                return
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            cls = self._find_policy_class(module)
            if cls is None:
                logger.warning("no Policy subclass in %s", path.name)
                return
            instance = cls()
            with self._lock:
                old = self._policies.get(stem)
                if old is not None:
                    self._safe_unload(old, stem)
                instance.on_load()
                self._policies[stem] = instance
                self._sources[stem] = source
            logger.info("loaded policy '%s' from %s", instance.name, path.name)
        except Exception:
            logger.exception("failed loading policy from %s (keeping previous)", path.name)

    def remove_file(self, path: str | Path) -> None:
        with self._lock:
            if self._frozen:
                logger.warning("policy set FROZEN — ignoring removal of %s", path)
                return
            self._unload(Path(path).stem)

    def start_watching(self, poll_delay_ms: int = 200) -> None:
        """Watch via watchfiles with force_polling (WSL-safe)."""
        from watchfiles import watch  # local import: optional dep

        def _run() -> None:
            for changes in watch(self.dir, force_polling=True,
                                 poll_delay_ms=poll_delay_ms,
                                 stop_event=self._stop):
                for _change, p in changes:
                    if Path(p).exists():
                        self.load_file(p)
                    else:
                        self.remove_file(p)

        self._watch_thread = threading.Thread(target=_run, daemon=True, name="policy-watch")
        self._watch_thread.start()

    def stop_watching(self) -> None:
        self._stop.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=3)
            self._watch_thread = None
        self._stop = threading.Event()

    # ---- internals ----
    def _unload(self, stem: str) -> None:
        inst = self._policies.pop(stem, None)
        self._sources.pop(stem, None)
        if inst is not None:
            self._safe_unload(inst, stem)

    @staticmethod
    def _safe_unload(inst: Policy, stem: str) -> None:
        try:
            inst.on_unload()
        except Exception:
            logger.exception("on_unload failed for %s", stem)

    @staticmethod
    def _find_policy_class(module) -> type[Policy] | None:
        found = None
        for val in vars(module).values():
            if (isinstance(val, type) and issubclass(val, Policy)
                    and val is not Policy and val.__module__ == module.__name__):
                found = val
        return found
