import asyncio
from app.rag.pipeline import RAGPipeline

async def main():
    rag = RAGPipeline()
    try:
        # Check jobs
        jobs = await rag._search_jobs_fallback(10)
        print("Fallback search returned:", len(jobs))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
