import logging
import sys
from pathlib import Path
from typing import Optional

_LOG_CONFIGURED = False
_LOG_FILE: Optional[Path] = None


def configure_logging(log_level: int = logging.INFO) -> None:
    """初始化全局日志配置（只执行一次）."""
    global _LOG_CONFIGURED, _LOG_FILE
    if _LOG_CONFIGURED:
        return

    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    _LOG_FILE = log_dir / "app.log"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(_LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    _LOG_CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取指定名称的 logger，并确保已配置。"""
    configure_logging()
    return logging.getLogger(name)

