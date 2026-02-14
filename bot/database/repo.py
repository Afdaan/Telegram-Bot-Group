from sqlalchemy import select, delete, func
from bot.database.engine import async_session
from bot.database.models import User, Group, GroupSettings, Warning, StickerPack, Filter, Blacklist, RssFeed, WarnFilter


class Repository:

    @staticmethod
    async def upsert_user(telegram_id: int, username: str = None, first_name: str = None) -> User:
        async with async_session() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if user:
                user.username = username or user.username
                user.first_name = first_name or user.first_name
            else:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                )
                session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_user_by_username(username: str) -> User | None:
        async with async_session() as session:
            return await session.scalar(
                select(User).where(func.lower(User.username) == username.lower())
            )

    @staticmethod
    async def get_user(telegram_id: int) -> User | None:
        async with async_session() as session:
            return await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )

    @staticmethod
    async def upsert_group(telegram_id: int, title: str = None) -> Group:
        async with async_session() as session:
            group = await session.scalar(
                select(Group).where(Group.telegram_id == telegram_id)
            )
            if group:
                group.title = title or group.title
            else:
                group = Group(telegram_id=telegram_id, title=title)
                session.add(group)
            await session.commit()
            await session.refresh(group)
            return group

    @staticmethod
    async def get_or_create_settings(group_id: int) -> GroupSettings:
        async with async_session() as session:
            settings = await session.scalar(
                select(GroupSettings).where(GroupSettings.group_id == group_id)
            )
            if not settings:
                group = await session.scalar(
                    select(Group).where(Group.telegram_id == group_id)
                )
                if not group:
                    group = Group(telegram_id=group_id)
                    session.add(group)
                    await session.flush()
                settings = GroupSettings(group_id=group_id)
                session.add(settings)
                await session.commit()
                await session.refresh(settings)
            return settings

    @staticmethod
    async def update_settings(group_id: int, **kwargs) -> GroupSettings:
        async with async_session() as session:
            settings = await session.scalar(
                select(GroupSettings).where(GroupSettings.group_id == group_id)
            )
            if not settings:
                settings = GroupSettings(group_id=group_id, **kwargs)
                session.add(settings)
            else:
                for key, value in kwargs.items():
                    setattr(settings, key, value)
            await session.commit()
            await session.refresh(settings)
            return settings

    @staticmethod
    async def add_warning(user_id: int, group_id: int, reason: str, warned_by: int) -> tuple[Warning, int]:
        async with async_session() as session:
            warning = Warning(
                user_id=user_id,
                group_id=group_id,
                reason=reason,
                warned_by=warned_by,
            )
            session.add(warning)
            await session.commit()

            count = await session.scalar(
                select(func.count(Warning.id)).where(
                    Warning.user_id == user_id,
                    Warning.group_id == group_id,
                )
            )
            return warning, count

    @staticmethod
    async def get_warnings(user_id: int, group_id: int) -> list[Warning]:
        async with async_session() as session:
            result = await session.scalars(
                select(Warning)
                .where(Warning.user_id == user_id, Warning.group_id == group_id)
                .order_by(Warning.created_at.desc())
            )
            return list(result.all())

    @staticmethod
    async def reset_warnings(user_id: int, group_id: int) -> int:
        async with async_session() as session:
            result = await session.execute(
                delete(Warning).where(
                    Warning.user_id == user_id,
                    Warning.group_id == group_id,
                )
            )
            await session.commit()
            return result.rowcount

    @staticmethod
    async def register_sticker_pack(pack_name: str, owner_id: int) -> StickerPack:
        async with async_session() as session:
            pack = StickerPack(pack_name=pack_name, owner_id=owner_id)
            session.add(pack)
            await session.commit()
            await session.refresh(pack)
            return pack

    @staticmethod
    async def get_user_sticker_packs(owner_id: int) -> list[StickerPack]:
        async with async_session() as session:
            result = await session.scalars(
                select(StickerPack).where(StickerPack.owner_id == owner_id)
            )
            return list(result.all())

    @staticmethod
    async def add_filter(group_id: int, trigger: str, response: str, file_id: str = None, file_type: str = None) -> Filter:
        async with async_session() as session:
            trigger = trigger.lower()
            existing_filter = await session.scalar(
                select(Filter).where(Filter.group_id == group_id, Filter.trigger == trigger)
            )
            if existing_filter:
                existing_filter.response = response
                existing_filter.file_id = file_id
                existing_filter.file_type = file_type
            else:
                existing_filter = Filter(group_id=group_id, trigger=trigger, response=response, file_id=file_id, file_type=file_type)
                session.add(existing_filter)
            await session.commit()
            await session.refresh(existing_filter)
            return existing_filter

    @staticmethod
    async def remove_filter(group_id: int, trigger: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                delete(Filter).where(Filter.group_id == group_id, Filter.trigger == trigger.lower())
            )
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def get_filter(group_id: int, trigger: str) -> Filter | None:
        async with async_session() as session:
            return await session.scalar(
                select(Filter).where(Filter.group_id == group_id, Filter.trigger == trigger.lower())
            )

    @staticmethod
    async def get_filters(group_id: int) -> list[Filter]:
        async with async_session() as session:
            result = await session.scalars(
                select(Filter).where(Filter.group_id == group_id)
            )
            return list(result.all())

    @staticmethod
    async def get_blacklist(group_id: int) -> list[str]:
        async with async_session() as session:
            result = await session.scalars(
                select(Blacklist.trigger).where(Blacklist.group_id == group_id)
            )
            return list(result.all())

    @staticmethod
    async def add_blacklist(group_id: int, trigger: str) -> None:
        async with async_session() as session:
            existing = await session.scalar(
                select(Blacklist).where(
                    Blacklist.group_id == group_id,
                    func.lower(Blacklist.trigger) == trigger.lower(),
                )
            )
            if not existing:
                session.add(Blacklist(group_id=group_id, trigger=trigger.lower()))
                await session.commit()

    @staticmethod
    async def remove_blacklist(group_id: int, trigger: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                delete(Blacklist).where(
                    Blacklist.group_id == group_id,
                    func.lower(Blacklist.trigger) == trigger.lower(),
                )
            )
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def get_rss_feeds(chat_id: int) -> list[RssFeed]:
        async with async_session() as session:
            result = await session.scalars(
                select(RssFeed).where(RssFeed.chat_id == chat_id)
            )
            return list(result.all())

    @staticmethod
    async def get_all_rss_feeds() -> list[RssFeed]:
        async with async_session() as session:
            result = await session.scalars(select(RssFeed))
            return list(result.all())

    @staticmethod
    async def add_rss_feed(chat_id: int, feed_link: str, old_entry_link: str = None) -> bool:
        async with async_session() as session:
            existing = await session.scalar(
                select(RssFeed).where(
                    RssFeed.chat_id == chat_id,
                    RssFeed.feed_link == feed_link,
                )
            )
            if existing:
                return False
            session.add(RssFeed(chat_id=chat_id, feed_link=feed_link, old_entry_link=old_entry_link))
            await session.commit()
            return True

    @staticmethod
    async def remove_rss_feed(chat_id: int, feed_link: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                delete(RssFeed).where(
                    RssFeed.chat_id == chat_id,
                    RssFeed.feed_link == feed_link,
                )
            )
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def update_rss_entry(feed_id: int, new_entry_link: str) -> None:
        async with async_session() as session:
            feed = await session.get(RssFeed, feed_id)
            if feed:
                feed.old_entry_link = new_entry_link
                await session.commit()

    @staticmethod
    async def remove_last_warning(user_id: int, group_id: int) -> bool:
        async with async_session() as session:
            warning = await session.scalar(
                select(Warning)
                .where(Warning.user_id == user_id, Warning.group_id == group_id)
                .order_by(Warning.created_at.desc())
                .limit(1)
            )
            if warning:
                await session.delete(warning)
                await session.commit()
                return True
            return False

    @staticmethod
    async def add_warn_filter(group_id: int, keyword: str, reply: str = "") -> None:
        async with async_session() as session:
            existing = await session.scalar(
                select(WarnFilter).where(
                    WarnFilter.group_id == group_id,
                    func.lower(WarnFilter.keyword) == keyword.lower(),
                )
            )
            if existing:
                existing.reply = reply
            else:
                session.add(WarnFilter(group_id=group_id, keyword=keyword.lower(), reply=reply))
            await session.commit()

    @staticmethod
    async def remove_warn_filter(group_id: int, keyword: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                delete(WarnFilter).where(
                    WarnFilter.group_id == group_id,
                    func.lower(WarnFilter.keyword) == keyword.lower(),
                )
            )
            await session.commit()
            return result.rowcount > 0

    @staticmethod
    async def get_warn_filters(group_id: int) -> list[WarnFilter]:
        async with async_session() as session:
            result = await session.scalars(
                select(WarnFilter).where(WarnFilter.group_id == group_id)
            )
            return list(result.all())
