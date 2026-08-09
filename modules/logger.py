import sys
import os
import logging
import importlib.abc
import importlib.machinery

import config

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d (%(funcName)s) — %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(f"logs/app-{config.PROJECT_NAME}.log", encoding="utf-8"), # Я в курсе, что так делать нельзя
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(config.PROJECT_NAME)

class ImportLogger(importlib.abc.MetaPathFinder):
    """
    Логгер импортов
    """
    def find_spec(self, fullname, path, target=None):
        if fullname in sys.modules:
            return None

        try:
            spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        except Exception:
            return None

        if spec is None:
            return None

        origin = getattr(spec, "origin", None)
        if origin:
            try:
                origin_abspath = os.path.abspath(origin)
                if origin_abspath.startswith(PROJECT_ROOT):
                    logger.info("Импортируется модуль: %s (origin=%s)", fullname, origin_abspath)
            except Exception:
                pass

        return None

for finder in sys.meta_path:
    if isinstance(finder, ImportLogger):
        break
else:
    sys.meta_path.insert(0, ImportLogger())
