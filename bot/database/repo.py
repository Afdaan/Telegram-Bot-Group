from sqlalchemy import select, delete, func
from bot.database.engine import async_session
from bot.database.models import User, Group, GroupSettings, Warning, StickerPack, Filter


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
