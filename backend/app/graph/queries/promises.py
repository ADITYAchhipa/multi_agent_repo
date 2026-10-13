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
  AND e.status='ACTIVE'
  AND (($version='' AND p.current_version_id=v.id) OR ($version<>'' AND v.id=$version))
RETURN p.id,p.current_version_id,p.revision,
       CASE WHEN p.current_version_id=v.id THEN p.current_state ELSE v.status_at_issuance END,
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
RETURN v.id,v.version,v.status_at_issuance,v.receipt_standing,
       v.payload_json,v.payload_hash,v.signature,v.promise_id
ORDER BY v.version,id(e) SKIP $offset LIMIT $limit
"""

REVIEW_STATE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
MATCH (p:Promise {id:$id,tenant_id:$tenant})-[e:HAS_VERSION]->
      (v:PromiseVersion {id:p.current_version_id,tenant_id:$tenant})
WHERE p.access_label='PUBLIC_DEMO' AND v.access_label='PUBLIC_DEMO'
  AND e.tenant_id=$tenant AND e.access_label='PUBLIC_DEMO' AND e.status='ACTIVE'
RETURN s.revision,coalesce(s.audit_sequence,0),s.audit_head_hash,
       p.current_version_id,p.revision,p.current_state,v.payload_json,
       v.payload_hash,v.signature,v.id LIMIT 1
"""

PUBLISH_REVIEW = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
MATCH (p:Promise {id:$promise,tenant_id:$tenant})-[old_edge:HAS_VERSION]->
      (old:PromiseVersion {id:$expected_version,tenant_id:$tenant})
WHERE s.revision=$expected_graph_revision
  AND coalesce(s.audit_sequence,0)=$expected_sequence
  AND coalesce(s.audit_head_hash,'')=coalesce($prev_hash,'')
  AND p.current_version_id=$expected_version AND p.revision=$expected_revision
  AND old_edge.tenant_id=$tenant AND old_edge.status='ACTIVE'
  AND p.access_label='PUBLIC_DEMO' AND old.access_label='PUBLIC_DEMO'
CREATE (new:PromiseVersion {id:$receipt_id,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',promise_id:$promise,version:$version,
  payload_json:$payload_json,payload_hash:$payload_hash,canonicalization:'promiseops-json-v1',
  statement:$statement,deliverable:$deliverable,commitment_class:$commitment_class,
  deadline_iso:$deadline_iso,deadline_text:$deadline_text,
  status_at_issuance:$new_state,receipt_standing:'ACTIVE',price_condition:$price_condition,
  signature:$signature,key_id:$key_id,issued_at:$now})
CREATE (p)-[:HAS_VERSION {id:$version_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'REVIEW',
  provenance_json:$provenance,access_label:$access_label,acl_principals_json:'[]'}]->(new)
CREATE (new)-[:SUPERSEDES {id:$supersedes_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'REVIEW',
  provenance_json:$provenance,access_label:$access_label,acl_principals_json:'[]'}]->(old)
CREATE (new)-[:HAS_EVENT {id:$event_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
  provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(a:AuditEvent {
  id:$audit_id,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',event_type:'PROMISE_REVIEW',
  actor_id:$actor,occurred_at:$now,sequence:$sequence,payload_json:$audit_payload,
  prev_event_hash:$prev_hash,event_hash:$audit_hash,signature:$audit_signature,
  key_id:$key_id,canonicalization:'promiseops-json-v1',request_id:$request_id})
CREATE (o:OperationRun {id:$operation,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',kind:'ANALYSIS',status:'SUCCEEDED',
  phase:'REVIEW_PUBLISHED',requested_by:$actor,request_id:$request_id,
  input_digest:$input_digest,input_json:$input_json,result_json:$result_json,
  errors_json:'[]',attempt_count:1})
CREATE (o)-[:HAS_EVENT {id:$operation_event_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
  provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(a)
SET old.receipt_standing='SUPERSEDED',old.updated_at=$now,
    p.current_version_id=$receipt_id,p.current_state=$new_state,p.revision=p.revision+1,
    p.customer_id=$customer_id,p.project_id=$project_id,
    p.updated_at=$now,s.revision=s.revision+1,s.audit_sequence=$sequence,
    s.audit_head_hash=$audit_hash,s.updated_at=$now
RETURN p.id,new.id,p.revision,p.current_state,a.id
"""

REVIEW_LEDGER = """
MATCH (o:OperationRun {id:$operation,tenant_id:$tenant,requested_by:$actor})
RETURN o.input_digest,o.result_json LIMIT 1
"""

REVIEW_EVIDENCE = """
MATCH (r:SourceRecord {tenant_id:$tenant})-[sv:HAS_SOURCE_VERSION]->
      (v:SourceVersion {tenant_id:$tenant})-[he:HAS_CHUNK]->
      (c:SourceChunk {id:$id,tenant_id:$tenant})
WHERE r.access_label='PUBLIC_DEMO' AND v.access_label='PUBLIC_DEMO'
  AND c.access_label='PUBLIC_DEMO' AND sv.access_label='PUBLIC_DEMO'
  AND he.access_label='PUBLIC_DEMO' AND sv.tenant_id=$tenant AND he.tenant_id=$tenant
  AND sv.status='ACTIVE' AND he.status='ACTIVE'
RETURN r.id,v.id,v.content_hash,v.representation_hash,c.text,c.start_offset,
       c.end_offset,c.chunk_hash,c.created_at,r.source_updated_at LIMIT 1
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

HISTORY_STATE = """
MATCH (p:Promise {id:$id,tenant_id:$tenant})
WHERE p.access_label='PUBLIC_DEMO'
RETURN p.current_version_id,p.revision,p.current_state LIMIT 1
"""

HISTORY_LINKS = """
MATCH (p:Promise {id:$id,tenant_id:$tenant})-[hv:HAS_VERSION]->
      (v:PromiseVersion {tenant_id:$tenant})-[e:SUPERSEDES|HAS_EVENT]->(target)
WHERE p.access_label='PUBLIC_DEMO' AND hv.access_label='PUBLIC_DEMO'
  AND hv.tenant_id=$tenant AND hv.status='ACTIVE' AND v.access_label='PUBLIC_DEMO'
  AND e.access_label='PUBLIC_DEMO' AND e.tenant_id=$tenant AND e.status='ACTIVE'
  AND target.tenant_id=$tenant AND target.access_label='PUBLIC_DEMO'
  AND v.id=$version
  AND ((type(e)='HAS_EVENT' AND target:AuditEvent)
    OR (type(e)='SUPERSEDES' AND target:PromiseVersion))
RETURN v.id,type(e),target.id,target.payload_json,target.event_hash,
       target.event_type LIMIT 3
"""
