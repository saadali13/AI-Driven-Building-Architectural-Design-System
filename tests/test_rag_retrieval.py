"""
Unit tests for Phase 10: RAG document generation and FAISS vector retrieval.
"""

import pytest
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    WallModel,
    OpeningModel,
    RoomModel,
    GraphEdgeModel
)
from dataset.rag_generator import ArchitecturalRAGGenerator
from retrieval.vector_store import ArchitecturalVectorStore


@pytest.fixture
def sample_plans():
    # Plan 1: 3BHK 120m2
    p1 = CanonicalFloorPlan(
        metadata=MetadataModel(plan_id="plan_3bhk", source_type="synthetic_generated"),
        boundary=[[0, 0], [12, 0], [12, 10], [0, 10], [0, 0]],
        total_area_m2=120.0,
        rooms=[
            RoomModel(room_id="r1", room_type="living_room", room_name="Living Room", polygon=[[0,0],[6,0],[6,6],[0,6],[0,0]], area_m2=36.0, centroid=[3,3]),
            RoomModel(room_id="r2", room_type="bedroom", room_name="Master Bedroom", polygon=[[6,0],[12,0],[12,5],[6,5],[6,0]], area_m2=30.0, centroid=[9,2.5]),
            RoomModel(room_id="r3", room_type="bedroom", room_name="Bedroom 2", polygon=[[6,5],[12,5],[12,10],[6,10],[6,5]], area_m2=30.0, centroid=[9,7.5]),
            RoomModel(room_id="r4", room_type="bedroom", room_name="Guest Bedroom", polygon=[[0,6],[4,6],[4,10],[0,10],[0,6]], area_m2=16.0, centroid=[2,8]),
            RoomModel(room_id="r5", room_type="bathroom", room_name="Bath", polygon=[[4,6],[6,6],[6,10],[4,10],[4,6]], area_m2=8.0, centroid=[5,8], is_habitable=False)
        ],
        graph_edges=[
            GraphEdgeModel(source_room_id="r1", target_room_id="r2", relationship_type="via_door")
        ]
    )

    # Plan 2: 1BHK Studio 45m2
    p2 = CanonicalFloorPlan(
        metadata=MetadataModel(plan_id="plan_1bhk", source_type="synthetic_generated"),
        boundary=[[0, 0], [7, 0], [7, 6.5], [0, 6.5], [0, 0]],
        total_area_m2=45.5,
        rooms=[
            RoomModel(room_id="r1", room_type="living_room", room_name="Living Space", polygon=[[0,0],[4,0],[4,6.5],[0,6.5],[0,0]], area_m2=26.0, centroid=[2,3.25]),
            RoomModel(room_id="r2", room_type="bedroom", room_name="Cozy Bedroom", polygon=[[4,0],[7,0],[7,4.5],[4,4.5],[4,0]], area_m2=13.5, centroid=[5.5,2.25]),
            RoomModel(room_id="r3", room_type="bathroom", room_name="Compact Bath", polygon=[[4,4.5],[7,4.5],[7,6.5],[4,6.5],[4,4.5]], area_m2=6.0, centroid=[5.5,5.5], is_habitable=False)
        ]
    )

    return [p1, p2]


def test_rag_document_generation(sample_plans):
    doc1 = ArchitecturalRAGGenerator.generate_document(sample_plans[0])
    assert doc1["plan_id"] == "plan_3bhk"
    assert doc1["metadata"]["bhk_tag"] == "3BHK"
    assert doc1["metadata"]["bedroom_count"] == 3
    assert "Master Bedroom" in doc1["text"]
    assert "via_door" in doc1["text"]

    doc2 = ArchitecturalRAGGenerator.generate_document(sample_plans[1])
    assert doc2["plan_id"] == "plan_1bhk"
    assert doc2["metadata"]["bhk_tag"] == "1BHK"
    assert doc2["metadata"]["total_area_m2"] == 45.5


def test_vector_store_indexing_and_hybrid_search(sample_plans):
    docs = [ArchitecturalRAGGenerator.generate_document(p) for p in sample_plans]

    vs = ArchitecturalVectorStore()
    vs.add_documents(docs)

    assert vs.index.ntotal == 2

    # Query 1: Search for spacious 3-bedroom home
    res1 = vs.search("spacious 3 bedroom family home with living room", top_k=2)
    assert len(res1) >= 1
    assert res1[0]["plan_id"] == "plan_3bhk"

    # Query 2: Search with BHK filter
    res2 = vs.search("compact home", top_k=2, bhk_filter="1BHK")
    assert len(res2) == 1
    assert res2[0]["plan_id"] == "plan_1bhk"

    # Query 3: Area bounds filter
    res3 = vs.search("family house", top_k=2, min_area_m2=100.0)
    assert len(res3) == 1
    assert res3[0]["plan_id"] == "plan_3bhk"
