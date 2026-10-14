# Bounded knowledge read API

Session required. Graph and question answering expose only tenant-owned PUBLIC_DEMO records and edges; administrator does not override this boundary. Projection never returns raw graph property dictionaries.

- GET `/api/graph/{entity_id}?depth=2&limit=100`: depth 1–3, limit 1–200. Returns request_id, nodes [{id,kind}], edges [{id,type,source,target}], truncated. Traverses ACTIVE edges only, at most limit edges/nodes. Absent/inaccessible root: 404.
- GET `/api/trace/{request_id}`: returns request_id, trace_request_id, operations [{id,kind,status,phase}]. Tenant-owned operation records are visible to requester or admin. No matching authorized record: 404. Limit 100 with truncated marker.
- GET `/api/knowledge/health`: returns request_id, sources [{id,retention_state,parse_status}], truncated. Bounded 100-source projection, not a claim of full-corpus health or vendor availability.
- POST `/api/chat`: JSON {question: string 1–2000}. Deterministic extractive search over at most 200 current, available, retained public chunks. Returns request_id, answer (exact quotes only or null), evidence [{evidence_ref_id,source_id,source_version_id,quote}], abstained, limitations. Retained artifact and exact offset verification required before answering. No inference, arithmetic or model-generated assertions; keyword matches do not establish that the question is answered. Answer explicitly labels excerpts. Missing or corrupt artifacts are excluded. Results maximum five chunks, each quote maximum 2000 characters. Retrieval is bounded and incomplete, and explicitly says so.

These APIs are observations, not signed proof verification. Receipt cryptographic integrity remains the dedicated verify endpoint. No conflict resolution, source retirement, action execution, or new fact writes occur in these routes.
