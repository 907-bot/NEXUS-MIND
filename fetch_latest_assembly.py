import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, desc
from app.models.agent_output import AgentOutput
from app.config import settings

async def get_latest_assembly():
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)
    
    async with AsyncSessionLocal() as session:
        stmt = select(AgentOutput).where(AgentOutput.agent_name == "AssemblerAgent").order_by(desc(AgentOutput.created_at)).limit(1)
        result = await session.execute(stmt)
        output = result.scalar_one_or_none()
        
        if output:
            print("---START_JSON---")
            print(json.dumps(output.output))
            print("---END_JSON---")
        else:
            print("No assembly output found.")

if __name__ == "__main__":
    asyncio.run(get_latest_assembly())
