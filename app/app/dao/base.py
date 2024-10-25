from sqlalchemy.future import select
from app.db.session import get_db


class BaseDAO:
    model = None
    
    @classmethod
    async def find_all(cls, **filter_by):
        async with get_db() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()
        
    @classmethod
    async def add(cls, **values):
        async with get_db() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    raise e
                return new_instance