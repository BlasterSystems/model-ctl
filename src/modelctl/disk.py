"""Store free-space guards (IR-213 parity).

Downloads must not fill the destination pool. The floor is opt-in via
``--min-free-bytes`` (0 = disabled) so existing behavior and test fixtures on
small filesystems stay valid; operators pass a floor derived from their pool
size. All aborts happen BEFORE any write, so nothing partial is published or
marked resumable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from .errors import ModelctlError


class DiskSpaceError(ModelctlError):
    """Raised when a destination volume is below its configured free-space floor."""


def free_bytes(path: Path, statvfs: Callable[[Path], os.statvfs_result] | None = None) -> int:
    """Free bytes available to unprivileged writes on ``path``'s volume."""
    result = (statvfs or os.statvfs)(path)
    return result.f_bavail * result.f_bsize


def ensure_free_space(
    path: Path,
    floor_bytes: int,
    required_extra: int = 0,
    *,
    statvfs: Callable[[Path], os.statvfs_result] | None = None,
) -> int:
    """Raise :class:`DiskSpaceError` unless ``path``'s volume has room for
    ``required_extra`` bytes of writes on top of ``floor_bytes``. Returns the
    measured free bytes. A floor of 0 disables the check entirely."""
    if floor_bytes <= 0:
        return 0
    free = free_bytes(path, statvfs)
    if free < floor_bytes + required_extra:
        raise DiskSpaceError(
            f"store has {free / 2**40:.2f} TiB free at {path}; this operation "
            f"needs a {floor_bytes / 2**40:.1f} TiB floor"
            + (f" plus {required_extra / 2**40:.2f} TiB of expected files" if required_extra else "")
            + "; free space on the volume or lower --min-free-bytes"
        )
    return free
