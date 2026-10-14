READ = """
MATCH (n:Scenario {id:$id,tenant_id:$tenant,actor_id:$actor,access_label:'PUBLIC_DEMO'})
RETURN n.result_json,n.published_revision LIMIT 1
"""
LEDGER = """
MATCH (n:ScenarioRun {id:$id,tenant_id:$tenant,actor_id:$actor})
RETURN n.input_digest,n.result_json LIMIT 1
"""
PUBLISH = """
MATCH (s:GraphState {id:'graph-state',tenant_id:$tenant})
MATCH (p:Promise {id:$promise,tenant_id:$tenant,access_label:'PUBLIC_DEMO'})
WHERE s.revision=$revision AND coalesce(s.audit_sequence,0)=$previous_sequence
 AND coalesce(s.audit_head_hash,'')=coalesce($prev_hash,'')
 AND p.current_version_id=$receipt
CREATE (run:ScenarioRun {id:$run,tenant_id:$tenant,actor_id:$actor,
 input_digest:$digest,result_json:$result_json})
CREATE (a:AuditEvent {id:$audit_id,tenant_id:$tenant,created_at:$now,updated_at:$now,
 access_label:'PUBLIC_DEMO',acl_principals_json:'[]',event_type:'SCENARIO_COMPUTED',
 actor_id:$actor,occurred_at:$now,sequence:$sequence,payload_json:$audit_payload,
 prev_event_hash:$prev_hash,event_hash:$audit_hash,signature:$signature,
 key_id:$key_id,canonicalization:'promiseops-json-v1',request_id:$request_id})
SET s.revision=s.revision+1,s.audit_sequence=$sequence,
 s.audit_head_hash=$audit_hash,s.updated_at=$now
WITH s,p,a,run
UNWIND $scenarios AS item
CREATE (n:Scenario {id:item.id,tenant_id:$tenant,actor_id:$actor,
 access_label:'PUBLIC_DEMO',result_json:item.result_json,published_revision:s.revision,
 created_at:$now,parent_scenario_id:$parent})
CREATE (n)-[:HAS_EVENT {tenant_id:$tenant,access_label:'PUBLIC_DEMO',status:'ACTIVE'}]->(a)
CREATE (n)-[:AFFECTS {tenant_id:$tenant,access_label:'PUBLIC_DEMO',status:'ACTIVE'}]->(p)
RETURN n.id
"""
