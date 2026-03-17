"""
통합 테스트 — F1→F2→F3→F4→F5 전체 파이프라인

시나리오: W5(2024-02-12) CNC-001에서 COOLANT_LOW_001 이상 감지
- P003 Coolant 재고 = 0 → F5 LLM이 "긴급 발주 필요" 판단해야 함

사용법:
  python test_integration.py
"""
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# .env 로드
from dotenv import load_dotenv
load_dotenv()

from app.services.itot_sync import sync_itot_context
from app.services.graphrag import search_graphrag
from app.services.llm_agent import generate_action
from app.models.schemas import AnomalyResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def test_w5_coolant_scenario():
    """W5 냉각수 재고 0 시나리오 — 전체 파이프라인 테스트"""
    logger.info("=" * 60)
    logger.info("통합 테스트: W5 Coolant 재고=0 시나리오")
    logger.info("=" * 60)

    # ── F2 결과 (시뮬레이션) ──
    logger.info("\n[F2] 이상탐지 결과 (시뮬레이션)")
    f2_result = AnomalyResult(
        timestamp=datetime(2024, 2, 12, 10, 30, 0),  # W5 시점
        equipment_id="CNC-001",
        anomaly_score=0.72,
        is_anomaly=True,
        predicted_failure_code="COOLANT_LOW_001",
        confidence=0.72,
        model_version="IF-v1",
    )
    logger.info(f"  설비: {f2_result.equipment_id}")
    logger.info(f"  시각: {f2_result.timestamp} (W5)")
    logger.info(f"  점수: {f2_result.anomaly_score}")
    logger.info(f"  고장: {f2_result.predicted_failure_code}")

    # ── F3 IT/OT 동기화 ──
    logger.info("\n[F3] IT/OT 동기화 — 실제 DB 조회")
    f3_context = sync_itot_context(
        equipment_id=f2_result.equipment_id,
        timestamp=f2_result.timestamp,
        predicted_failure_code=f2_result.predicted_failure_code,
    )
    logger.info(f"  작업: {f3_context.latest_work_order or f3_context.work_order_note}")
    logger.info(f"  정비 이력: {len(f3_context.recent_maintenance)}건")
    logger.info(f"  재고:")
    for inv in f3_context.inventory:
        status = "⚠️ 부족!" if inv.stock_quantity <= inv.reorder_point else "OK"
        alert = " *** 재고 0 ***" if inv.stock_quantity == 0 else ""
        logger.info(f"    {inv.part_id}({inv.part_name}): {inv.stock_quantity}개 [{status}]{alert}")

    # ── F4 GraphRAG ──
    logger.info("\n[F4] GraphRAG 검색")
    f4_rag = search_graphrag(
        failure_code=f2_result.predicted_failure_code,
        equipment_id=f2_result.equipment_id,
    )
    logger.info(f"  필요 부품: {[(p.part_id, p.part_name) for p in f4_rag.related_parts]}")
    logger.info(f"  관련 매뉴얼: {[(d.manual_id, d.title) for d in f4_rag.related_documents]}")
    logger.info(f"  과거 정비: {[(m.event_id, m.duration_min) for m in f4_rag.past_maintenance]}")

    # ── F5 LLM 자율 판단 ──
    logger.info("\n[F5] LLM 자율 판단")
    f5_action = asyncio.run(generate_action(
        f2_result=f2_result,
        f3_context=f3_context,
        f4_rag_result=f4_rag,
    ))
    logger.info(f"  판단: {f5_action.recommendation}")
    logger.info(f"  신뢰도: {f5_action.confidence}")
    logger.info(f"  고장코드: {f5_action.predicted_failure_code}")
    logger.info(f"  예상 다운타임: {f5_action.estimated_downtime_min}분")
    logger.info(f"  조치 단계:")
    for i, step in enumerate(f5_action.action_steps):
        logger.info(f"    {i+1}. {step}")
    logger.info(f"  필요 부품:")
    for p in f5_action.parts_needed:
        logger.info(f"    {p.part_id}: {p.quantity}개 — {'재고 있음 ✅' if p.in_stock else '재고 없음 ❌ 발주 필요'}")
    logger.info(f"  판단 근거:")
    logger.info(f"    {f5_action.reasoning}")

    # ── 검증 ──
    logger.info("\n" + "=" * 60)
    logger.info("검증 결과")
    logger.info("=" * 60)

    checks = []

    # P003 재고 0 확인
    p003 = next((i for i in f3_context.inventory if i.part_id == "P003"), None)
    p003_zero = p003 is not None and p003.stock_quantity == 0
    checks.append(("P003 재고 = 0", p003_zero))

    # F5가 COOLANT_LOW_001 인식
    fc_match = f5_action.predicted_failure_code == "COOLANT_LOW_001"
    checks.append(("F5 고장코드 = COOLANT_LOW_001", fc_match))

    # F5 부품에서 P003 in_stock=False
    p003_needed = next((p for p in f5_action.parts_needed if p.part_id == "P003"), None)
    p003_out = p003_needed is not None and not p003_needed.in_stock
    checks.append(("P003 in_stock = False (발주 필요)", p003_out))

    # recommendation이 REDUCE 또는 STOP
    rec_ok = f5_action.recommendation in ("STOP", "REDUCE")
    checks.append(("판단 = STOP 또는 REDUCE", rec_ok))

    all_pass = True
    for label, passed in checks:
        icon = "✅" if passed else "❌"
        logger.info(f"  {icon} {label}")
        if not passed:
            all_pass = False

    logger.info(f"\n{'🎉 전체 통과!' if all_pass else '⚠️ 일부 실패'}")
    return all_pass


def test_spindle_overheat_scenario():
    """스핀들 과열 시나리오 — urgent 작업 중 판단"""
    logger.info("\n" + "=" * 60)
    logger.info("통합 테스트: 스핀들 과열 + urgent 작업 시나리오")
    logger.info("=" * 60)

    f2_result = AnomalyResult(
        timestamp=datetime(2024, 1, 29, 8, 1, 30),  # WO-2024-007 진행 중
        equipment_id="CNC-002",
        anomaly_score=0.87,
        is_anomaly=True,
        predicted_failure_code="SPINDLE_OVERHEAT_001",
        confidence=0.87,
        model_version="IF-v1",
    )

    logger.info(f"\n[F2] 점수={f2_result.anomaly_score}, 고장={f2_result.predicted_failure_code}")

    f3_context = sync_itot_context(
        equipment_id=f2_result.equipment_id,
        timestamp=f2_result.timestamp,
    )
    logger.info(f"[F3] 작업: {f3_context.latest_work_order.work_order_id if f3_context.latest_work_order else 'None'}"
                f" (priority={f3_context.latest_work_order.priority if f3_context.latest_work_order else 'N/A'})")

    f4_rag = search_graphrag(
        failure_code=f2_result.predicted_failure_code,
        equipment_id=f2_result.equipment_id,
    )
    logger.info(f"[F4] 부품={[p.part_id for p in f4_rag.related_parts]}, 매뉴얼={[d.manual_id for d in f4_rag.related_documents]}")

    f5_action = asyncio.run(generate_action(f2_result, f3_context, f4_rag))
    logger.info(f"[F5] 판단: {f5_action.recommendation} (confidence={f5_action.confidence})")
    logger.info(f"     근거: {f5_action.reasoning[:200]}...")

    # 검증
    checks = [
        ("P002 필요 부품 포함", any(p.part_id == "P002" for p in f5_action.parts_needed)),
        ("DOC-004 매뉴얼 참조", any(d.manual_id == "DOC-004" for d in f4_rag.related_documents)),
    ]

    all_pass = True
    for label, passed in checks:
        logger.info(f"  {'✅' if passed else '❌'} {label}")
        if not passed:
            all_pass = False
    return all_pass


if __name__ == "__main__":
    result1 = test_w5_coolant_scenario()
    result2 = test_spindle_overheat_scenario()
    logger.info("\n=== 통합 테스트 완료 ===")

    # CI에서 실패 감지 가능하도록 assert + exit code
    assert result1, "W5 Coolant 시나리오 실패!"
    assert result2, "Spindle 시나리오 실패!"
    logger.info("모든 시나리오 통과!")
