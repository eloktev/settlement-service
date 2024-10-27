from sqlalchemy.future import select
from pydantic import BaseModel
from app.db.session import get_db
from sqlalchemy.dialects.postgresql import insert  


class BaseDAO:
    model = None
    create_schema = None
    BATCH_SIZE = 500  # Set a default batch size for all DAOs
    
   
    @classmethod
    async def find_all(cls, session, **filter_by):
        query = select(cls.model).filter_by(**filter_by)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def add(cls, session, **values):
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        return new_instance
    
        
    @classmethod
    async def batch_insert(cls, instances: list[BaseModel], batch_size: int = None):
        """Batch insert instances based on Pydantic create schema.

        Args:
            instances (List[BaseModel]): List of Pydantic schema instances to insert.
            batch_size (int, optional): Number of records to insert per batch.
        """
        if batch_size is None:
            batch_size = cls.BATCH_SIZE

        # Convert Pydantic schema instances to dictionaries
        data = [instance.model_dump() for instance in instances]

        async for session in get_db():
            try:
                for i in range(0, len(data), batch_size):
                    batch_data = data[i:i + batch_size]
                    stmt = insert(cls.model).values(batch_data)
                    stmt = stmt.on_conflict_do_nothing()  # Ignore conflicts
                    await session.execute(stmt)
                    # i += batch_size 
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e