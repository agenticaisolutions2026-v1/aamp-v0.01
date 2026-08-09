from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)