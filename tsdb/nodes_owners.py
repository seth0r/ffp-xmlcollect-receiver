from sqlalchemy import Table, Column, ForeignKey
import tsdb

nodes_owners = Table(
    "nodes_owners",
    tsdb.Base.metadata,
    Column("nodeid", ForeignKey("nodes.nodeid", ondelete="CASCADE"), primary_key=True),
    Column("userid", ForeignKey("users.userid", ondelete="CASCADE"), primary_key=True)
)
