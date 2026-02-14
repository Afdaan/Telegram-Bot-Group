from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    about: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    warnings: Mapped[list["Warning"]] = relationship(back_populates="user")
    sticker_packs: Mapped[list["StickerPack"]] = relationship(back_populates="owner")


class Group(Base):
    __tablename__ = "groups_"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    settings: Mapped["GroupSettings"] = relationship(back_populates="group", uselist=False)
    filters: Mapped[list["Filter"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    blacklists: Mapped[list["Blacklist"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    warn_filters: Mapped[list["WarnFilter"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class GroupSettings(Base):
    __tablename__ = "group_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups_.telegram_id", ondelete="CASCADE"), unique=True
    )
    warn_limit: Mapped[int] = mapped_column(Integer, default=3)
    welcome_msg: Mapped[str | None] = mapped_column(Text)
    goodbye_msg: Mapped[str | None] = mapped_column(Text)
    rules_text: Mapped[str | None] = mapped_column(Text)
    antiflood_limit: Mapped[int] = mapped_column(Integer, default=5)
    antiflood_time: Mapped[int] = mapped_column(Integer, default=10)
    slowmode_seconds: Mapped[int] = mapped_column(Integer, default=0)
    report_enabled: Mapped[int] = mapped_column(Integer, default=1)
    warn_action: Mapped[str] = mapped_column(String(10), default="ban")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    group: Mapped["Group"] = relationship(back_populates="settings")


class Warning(Base):
    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups_.telegram_id", ondelete="CASCADE")
    )
    reason: Mapped[str] = mapped_column(String(512), default="No reason provided")
    warned_by: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="warnings")


class WarnFilter(Base):
    __tablename__ = "warn_filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups_.telegram_id", ondelete="CASCADE")
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    reply: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    group: Mapped["Group"] = relationship(back_populates="warn_filters")


class StickerPack(Base):
    __tablename__ = "sticker_packs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pack_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="sticker_packs")


class Filter(Base):
    __tablename__ = "filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups_.telegram_id", ondelete="CASCADE")
    )
    trigger: Mapped[str] = mapped_column(String(255), nullable=False)
    response: Mapped[str | None] = mapped_column(Text)
    file_id: Mapped[str | None] = mapped_column(String(255))
    file_type: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    group: Mapped["Group"] = relationship(back_populates="filters")


class Blacklist(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups_.telegram_id", ondelete="CASCADE")
    )
    trigger: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    group: Mapped["Group"] = relationship(back_populates="blacklists")


class RssFeed(Base):
    __tablename__ = "rss_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    feed_link: Mapped[str] = mapped_column(String(512), nullable=False)
    old_entry_link: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
