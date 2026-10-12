LIST = """
MATCH (p:Promise)-[e:HAS_VERSION]->(v:PromiseVersion)
WHERE p.tenant_id=$tenant AND v.tenant_id=$tenant AND e.tenant_id=$tenant
  AND p.access_label='PUBLIC_DEMO' AND v.access_label='PUBLIC_DEMO'
  AND e.access_label='PUBLIC_DEMO' AND e.status='ACTIVE'
  AND p.current_version_id=v.id AND p.id>$after
  AND ($status='' OR p.current_state=$status)
  AND ($customer='' OR p.customer_id=$customer)
  AND ($deadline_from='' OR v.deadline_iso >= $deadline_from)
  AND ($deadline_to='' OR v.deadline_iso <= $deadline_to)
RETURN p.id,p.current_version_id,p.revision,p.current_state,
       v.receipt_standing,p.customer_id,p.project_id,v.deliverable,
       v.deadline_iso,v.deadline_text,v.scope_status
ORDER BY p.id LIMIT $limit
"""

DETAIL = """
MATCH (p:Promise {id:$id,tenant_id:$tenant})-[e:HAS_VERSION]->
      (v:PromiseVersion {tenant_id:$tenant})
WHERE p.access_label='PUBLIC_DEMO' AND v.access_label='PUBLIC_DEMO'
  AND e.tenant_id=$tenant AND e.access_label='PUBLIC_DEMO'
  AND e.status='ACTIVE' AND p.current_version_id=v.id
RETURN p.id,p.current_version_id,p.revision,p.current_state,
       v.receipt_standing,p.customer_id,p.project_id,v.deliverable,
       v.deadline_iso,v.deadline_text,v.scope_status,
       v.payload_json,v.payload_hash,v.signature,v.id,e.id
LIMIT 1
"""

VERSIONS = """
MATCH (p:Promise {id:$id,tenant_id:$tenant})-[e:HAS_VERSION]->
      (v:PromiseVersion {tenant_id:$tenant})
WHERE p.access_label='PUBLIC_DEMO' AND v.access_label='PUBLIC_DEMO'
  AND e.tenant_id=$tenant AND e.access_label='PUBLIC_DEMO'
  AND e.status='ACTIVE'
RETURN v.id,v.version,v.status_at_issuance,v.receipt_standing
ORDER BY v.version LIMIT 100
"""

SOURCE_VERSION = """
MATCH (s:SourceRecord {id:$source,tenant_id:$tenant})-
      [e:HAS_SOURCE_VERSION]->(v:SourceVersion {id:$version,tenant_id:$tenant})
WHERE s.access_label='PUBLIC_DEMO' AND e.access_label='PUBLIC_DEMO'
  AND v.access_label='PUBLIC_DEMO' AND e.tenant_id=$tenant
  AND e.status='ACTIVE'
RETURN v.content_hash,v.representation_hash,v.availability LIMIT 1
"""

GRAPH_REVISION = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
RETURN s.revision LIMIT 1
"""

RELATED_ISSUES = """
MATCH (v:PromiseVersion {id:$version,tenant_id:$tenant})-
      [e:IMPLEMENTED_BY|TRACKED_BY]->(i:JiraIssue {tenant_id:$tenant})
WHERE v.access_label='PUBLIC_DEMO' AND e.access_label='PUBLIC_DEMO'
  AND i.access_label='PUBLIC_DEMO' AND e.tenant_id=$tenant
  AND e.status='ACTIVE'
RETURN DISTINCT i.id ORDER BY i.id LIMIT 100
"""

MILESTONES = """
MATCH (v:PromiseVersion {id:$version,tenant_id:$tenant})-
      [e:AFFECTS]->(m:InvoiceMilestone {tenant_id:$tenant})
WHERE v.access_label='PUBLIC_DEMO' AND e.access_label='PUBLIC_DEMO'
  AND m.access_label='PUBLIC_DEMO' AND e.tenant_id=$tenant
  AND e.status='ACTIVE'
RETURN DISTINCT m.id ORDER BY m.id LIMIT 100
"""
