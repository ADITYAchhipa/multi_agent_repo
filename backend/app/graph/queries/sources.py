STATE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
OPTIONAL MATCH (r:SourceRecord {id:$source,tenant_id:$tenant})
OPTIONAL MATCH (r)-[:HAS_SOURCE_VERSION]->(v:SourceVersion {id:r.current_version_id})
RETURN s.revision,coalesce(s.audit_sequence,0),s.audit_head_hash,
       r.current_version_id,r.content_hash,v.version,
       s.ontology_version,s.policy_version,r.access_label LIMIT 1
"""

LEDGER = """
MATCH (o:OperationRun {id:$operation,tenant_id:$tenant})
RETURN o.input_digest,o.result_json LIMIT 1
"""

CREATE_SOURCE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
WHERE s.revision=$expected_revision AND coalesce(s.audit_sequence,0)=$expected_sequence
CREATE (r:SourceRecord {id:$source,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',source_type:$source_type,
  title:$title,connector_id:'UPLOAD',external_id:$external_id,retention_state:'ACTIVE',
  parse_status:'PARSED',current_version_id:$version,content_hash:$raw_hash,
  content_hash_algorithm:'SHA-256',ingested_at:$now,content_type:$content_type})
CREATE (v:SourceVersion {id:$version,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',source_id:$source,version:1,
  content_hash:$raw_hash,content_hash_algorithm:'SHA-256',
  representation_hash:$representation_hash,representation_version:'text-v1',
  parser_version:'text-v1',content_type:$content_type,ingested_at:$now,
  original_artifact_id:$raw_hash,representation_artifact_id:$representation_hash,
  parse_status:'PUBLISHED',availability:'AVAILABLE'})
CREATE (r)-[:HAS_SOURCE_VERSION {id:$source_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
  provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(v)
CREATE (o:OperationRun {id:$operation,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',kind:'INGESTION',status:'SUCCEEDED',
  phase:'PUBLISHED',requested_by:$actor,request_id:$request_id,input_digest:$input_digest,
  input_json:'{}',result_json:$result_json,errors_json:'[]',attempt_count:1})
CREATE (a:AuditEvent {id:$audit_id,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',event_type:'SOURCE_IMPORTED',
  actor_id:$actor,occurred_at:$now,sequence:$sequence,payload_json:$audit_payload,
  prev_event_hash:$prev_hash,event_hash:$audit_hash,signature:$audit_signature,
  key_id:$key_id,canonicalization:'promiseops-json-v1',request_id:$request_id})
CREATE (r)-[:HAS_EVENT {id:$audit_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
  provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(a)
SET s.revision=s.revision+1,s.audit_sequence=$sequence,s.audit_head_hash=$audit_hash,
    s.updated_at=$now
RETURN r.id,v.id,o.id,s.revision
"""

UPDATE_SOURCE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
MATCH (r:SourceRecord {id:$source,tenant_id:$tenant})
WHERE s.revision=$expected_revision AND coalesce(s.audit_sequence,0)=$expected_sequence
  AND r.current_version_id=$previous_version AND r.content_hash=$previous_hash
CREATE (v:SourceVersion {id:$version,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',source_id:$source,version:$version_number,
  content_hash:$raw_hash,content_hash_algorithm:'SHA-256',
  representation_hash:$representation_hash,representation_version:'text-v1',
  parser_version:'text-v1',content_type:$content_type,ingested_at:$now,
  original_artifact_id:$raw_hash,representation_artifact_id:$representation_hash,
  parse_status:'PUBLISHED',availability:'AVAILABLE',predecessor_version_id:$previous_version})
CREATE (r)-[:HAS_SOURCE_VERSION {id:$source_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
  provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(v)
CREATE (o:OperationRun {id:$operation,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',kind:'INGESTION',status:'SUCCEEDED',
  phase:'PUBLISHED',requested_by:$actor,request_id:$request_id,input_digest:$input_digest,
  input_json:'{}',result_json:$result_json,errors_json:'[]',attempt_count:1})
CREATE (a:AuditEvent {id:$audit_id,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',event_type:'SOURCE_UPDATED',
  actor_id:$actor,occurred_at:$now,sequence:$sequence,payload_json:$audit_payload,
  prev_event_hash:$prev_hash,event_hash:$audit_hash,signature:$audit_signature,
  key_id:$key_id,canonicalization:'promiseops-json-v1',request_id:$request_id})
CREATE (r)-[:HAS_EVENT {id:$audit_edge,tenant_id:$tenant,created_at:$now,
  status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
  provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(a)
SET r.current_version_id=$version,r.content_hash=$raw_hash,r.updated_at=$now,
    r.ingested_at=$now,r.parse_status='PARSED',r.title=$title,
    r.content_type=$content_type,
    s.revision=s.revision+1,s.audit_sequence=$sequence,s.audit_head_hash=$audit_hash,
    s.updated_at=$now
RETURN r.id,v.id,o.id,s.revision
"""

SOURCE_DETAIL = """
MATCH (r:SourceRecord {id:$source,tenant_id:$tenant})-
      [e:HAS_SOURCE_VERSION]->(v:SourceVersion {tenant_id:$tenant})
WHERE ($admin OR (r.access_label='PUBLIC_DEMO' AND e.access_label='PUBLIC_DEMO'
  AND v.access_label='PUBLIC_DEMO')) AND e.tenant_id=$tenant
RETURN r.id,r.source_type,r.title,r.current_version_id,r.source_updated_at,
       r.ingested_at,r.content_hash,r.retention_state,r.parse_status,
       v.id,v.version,v.content_hash,v.representation_hash,v.availability,
       v.source_updated_at
ORDER BY v.version LIMIT 100
"""

OPERATION = """
MATCH (o:OperationRun {id:$operation,tenant_id:$tenant})
WHERE (o.access_label='PUBLIC_DEMO' OR $admin) AND (o.requested_by=$actor OR $admin)
RETURN o.id,o.kind,o.status,o.phase,o.created_at,o.started_at,o.finished_at,
       o.result_json,o.errors_json LIMIT 1
"""

AUDIT_STATE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
RETURN coalesce(s.audit_sequence,0),s.audit_head_hash LIMIT 1
"""

AUDIT_EVENTS = """
MATCH (a:AuditEvent {tenant_id:$tenant})
RETURN a.id,a.sequence,a.payload_json,a.event_hash,a.prev_event_hash,
       a.signature,a.key_id ORDER BY a.sequence LIMIT 1001
"""
