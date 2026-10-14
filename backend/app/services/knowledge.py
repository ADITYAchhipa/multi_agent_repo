"""Bounded public-evidence projections, with no arbitrary Cypher or raw properties."""

import re

from fastapi import HTTPException


class KnowledgeService:
    def __init__(self, repository, artifacts):
        self.repository = repository
        self.artifacts = artifacts

    def read(self, tenant, query, **params):
        return self.repository._read(tenant, query, {"tenant": tenant, **params})

    def graph(self, actor, entity_id, depth=2, limit=100):
        roots = self.read(
            actor.tenant_id,
            """
            MATCH (n {id:$id,tenant_id:$tenant,access_label:'PUBLIC_DEMO'})
            RETURN n.id,labels(n)[0] LIMIT 1
        """,
            id=entity_id,
        )
        if not roots:
            raise HTTPException(404)
        nodes = {roots[0][0]: {"id": roots[0][0], "kind": roots[0][1]}}
        edges = {}
        frontier = [entity_id]
        truncated = False
        for _ in range(depth):
            if not frontier:
                break
            rows = self.read(
                actor.tenant_id,
                """
                MATCH (a)-[e]-(b)
                WHERE a.id IN $frontier AND a.tenant_id=$tenant
                  AND b.tenant_id=$tenant AND e.tenant_id=$tenant
                  AND a.access_label='PUBLIC_DEMO' AND b.access_label='PUBLIC_DEMO'
                  AND e.access_label='PUBLIC_DEMO' AND e.status='ACTIVE'
                RETURN a.id,labels(a)[0],b.id,labels(b)[0],e.id,type(e),
                       startNode(e).id,endNode(e).id
                ORDER BY e.id LIMIT $limit
            """,
                frontier=frontier,
                limit=limit + 1,
            )
            next_frontier = []
            for _a, _ak, b, bk, edge, kind, source, target in rows:
                if edge in edges:
                    continue
                if len(edges) >= limit or (b not in nodes and len(nodes) >= limit):
                    truncated = True
                    continue
                if b not in nodes:
                    next_frontier.append(b)
                nodes[b] = {"id": b, "kind": bk}
                edges[edge] = {"id": edge, "type": kind, "source": source, "target": target}
            frontier = next_frontier
        return {
            "nodes": list(nodes.values()),
            "edges": list(edges.values()),
            "truncated": truncated,
        }

    def trace(self, actor, request_id):
        rows = self.read(
            actor.tenant_id,
            """
            MATCH (o:OperationRun {tenant_id:$tenant,request_id:$request})
            WHERE (o.requested_by=$actor OR $admin)
              AND (o.access_label='PUBLIC_DEMO' OR $admin)
            RETURN o.id,o.kind,o.status,o.phase ORDER BY o.id LIMIT 101
        """,
            request=request_id,
            actor=actor.id,
            admin="admin" in actor.roles,
        )
        if not rows:
            raise HTTPException(404)
        return {
            "trace_request_id": request_id,
            "operations": [
                dict(zip(("id", "kind", "status", "phase"), row, strict=True)) for row in rows[:100]
            ],
            "truncated": len(rows) > 100,
        }

    def health(self, actor):
        rows = self.read(
            actor.tenant_id,
            """
            MATCH (s:SourceRecord {tenant_id:$tenant,access_label:'PUBLIC_DEMO'})
            RETURN s.id,s.retention_state,s.parse_status ORDER BY s.id LIMIT 101
        """,
        )
        return {
            "sources": [
                dict(zip(("id", "retention_state", "parse_status"), row, strict=True))
                for row in rows[:100]
            ],
            "truncated": len(rows) > 100,
        }

    def ask(self, actor, question):
        tokens = set(re.findall(r"[a-z0-9]{3,}", question.lower()))
        tokens -= {"the", "and", "what", "when", "where", "does", "with", "will", "that", "are"}
        rows = self.read(
            actor.tenant_id,
            """
            MATCH (s:SourceRecord)-[sv:HAS_SOURCE_VERSION]->(v:SourceVersion)
                  -[hc:HAS_CHUNK]->(c:SourceChunk)
            WHERE s.tenant_id=$tenant AND v.tenant_id=$tenant AND c.tenant_id=$tenant
              AND sv.tenant_id=$tenant AND hc.tenant_id=$tenant
              AND s.access_label='PUBLIC_DEMO' AND v.access_label='PUBLIC_DEMO'
              AND c.access_label='PUBLIC_DEMO' AND sv.access_label='PUBLIC_DEMO'
              AND hc.access_label='PUBLIC_DEMO' AND sv.status='ACTIVE' AND hc.status='ACTIVE'
              AND s.retention_state='ACTIVE' AND v.availability='AVAILABLE'
              AND s.current_version_id=v.id AND c.source_version_id=v.id AND c.source_id=s.id
            RETURN c.id,s.id,v.id,c.text,c.start_offset,c.end_offset,v.representation_hash
            ORDER BY c.id LIMIT 201
        """,
        )
        candidates = []
        for evidence_id, source, version, quote, start, end, representation_hash in rows[:200]:
            score = len(tokens & set(re.findall(r"[a-z0-9]{3,}", quote.lower())))
            if not score:
                continue
            try:
                representation = self.artifacts.read(
                    actor.tenant_id, representation_hash, "representation"
                ).decode("utf-8")
                if representation[start:end] != quote:
                    continue
            except FileNotFoundError, ValueError, UnicodeDecodeError, TypeError:
                continue
            candidates.append(
                (
                    score,
                    {
                        "evidence_ref_id": evidence_id,
                        "source_id": source,
                        "source_version_id": version,
                        "quote": quote[:2000],
                    },
                )
            )
        candidates.sort(key=lambda pair: (-pair[0], pair[1]["evidence_ref_id"]))
        evidence = [item for _, item in candidates[:5]]
        return {
            "answer": "Matching source excerpts:\n" + "\n".join(item["quote"] for item in evidence)
            if evidence
            else None,
            "evidence": evidence,
            "abstained": not evidence,
            "limitations": [
                "Keyword retrieval does not infer an answer.",
                "Search covers at most 200 current public chunks.",
            ],
        }
