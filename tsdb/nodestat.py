from typing import Optional
from sqlalchemy.orm import Mapped
import tsdb

class NodeStat(tsdb.Stat,tsdb.Base):
    uptime: Mapped[Optional[int]]
    domain: Mapped[Optional[str]]
    hw_model: Mapped[Optional[str]]
    hw_nproc: Mapped[Optional[int]]
    fw_base: Mapped[Optional[str]]
    fw_release: Mapped[Optional[str]]
    au_branch: Mapped[Optional[str]]
    au_enabled: Mapped[Optional[bool]]
