import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import tsdb

class Session(tsdb.Base):
    __tablename__ = "sessions"

    sessid: Mapped[str] = mapped_column(primary_key=True)
    expire: Mapped[datetime.datetime]
    
    userid: Mapped[int] = mapped_column(ForeignKey("users.userid", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="sessions")
