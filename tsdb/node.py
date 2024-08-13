import datetime
from sqlalchemy_json import NestedMutableJson
from typing import List
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import tsdb

class Node(tsdb.Base):
    __tablename__ = "nodes"

    nodeid: Mapped[str] = mapped_column( String(12), primary_key=True )
    hostname: Mapped[str]
    last_data: Mapped[Optional[datetime.datetime]]
    loc_lon: Mapped[Optional[float]]
    loc_lat: Mapped[Optional[float]]
    loc_guess_lon: Mapped[Optional[float]]
    loc_guess_lat: Mapped[Optional[float]]
    contact: Mapped[Optional[str]]
    last_contact_update: Mapped[Optional[datetime.datetime]]
    network: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )
    software: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )

    settings: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )

    macaddrs: Mapped[List["MacAddr"]] = relationship(
        back_populates = "node", cascade = "all, delete-orphan"
    )
    owners: Mapped[List["User"]] = relationship(
        secondary = tsdb.nodes_owners, back_populates = "nodes"
    )
