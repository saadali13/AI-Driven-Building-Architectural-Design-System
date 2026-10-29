import os
import json
import re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    HAVE_VECTOR_SEARCH = True
except ImportError:
    HAVE_VECTOR_SEARCH = False
    SentenceTransformer = None
    chromadb = None

from auth_service import auth_router
from cost_estimation_service import cost_router

app = FastAPI(
    title="ArchAI NLP Vector & Semantic Search Service",
    description="Vector search and authentication microservice for Architext_v1 layout JSON datasets using SentenceTransformers, ChromaDB & PostgreSQL RBAC (Supervised by Dr. Aamer Nadeem - CUST)",
    version="2.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Authentication & RBAC Router
app.include_router(auth_router)
# Mount Location-Aware Cost Estimation & Rate Analysis Router
app.include_router(cost_router)

# Load sentence transformer model & ChromaDB client if available
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = None
chroma_client = None
collection = None

if HAVE_VECTOR_SEARCH:
    try:
        model = SentenceTransformer(MODEL_NAME)
        CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collection = chroma_client.get_or_create_collection(
            name="architext_layouts",
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as exc:
        print(f"[Warning] Failed to load vector model or collection: {exc}")
        HAVE_VECTOR_SEARCH = False

class LayoutSearchRequest(BaseModel):
    prompt: str = Field(..., example="A modern 3 marla residential plan with 2 bedrooms, 2 bathrooms, open living room and kitchen.")
    top_k: int = Field(default=5, ge=1, le=20)
    min_beds: Optional[int] = None
    min_baths: Optional[int] = None
    max_plot_marla: Optional[float] = None

class FloorPlanResponse(BaseModel):
    id: str
    prompt_text: str
    similarity_score: float
    bed_count: int
    bath_count: int
    plot_marla: float
    floor_plan_json: Dict[str, Any]

def preprocess_prompt(text: str) -> str:
    """Clean prompt string, normalize whitespace, extract unit specifications."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\-\.]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

@app.get("/")
def read_root():
    return {
        "system": "ArchAI NLP & Vector Search Engine with PostgreSQL RBAC",
        "model": MODEL_NAME,
        "embedding_dimensions": 384,
        "auth_endpoints": ["/api/auth/login", "/api/auth/signup", "/api/auth/me"],
        "status": "healthy"
    }

@app.post("/api/v1/semantic-search", response_model=List[FloorPlanResponse])
async def search_floor_plans(req: LayoutSearchRequest):
    cleaned_prompt = preprocess_prompt(req.prompt)
    if not cleaned_prompt:
        raise HTTPException(status_code=400, detail="Prompt text cannot be empty")

    if not HAVE_VECTOR_SEARCH or model is None or collection is None:
        # Fallback return empty list or dummy matching response if vector engine is offline
        return []

    # Generate 384-dim dense vector embedding
    query_embedding = model.encode(cleaned_prompt).tolist()

    # Build metadata filters
    where_conditions = {}
    if req.min_beds is not None:
        where_conditions["bed_count"] = {"$gte": req.min_beds}
    if req.min_baths is not None:
        where_conditions["bath_count"] = {"$gte": req.min_baths}

    # Query ChromaDB collection using Cosine Similarity
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=req.top_k,
        where=where_conditions if where_conditions else None,
        include=["metadatas", "documents", "distances"]
    )

    formatted_results = []
    if results and results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            record_id = results["ids"][0][i]
            distance = results["distances"][0][i]
            metadata = results["metadatas"][0][i]
            
            # Convert cosine distance to percentage score
            similarity = max(0.0, min(1.0, 1.0 - distance))

            formatted_results.append(FloorPlanResponse(
                id=record_id,
                prompt_text=metadata.get("prompt_text", ""),
                similarity_score=round(similarity * 100, 2),
                bed_count=metadata.get("bed_count", 0),
                bath_count=metadata.get("bath_count", 0),
                plot_marla=metadata.get("plot_marla", 5.0),
                floor_plan_json=json.loads(metadata.get("floor_plan_json", "{}"))
            ))

    return formatted_results

@app.post("/api/v1/ingest-architext-dataset")
async def ingest_dataset(records: List[Dict[str, Any]]):
    """Ingest records from THEODOROS/Architext_v1 into 384-dim vector index."""
    if not HAVE_VECTOR_SEARCH or model is None or collection is None:
        raise HTTPException(status_code=503, detail="Vector search engine is unavailable. Please install sentence-transformers and chromadb.")

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for item in records:
        rec_id = str(item["id"])
        prompt = item["prompt"]
        fp_json = item["floor_plan_json"]
        
        emb = model.encode(preprocess_prompt(prompt)).tolist()
        ids.append(rec_id)
        embeddings.append(emb)
        documents.append(prompt)
        metadatas.append({
            "prompt_text": prompt,
            "bed_count": item.get("bed_count", 2),
            "bath_count": item.get("bath_count", 2),
            "plot_marla": item.get("plot_marla", 5.0),
            "floor_plan_json": json.dumps(fp_json)
        })

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )
    return {"status": "success", "ingested_count": len(ids)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("semantic_search_service:app", host="0.0.0.0", port=8000, reload=True)
