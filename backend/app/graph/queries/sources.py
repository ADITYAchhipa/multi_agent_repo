STATE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
OPTIONAL MATCH (r:SourceRecord {id:$source,tenant_id:$tenant})
OPTIONAL MATCH (r)-[sv:HAS_SOURCE_VERSION]->
      (v:SourceVersion {id:r.current_version_id,tenant_id:$tenant})
WHERE sv.tenant_id=$tenant AND sv.status='ACTIVE'
  AND sv.access_label=r.access_label AND v.access_label=r.access_label
  AND v.source_id=r.id
RETURN s.revision,coalesce(s.audit_sequence,0),s.audit_head_hash,
       r.current_version_id,r.content_hash,v.version,
       s.ontology_version,s.policy_version,r.access_label,v.id LIMIT 1
"""

LEDGER = """
MATCH (o:OperationRun {id:$operation,tenant_id:$tenant})
RETURN o.input_digest,o.result_json LIMIT 1
"""

CREATE_SOURCE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
OPTIONAL MATCH (ledger:OperationRun {id:$operation,tenant_id:$tenant})
WITH s, ledger
WHERE ledger IS NULL AND s.revision=$expected_revision
  AND coalesce(s.audit_sequence,0)=$expected_sequence
  AND coalesce(s.audit_head_hash,'')=coalesce($prev_hash,'')
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
CREATE (a:AuditEvent {id:$audit_id,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',event_type:'SOURCE_IMPORTED',
  actor_id:$actor,occurred_at:$now,sequence:$sequence,payload_json:$audit_payload,
  prev_event_hash:$prev_hash,event_hash:$audit_hash,signature:$audit_signature,
  key_id:$key_id,canonicalization:'promiseops-json-v1',request_id:$request_id})
FOREACH (chunk IN $chunks |
  CREATE (c:SourceChunk {id:chunk.id,tenant_id:$tenant,created_at:$now,updated_at:$now,
    access_label:$access_label,acl_principals_json:'[]',source_id:$source,
    source_version_id:$version,text:chunk.text,start_offset:chunk.start,
    end_offset:chunk.end,chunk_hash:chunk.hash})
  CREATE (v)-[:HAS_CHUNK {id:chunk.edge_id,tenant_id:$tenant,created_at:$now,
    status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
    provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(c)
  FOREACH (proposal IN [item IN $proposals WHERE item.chunk_start=chunk.start] |
    CREATE (p:Promise {id:proposal.promise_id,tenant_id:$tenant,created_at:$now,
      updated_at:$now,access_label:$access_label,acl_principals_json:'[]',
      current_version_id:proposal.receipt_id,current_state:'PROPOSED',revision:1})
    CREATE (pv:PromiseVersion {id:proposal.receipt_id,tenant_id:$tenant,created_at:$now,
      updated_at:$now,access_label:$access_label,acl_principals_json:'[]',
      promise_id:proposal.promise_id,version:1,payload_json:proposal.payload_json,
      payload_hash:proposal.payload_hash,canonicalization:'promiseops-json-v1',
      statement:proposal.statement,deliverable:proposal.deliverable,commitment_class:'ambiguous',
      status_at_issuance:'PROPOSED',receipt_standing:'ACTIVE',price_condition:proposal.price_condition,
      deadline_iso:proposal.deadline_iso,deadline_text:proposal.deadline_text,
      signature:proposal.signature,key_id:$key_id,issued_at:$now})
    CREATE (p)-[:HAS_VERSION {id:proposal.version_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
      provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(pv)
    CREATE (c)-[:PROPOSES {id:proposal.proposes_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'EXTRACTED',
      source_id:$source,source_version_id:$version,source_hash:$raw_hash,
      evidence_quote:proposal.statement,start_offset:proposal.start_offset,
      end_offset:proposal.end_offset,extracted_at:$now,model_id:proposal.extraction_profile,
      confidence:'UNKNOWN',
      provenance_json:proposal.provenance,access_label:$access_label,acl_principals_json:'[]'}]->(pv)
    CREATE (pv)-[:SUPPORTED_BY {id:proposal.support_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'EXTRACTED',
      source_id:$source,source_version_id:$version,source_hash:$raw_hash,
      evidence_quote:proposal.statement,start_offset:proposal.start_offset,
      end_offset:proposal.end_offset,extracted_at:$now,model_id:proposal.extraction_profile,
      confidence:'UNKNOWN',
      provenance_json:proposal.provenance,access_label:$access_label,acl_principals_json:'[]'}]->(c)
    CREATE (pv)-[:HAS_EVENT {id:proposal.event_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
      provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(a)
  )
)
CREATE (o:OperationRun {id:$operation,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',kind:'INGESTION',status:'SUCCEEDED',
  phase:'PUBLISHED',requested_by:$actor,request_id:$request_id,input_digest:$input_digest,
  input_json:'{}',result_json:$result_json,errors_json:'[]',attempt_count:1})
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
OPTIONAL MATCH (ledger:OperationRun {id:$operation,tenant_id:$tenant})
WITH s,r,ledger
WHERE ledger IS NULL AND s.revision=$expected_revision
  AND coalesce(s.audit_sequence,0)=$expected_sequence
  AND coalesce(s.audit_head_hash,'')=coalesce($prev_hash,'')
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
CREATE (a:AuditEvent {id:$audit_id,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',event_type:'SOURCE_UPDATED',
  actor_id:$actor,occurred_at:$now,sequence:$sequence,payload_json:$audit_payload,
  prev_event_hash:$prev_hash,event_hash:$audit_hash,signature:$audit_signature,
  key_id:$key_id,canonicalization:'promiseops-json-v1',request_id:$request_id})
FOREACH (chunk IN $chunks |
  CREATE (c:SourceChunk {id:chunk.id,tenant_id:$tenant,created_at:$now,updated_at:$now,
    access_label:$access_label,acl_principals_json:'[]',source_id:$source,
    source_version_id:$version,text:chunk.text,start_offset:chunk.start,
    end_offset:chunk.end,chunk_hash:chunk.hash})
  CREATE (v)-[:HAS_CHUNK {id:chunk.edge_id,tenant_id:$tenant,created_at:$now,
    status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
    provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(c)
  FOREACH (proposal IN [item IN $proposals WHERE item.chunk_start=chunk.start] |
    CREATE (p:Promise {id:proposal.promise_id,tenant_id:$tenant,created_at:$now,
      updated_at:$now,access_label:$access_label,acl_principals_json:'[]',
      current_version_id:proposal.receipt_id,current_state:'PROPOSED',revision:1})
    CREATE (pv:PromiseVersion {id:proposal.receipt_id,tenant_id:$tenant,created_at:$now,
      updated_at:$now,access_label:$access_label,acl_principals_json:'[]',
      promise_id:proposal.promise_id,version:1,payload_json:proposal.payload_json,
      payload_hash:proposal.payload_hash,canonicalization:'promiseops-json-v1',
      statement:proposal.statement,deliverable:proposal.deliverable,commitment_class:'ambiguous',
      status_at_issuance:'PROPOSED',receipt_standing:'ACTIVE',price_condition:proposal.price_condition,
      deadline_iso:proposal.deadline_iso,deadline_text:proposal.deadline_text,
      signature:proposal.signature,key_id:$key_id,issued_at:$now})
    CREATE (p)-[:HAS_VERSION {id:proposal.version_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
      provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(pv)
    CREATE (c)-[:PROPOSES {id:proposal.proposes_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'EXTRACTED',
      source_id:$source,source_version_id:$version,source_hash:$raw_hash,
      evidence_quote:proposal.statement,start_offset:proposal.start_offset,
      end_offset:proposal.end_offset,extracted_at:$now,model_id:proposal.extraction_profile,
      confidence:'UNKNOWN',
      provenance_json:proposal.provenance,access_label:$access_label,acl_principals_json:'[]'}]->(pv)
    CREATE (pv)-[:SUPPORTED_BY {id:proposal.support_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'EXTRACTED',
      source_id:$source,source_version_id:$version,source_hash:$raw_hash,
      evidence_quote:proposal.statement,start_offset:proposal.start_offset,
      end_offset:proposal.end_offset,extracted_at:$now,model_id:proposal.extraction_profile,
      confidence:'UNKNOWN',
      provenance_json:proposal.provenance,access_label:$access_label,acl_principals_json:'[]'}]->(c)
    CREATE (pv)-[:HAS_EVENT {id:proposal.event_edge,tenant_id:$tenant,created_at:$now,
      status:'ACTIVE',valid_from:$now,recorded_at:$now,provenance_kind:'STRUCTURAL',
      provenance_json:'[]',access_label:$access_label,acl_principals_json:'[]'}]->(a)
  )
)
CREATE (o:OperationRun {id:$operation,tenant_id:$tenant,created_at:$now,updated_at:$now,
  access_label:$access_label,acl_principals_json:'[]',kind:'INGESTION',status:'SUCCEEDED',
  phase:'PUBLISHED',requested_by:$actor,request_id:$request_id,input_digest:$input_digest,
  input_json:'{}',result_json:$result_json,errors_json:'[]',attempt_count:1})
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
  AND e.status='ACTIVE' AND v.source_id=r.id
RETURN r.id,r.source_type,r.title,r.current_version_id,r.source_updated_at,
       r.ingested_at,r.content_hash,r.retention_state,r.parse_status,
       v.id,v.version,v.content_hash,v.representation_hash,v.availability,
       v.source_updated_at
ORDER BY v.version,id(e) SKIP $offset LIMIT $limit
"""

OPERATION = """
MATCH (o:OperationRun {id:$operation,tenant_id:$tenant})
WHERE (o.access_label='PUBLIC_DEMO' OR $admin) AND (o.requested_by=$actor OR $admin)
RETURN o.id,o.kind,o.status,o.phase,o.created_at,o.started_at,o.finished_at,
       o.result_json,o.errors_json LIMIT 1
"""

AUDIT_STATE = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
RETURN coalesce(s.audit_sequence,0),s.audit_head_hash,s.revision LIMIT 1
"""

AUDIT_EVENTS = """
MATCH (a:AuditEvent {tenant_id:$tenant})
RETURN a.id,a.sequence,a.payload_json,a.event_hash,a.prev_event_hash,
       a.signature,a.key_id,a.event_type
ORDER BY a.sequence,id(a) SKIP $offset LIMIT $limit
"""

SOURCE_CHUNKS = """
MATCH (r:SourceRecord {id:$source,tenant_id:$tenant})-[sv:HAS_SOURCE_VERSION]->
      (v:SourceVersion {id:$version,tenant_id:$tenant})-[e:HAS_CHUNK]->
      (c:SourceChunk {tenant_id:$tenant})
WHERE sv.tenant_id=$tenant AND e.tenant_id=$tenant
  AND sv.status='ACTIVE' AND e.status='ACTIVE'
  AND ($chunk='' OR c.id=$chunk)
  AND ($admin OR (r.access_label='PUBLIC_DEMO' AND sv.access_label='PUBLIC_DEMO'
    AND v.access_label='PUBLIC_DEMO' AND e.access_label='PUBLIC_DEMO'
    AND c.access_label='PUBLIC_DEMO'))
RETURN c.id,c.text,c.start_offset,c.end_offset,c.chunk_hash,c.access_label,c.created_at
ORDER BY c.start_offset LIMIT 200
"""

EXISTING_PROMISES = """
MATCH (p:Promise {tenant_id:$tenant}) WHERE p.id IN $ids RETURN p.id LIMIT 100
"""
