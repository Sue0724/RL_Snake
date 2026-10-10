"""checkpoint 文件读取和公共加载错误；不写入来源文件。"""

import pickle
from pathlib import Path

import torch


class CheckpointError(ValueError):
    """文件不可读、格式无效或模型无法恢复时的预期加载错误。"""


RESTORE_ERRORS = (
    ValueError, RuntimeError, KeyError, TypeError, IndexError, AttributeError,
    AssertionError, OverflowError,
)


def checkpoint_error(path, reason):
    """路径用于定位来源；详细原异常由调用方通过 raise ... from 保留。"""
    path = Path(path).expanduser().resolve()
    # Torch 的恢复异常可能包含多行内部细节，CLI 只展示第一行。
    lines = str(reason).splitlines()
    reason = lines[0] if lines else "无法恢复模型"
    return CheckpointError(f"模型加载失败：{path}：{reason}")


def read_checkpoint(path, *, device="cpu"):
    """读取一次 checkpoint，拒绝执行任意 pickle 对象。"""
    path = Path(path).expanduser().resolve()
    try:
        checkpoint = torch.load(path, map_location=device, weights_only=True)
    except FileNotFoundError as error:
        raise checkpoint_error(path, "文件不存在") from error
    except PermissionError as error:
        raise checkpoint_error(path, "没有读取权限") from error
    except IsADirectoryError as error:
        raise checkpoint_error(path, "路径指向目录，请提供 checkpoint 文件") from error
    except (OSError, EOFError, pickle.UnpicklingError, *RESTORE_ERRORS) as error:
        raise checkpoint_error(path, "无法读取 checkpoint，文件损坏或格式不支持") from error
    version = checkpoint.get("format_version") if isinstance(checkpoint, dict) else None
    if type(version) is not int or version != 1:
        raise checkpoint_error(path, "checkpoint 格式不支持，当前要求 format_version=1")
    return checkpoint
