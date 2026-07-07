import asyncio
from app.rag.pipeline import rag_pipeline

async def test():
    await rag_pipeline.initialize()
    jobs = await rag_pipeline.search_jobs('python developer', 1)
    print("JOBS FOUND:", len(jobs))
    if jobs:
        print("FIRST JOB:", jobs[0].get("title"))

asyncio.run(test())
