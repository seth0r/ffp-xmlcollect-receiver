import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import String, DateTime, Column, ForeignKey
from sqlalchemy.ext.declarative import declared_attr

class Stat:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() + "s"

    __table_args__ = ({
        'timescaledb_hypertable':{
            'time_column_name': 'timestamp'
        }
    })

    timestamp = Column(
        DateTime(), default=datetime.datetime.now, primary_key=True
    )
    
    @declared_attr
    def nodeid(cls):
        return Column(String(12), ForeignKey("nodes.nodeid", ondelete="CASCADE"), primary_key=True )

    @declared_attr
    def node(cls):
        return relationship("Node")

