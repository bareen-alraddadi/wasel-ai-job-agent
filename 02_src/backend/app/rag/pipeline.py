"""
Wasel — RAG Pipeline (OpenAI embeddings + Qdrant)
Semantic search over the 500-job Saudi dataset and learning resources.
"""
import os, json, logging, asyncio
from typing import List, Dict
from pathlib import Path
from qdrant_client import QdrantClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# Paths for fallback stub data
DATA_DIR = Path(__file__).parent.parent.parent / "data"

class RAGPipeline:
    """
    Manages two Qdrant collections:
      1. wasel_jobs  (500 real jobs)
      2. wasel_resources  (courses & tutorials)
    """

    def __init__(self):
        self._oai = None
        self._initialized = False
        self.qdrant = None
        self.jobs_collection = "wasel_jobs"
        self.resources_collection = "wasel_resources"

    # ── Init ─────────────────────────────────────────────────

    async def initialize(self):
        if self._initialized:
            return

        try:
            # Initialize Qdrant client
            self.qdrant = QdrantClient(
                url=settings.URL_QDRANT,
                api_key=settings.API_KEY_QDRANT,
                timeout=30
            )
            # Just test connection by getting collections
            self.qdrant.get_collections()
            self._initialized = True
            logger.info("✅ Connected to Qdrant Cloud.")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant Cloud: {e}")
            self._initialized = False

    # ── Embedding ────────────────────────────────────────────

    async def _embed(self, text: str) -> list[float]:
        from openai import AsyncOpenAI
        if self._oai is None:
            self._oai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        resp = await self._oai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text[:8000],
        )
        return resp.data[0].embedding

    # ── Search ───────────────────────────────────────────────

    async def search_jobs(self, query: str, top_k: int = 3) -> List[Dict]:
        """Semantic search over Saudi job postings."""
        if not self._initialized:
            logger.warning("Qdrant not initialized, returning stub jobs.")
            return self._stub_jobs()[:top_k]

        try:
            vec = await self._embed(query)
            search_result = self.qdrant.query_points(
                collection_name=self.jobs_collection,
                query=vec,
                limit=top_k
            )
            
            results = []
            seen = set()  # Deduplicate by title+company
            for hit in search_result.points:
                job = hit.payload.copy()
                job["_similarity"] = hit.score
                # Build a dedup key from title and company (case-insensitive)
                dedup_key = (job.get("title", "").lower().strip(), job.get("company", "").lower().strip())
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    results.append(job)
                
            if not results:
                return self._stub_jobs()[:top_k]
            return results[:top_k]
        except Exception as e:
            logger.error(f"Job search error: {e}")
            return self._stub_jobs()[:top_k]

    async def search_resources(self, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic search over learning resources."""
        if not self._initialized:
            logger.warning("Qdrant not initialized, returning empty resources.")
            return []

        try:
            vec = await self._embed(query)
            search_result = self.qdrant.query_points(
                collection_name=self.resources_collection,
                query=vec,
                limit=top_k
            )
            
            results = []
            for hit in search_result.points:
                r = hit.payload.copy()
                r["_similarity"] = hit.score
                results.append(r)
                
            return results
        except Exception as e:
            logger.error(f"Resource search error: {e}")
            return []

    # ── Helpers ──────────────────────────────────────────────

    def _stub_jobs(self) -> List[Dict]:
        return [
            {"job_id":"s1","title":"AI/ML Engineer","company":"NEOM","location":"Tabuk",
             "description":"Build AI solutions for smart city infrastructure.",
             "required_skills":["Python","Machine Learning","PyTorch"],"preferred_skills":["Docker","MLflow"],
             "salary_range":"20000-30000 SAR","job_type":"Full-time","industry":"Smart City",
             "apply_link":"https://careers.neom.com"},
            {"job_id":"s2","title":"Data Scientist","company":"stc","location":"Riyadh",
             "description":"Analyze telecom data and build predictive models.",
             "required_skills":["Python","SQL","Pandas","Scikit-learn"],"preferred_skills":["Spark","Tableau"],
             "salary_range":"14000-20000 SAR","job_type":"Full-time","industry":"Telecom",
             "apply_link":"https://careers.stc.com.sa"},
            {"job_id":"s3","title":"Backend Engineer","company":"Careem","location":"Riyadh",
             "description":"Build scalable backend services for millions of users.",
             "required_skills":["Python","FastAPI","PostgreSQL","Docker"],"preferred_skills":["AWS","Redis"],
             "salary_range":"18000-28000 SAR","job_type":"Full-time","industry":"Transportation",
             "apply_link":"https://careers.careem.com"},
        ]

rag_pipeline = RAGPipeline()
