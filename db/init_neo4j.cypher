// Manufacturing AX Agent — Neo4j 온톨로지 초기화
// ontology-design.md 기준 7종 노드 + 10종 관계
// 실행: cat db/init_neo4j.cypher | docker exec -i ax-neo4j cypher-shell -u neo4j -p ax_password

// ============================================
// 1. 제약 조건 (유니크 + 인덱스)
// ============================================
CREATE CONSTRAINT equipment_pk IF NOT EXISTS FOR (e:Equipment) REQUIRE e.equipment_id IS UNIQUE;
CREATE CONSTRAINT sensor_pk IF NOT EXISTS FOR (s:Sensor) REQUIRE s.sensor_id IS UNIQUE;
CREATE CONSTRAINT failure_pk IF NOT EXISTS FOR (f:FailureCode) REQUIRE f.failure_code IS UNIQUE;
CREATE CONSTRAINT part_pk IF NOT EXISTS FOR (p:Part) REQUIRE p.part_id IS UNIQUE;
CREATE CONSTRAINT document_pk IF NOT EXISTS FOR (d:Document) REQUIRE d.manual_id IS UNIQUE;
CREATE CONSTRAINT workorder_pk IF NOT EXISTS FOR (w:WorkOrder) REQUIRE w.work_order_id IS UNIQUE;
CREATE CONSTRAINT maintenance_pk IF NOT EXISTS FOR (m:MaintenanceAction) REQUIRE m.event_id IS UNIQUE;

// ============================================
// 2. Equipment 노드 (3대)
// ============================================
MERGE (e:Equipment {equipment_id: 'CNC-001'})
SET e.equipment_type = 'CNC Milling Machine', e.status = 'active', e.experiment_range = 'exp01~06';
MERGE (e:Equipment {equipment_id: 'CNC-002'})
SET e.equipment_type = 'CNC Milling Machine', e.status = 'active', e.experiment_range = 'exp07~12';
MERGE (e:Equipment {equipment_id: 'CNC-003'})
SET e.equipment_type = 'CNC Milling Machine', e.status = 'active', e.experiment_range = 'exp13~18';

// ============================================
// 3. FailureCode 노드 (4종)
// ============================================
MERGE (f:FailureCode {failure_code: 'TOOL_WEAR_001'})
SET f.description = '엔드밀 마모로 인한 가공 품질 저하', f.severity = 'critical', f.category = 'tool_wear';
MERGE (f:FailureCode {failure_code: 'SPINDLE_OVERHEAT_001'})
SET f.description = '주축 과열로 인한 베어링 손상 위험', f.severity = 'critical', f.category = 'thermal';
MERGE (f:FailureCode {failure_code: 'CLAMP_PRESSURE_001'})
SET f.description = '클램프 압력 저하로 공작물 고정 불량', f.severity = 'warning', f.category = 'mechanical';
MERGE (f:FailureCode {failure_code: 'COOLANT_LOW_001'})
SET f.description = '절삭유 부족으로 가공면 품질 저하 위험', f.severity = 'warning', f.category = 'fluid';

// ============================================
// 4. Part 노드 (5종) — it-data-synthesis-schema.md 기준
// ============================================
MERGE (p:Part {part_id: 'P001'})
SET p.part_name = 'Endmill 6mm Carbide', p.unit_cost = 45000, p.lead_time_days = 3, p.reorder_point = 5;
MERGE (p:Part {part_id: 'P002'})
SET p.part_name = 'Spindle Bearing Set', p.unit_cost = 280000, p.lead_time_days = 7, p.reorder_point = 2;
MERGE (p:Part {part_id: 'P003'})
SET p.part_name = 'Coolant (Water-Soluble, 20L)', p.unit_cost = 35000, p.lead_time_days = 2, p.reorder_point = 3;
MERGE (p:Part {part_id: 'P004'})
SET p.part_name = 'Clamp Bolt Set', p.unit_cost = 12000, p.lead_time_days = 1, p.reorder_point = 4;
MERGE (p:Part {part_id: 'P005'})
SET p.part_name = 'Air Filter', p.unit_cost = 8000, p.lead_time_days = 1, p.reorder_point = 3;

// ============================================
// 5. Document 노드 (12건) — maintenance_manuals.json 기준
// ============================================
MERGE (d:Document {manual_id: 'DOC-001'}) SET d.title = '엔드밀 공구 교체 절차서', d.document_type = '교체 절차서', d.failure_code = 'TOOL_WEAR_001';
MERGE (d:Document {manual_id: 'DOC-002'}) SET d.title = '공구 마모 점검 체크리스트', d.document_type = '점검 체크리스트', d.failure_code = 'TOOL_WEAR_001';
MERGE (d:Document {manual_id: 'DOC-003'}) SET d.title = '공구 마모 트러블슈팅 가이드', d.document_type = '트러블슈팅 가이드', d.failure_code = 'TOOL_WEAR_001';
MERGE (d:Document {manual_id: 'DOC-004'}) SET d.title = '스핀들 베어링 교체 절차서', d.document_type = '교체 절차서', d.failure_code = 'SPINDLE_OVERHEAT_001';
MERGE (d:Document {manual_id: 'DOC-005'}) SET d.title = '스핀들 과열 점검 체크리스트', d.document_type = '점검 체크리스트', d.failure_code = 'SPINDLE_OVERHEAT_001';
MERGE (d:Document {manual_id: 'DOC-006'}) SET d.title = '스핀들 과열 트러블슈팅 가이드', d.document_type = '트러블슈팅 가이드', d.failure_code = 'SPINDLE_OVERHEAT_001';
MERGE (d:Document {manual_id: 'DOC-007'}) SET d.title = '클램프 볼트 교체 절차서', d.document_type = '교체 절차서', d.failure_code = 'CLAMP_PRESSURE_001';
MERGE (d:Document {manual_id: 'DOC-008'}) SET d.title = '클램프 압력 이상 점검 체크리스트', d.document_type = '점검 체크리스트', d.failure_code = 'CLAMP_PRESSURE_001';
MERGE (d:Document {manual_id: 'DOC-009'}) SET d.title = '클램프 압력 이상 트러블슈팅 가이드', d.document_type = '트러블슈팅 가이드', d.failure_code = 'CLAMP_PRESSURE_001';
MERGE (d:Document {manual_id: 'DOC-010'}) SET d.title = '냉각수 보충 및 필터 교체 절차서', d.document_type = '교체 절차서', d.failure_code = 'COOLANT_LOW_001';
MERGE (d:Document {manual_id: 'DOC-011'}) SET d.title = '냉각수 이상 점검 체크리스트', d.document_type = '점검 체크리스트', d.failure_code = 'COOLANT_LOW_001';
MERGE (d:Document {manual_id: 'DOC-012'}) SET d.title = '냉각수 이상 트러블슈팅 가이드', d.document_type = '트러블슈팅 가이드', d.failure_code = 'COOLANT_LOW_001';

// ============================================
// 6. R4 REQUIRES (FailureCode → Part)
// ============================================
MATCH (f:FailureCode {failure_code: 'TOOL_WEAR_001'}), (p:Part {part_id: 'P001'})
MERGE (f)-[:REQUIRES {quantity: 1, urgency: 'high'}]->(p);
MATCH (f:FailureCode {failure_code: 'SPINDLE_OVERHEAT_001'}), (p:Part {part_id: 'P002'})
MERGE (f)-[:REQUIRES {quantity: 1, urgency: 'high'}]->(p);
MATCH (f:FailureCode {failure_code: 'CLAMP_PRESSURE_001'}), (p:Part {part_id: 'P004'})
MERGE (f)-[:REQUIRES {quantity: 1, urgency: 'medium'}]->(p);
MATCH (f:FailureCode {failure_code: 'COOLANT_LOW_001'}), (p:Part {part_id: 'P003'})
MERGE (f)-[:REQUIRES {quantity: 1, urgency: 'medium'}]->(p);

// ============================================
// 7. R5 DESCRIBED_BY (FailureCode → Document)
// ============================================
MATCH (f:FailureCode {failure_code: 'TOOL_WEAR_001'}), (d:Document) WHERE d.failure_code = 'TOOL_WEAR_001'
MERGE (f)-[:DESCRIBED_BY {relevance_score: 0.95}]->(d);
MATCH (f:FailureCode {failure_code: 'SPINDLE_OVERHEAT_001'}), (d:Document) WHERE d.failure_code = 'SPINDLE_OVERHEAT_001'
MERGE (f)-[:DESCRIBED_BY {relevance_score: 0.95}]->(d);
MATCH (f:FailureCode {failure_code: 'CLAMP_PRESSURE_001'}), (d:Document) WHERE d.failure_code = 'CLAMP_PRESSURE_001'
MERGE (f)-[:DESCRIBED_BY {relevance_score: 0.95}]->(d);
MATCH (f:FailureCode {failure_code: 'COOLANT_LOW_001'}), (d:Document) WHERE d.failure_code = 'COOLANT_LOW_001'
MERGE (f)-[:DESCRIBED_BY {relevance_score: 0.95}]->(d);

// ============================================
// 8. R3 EXPERIENCES (Equipment → FailureCode)
//    maintenance_events에서 추출
// ============================================
// CNC-001: TOOL_WEAR, COOLANT_LOW
MATCH (e:Equipment {equipment_id: 'CNC-001'}), (f:FailureCode {failure_code: 'TOOL_WEAR_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-01-15')}]->(f);
MATCH (e:Equipment {equipment_id: 'CNC-001'}), (f:FailureCode {failure_code: 'COOLANT_LOW_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-01-19')}]->(f);

// CNC-002: SPINDLE_OVERHEAT, TOOL_WEAR, CLAMP_PRESSURE, COOLANT_LOW
MATCH (e:Equipment {equipment_id: 'CNC-002'}), (f:FailureCode {failure_code: 'SPINDLE_OVERHEAT_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-01-29')}]->(f);
MATCH (e:Equipment {equipment_id: 'CNC-002'}), (f:FailureCode {failure_code: 'TOOL_WEAR_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-01-30')}]->(f);
MATCH (e:Equipment {equipment_id: 'CNC-002'}), (f:FailureCode {failure_code: 'CLAMP_PRESSURE_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-02-06')}]->(f);
MATCH (e:Equipment {equipment_id: 'CNC-002'}), (f:FailureCode {failure_code: 'COOLANT_LOW_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-01-26')}]->(f);

// CNC-003: SPINDLE_OVERHEAT, TOOL_WEAR, COOLANT_LOW
MATCH (e:Equipment {equipment_id: 'CNC-003'}), (f:FailureCode {failure_code: 'SPINDLE_OVERHEAT_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-02-15')}]->(f);
MATCH (e:Equipment {equipment_id: 'CNC-003'}), (f:FailureCode {failure_code: 'TOOL_WEAR_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-02-06')}]->(f);
MATCH (e:Equipment {equipment_id: 'CNC-003'}), (f:FailureCode {failure_code: 'COOLANT_LOW_001'})
MERGE (e)-[:EXPERIENCES {first_occurrence: date('2024-02-02')}]->(f);

// ============================================
// 완료 확인
// ============================================
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY label;
