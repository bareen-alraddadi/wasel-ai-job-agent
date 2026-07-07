"""
Wasel — Qdrant Ingestion Pipeline
Builds the Qdrant Cloud indices from the Saudi jobs dataset and learning resources.

Run (from backend/):
  python scripts/build_qdrant_index.py
"""
import os, sys, json, uuid, asyncio
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, Distance, VectorParams, PayloadSchemaType
)
from openai import AsyncOpenAI
from app.core.config import settings

# ──────────────────────────────────────────────
# 1. CONFIG & SETUP
# ──────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent.parent / "data"

URL_QDRANT = settings.URL_QDRANT
API_KEY_QDRANT = settings.API_KEY_QDRANT
COLLECTION_JOBS = "wasel_jobs"
COLLECTION_RESOURCES = "wasel_resources"

VECTOR_DIM = 1536  # text-embedding-3-small dimension
BATCH_SIZE = 64
CHUNK_BATCH = 32

if not URL_QDRANT or not API_KEY_QDRANT:
    raise EnvironmentError("❌ Please set URL_QDRANT and API_KEY_QDRANT in your .env file.")

client = QdrantClient(url=URL_QDRANT, api_key=API_KEY_QDRANT, timeout=60)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def setup_collections(recreate: bool = False) -> None:
    existing = [c.name for c in client.get_collections().collections]

    for coll_name in [COLLECTION_JOBS, COLLECTION_RESOURCES]:
        if recreate and coll_name in existing:
            client.delete_collection(coll_name)
            existing.remove(coll_name)
            print(f"🗑️ Old collection '{coll_name}' deleted.")

        if coll_name not in existing:
            client.create_collection(
                collection_name=coll_name,
                vectors_config=VectorParams(
                    size=VECTOR_DIM,
                    distance=Distance.COSINE,
                ),
            )
            print(f"✨ Collection '{coll_name}' created.")
            
            # Setup payload indices
            if coll_name == COLLECTION_JOBS:
                indexes = [
                    ("job_id", PayloadSchemaType.KEYWORD),
                    ("company", PayloadSchemaType.KEYWORD),
                    ("industry", PayloadSchemaType.KEYWORD),
                    ("job_type", PayloadSchemaType.KEYWORD),
                    ("location", PayloadSchemaType.KEYWORD)
                ]
            else:
                indexes = [
                    ("skill", PayloadSchemaType.KEYWORD),
                    ("provider", PayloadSchemaType.KEYWORD),
                    ("level", PayloadSchemaType.KEYWORD)
                ]
            
            for field, schema in indexes:
                try:
                    client.create_payload_index(
                        collection_name=coll_name,
                        field_name=field,
                        field_schema=schema,
                    )
                except Exception as e:
                    pass
        else:
            print(f"ℹ️ Collection '{coll_name}' already exists.")

# ──────────────────────────────────────────────
# 2. EMBEDDING HELPER
# ──────────────────────────────────────────────
async def embed_batch(texts: list[str]) -> list[list[float]]:
    try:
        resp = await openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )
        return [d.embedding for d in resp.data]
    except Exception as e:
        print(f"Embedding error: {e}")
        return []

# ──────────────────────────────────────────────
# 3. BUILD JOBS
# ──────────────────────────────────────────────
async def ingest_jobs():
    print(f"\n{'─'*55}")
    print("💼 Ingesting Jobs")

    jobs_dir = DATA_DIR / "jobs_dataset"

    # Load only the two known job dataset files (not taxonomy or seed files)
    JOB_FILES = [
        "saudi_jobs_full.json",       # 500 curated jobs (original)
        "new_jobs_prepared.json",     # 10,000 real jobs from Indeed SA
    ]

    all_jobs: list[dict] = []
    for filename in JOB_FILES:
        jf = jobs_dir / filename
        if not jf.exists():
            print(f"   ⚠️  {filename} not found — skipping")
            continue
        with open(jf, encoding="utf-8") as f:
            batch = json.load(f)
        print(f"   📄 {filename}: {len(batch)} jobs")
        all_jobs.extend(batch)

    if not all_jobs:
        print("❌ No jobs loaded. Check that job dataset files exist.")
        return

    print(f"   Total: {len(all_jobs)} jobs across {sum(1 for f in JOB_FILES if (jobs_dir/f).exists())} file(s)")


    text_buffer   = []
    record_buffer = []
    points_batch  = []
    total_upserted = 0

    async def flush_embed_and_upsert():
        nonlocal text_buffer, record_buffer, points_batch, total_upserted
        if not text_buffer: return

        vectors = await embed_batch(text_buffer)

        for job, vec in zip(record_buffer, vectors):
            skills = ", ".join(job.get("required_skills", []) + job.get("preferred_skills", []))
            text = (
                f"{job.get('title','')} at {job.get('company','')} in {job.get('location','')}"
                f". Industry: {job.get('industry','')}. Skills: {skills}. {job.get('description','')[:300]}"
            )

            payload = job.copy()
            payload["text"] = text

            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"job|{job.get('job_id')}"))
            points_batch.append(PointStruct(id=point_id, vector=vec, payload=payload))

        if points_batch:
            client.upsert(collection_name=COLLECTION_JOBS, points=points_batch)
            total_upserted += len(points_batch)

        text_buffer.clear()
        record_buffer.clear()
        points_batch.clear()

    for job in all_jobs:
        skills = ", ".join(job.get("required_skills", []) + job.get("preferred_skills", []))
        text = (
            f"{job.get('title','')} at {job.get('company','')} in {job.get('location','')}"
            f". Industry: {job.get('industry','')}. Skills: {skills}. {job.get('description','')[:300]}"
        )
        text_buffer.append(text)
        record_buffer.append(job)

        if len(text_buffer) >= CHUNK_BATCH:
            await flush_embed_and_upsert()
            print(f"   ⏫ Upserted {total_upserted} jobs so far …", end="\r")

    await flush_embed_and_upsert()
    print(f"   ✅ {total_upserted} jobs upserted                          ")



# ──────────────────────────────────────────────
# 4. BUILD RESOURCES
# ──────────────────────────────────────────────
async def ingest_resources():
    print(f"\n{'─'*55}")
    print("📚 Ingesting Resources")
    res_path = DATA_DIR / "resources_seed.json"
    if not res_path.exists():
        print(f"❌ Resources file not found at {res_path}")
        return

    with open(res_path, encoding="utf-8") as f:
        resources = json.load(f)
    
    text_buffer = []
    record_buffer = []
    points_batch = []
    total_upserted = 0

    async def flush_embed_and_upsert():
        nonlocal text_buffer, record_buffer, points_batch, total_upserted
        if not text_buffer: return
        
        vectors = await embed_batch(text_buffer)
        
        for res, vec in zip(record_buffer, vectors):
            text = f"{res.get('skill','')} {res.get('title','')} {res.get('provider','')} {res.get('description','')}"
            
            payload = res.copy()
            payload["text"] = text

            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"resource|{res.get('title')}|{res.get('provider')}"))
            points_batch.append(PointStruct(id=point_id, vector=vec, payload=payload))

        if points_batch:
            client.upsert(collection_name=COLLECTION_RESOURCES, points=points_batch)
            total_upserted += len(points_batch)
        
        text_buffer.clear()
        record_buffer.clear()
        points_batch.clear()

    for res in resources:
        text = f"{res.get('skill','')} {res.get('title','')} {res.get('provider','')} {res.get('description','')}"
        text_buffer.append(text)
        record_buffer.append(res)

        if len(text_buffer) >= CHUNK_BATCH:
            await flush_embed_and_upsert()
            print(f"   ⏫ Upserted {total_upserted} resources so far …", end="\r")

    await flush_embed_and_upsert()
    print(f"   ✅ {total_upserted} resources upserted                          ")


# ──────────────────────────────────────────────
# 5. ENTRY POINT
# ──────────────────────────────────────────────
async def main():
    print("=" * 55)
    print("  Wasel — Qdrant Index Builder")
    print("=" * 55)
    
    setup_collections(recreate=True)
    await ingest_jobs()
    await ingest_resources()
    
    print(f"\n{'═'*55}")
    print("🎉 DONE! Indices ready in Qdrant.")
    cols = client.get_collections().collections
    print("📚 Collections:")
    for c in cols:
        info = client.get_collection(c.name)
        print(f"   • {c.name} ({info.points_count} points)")

if __name__ == "__main__":
    asyncio.run(main())
