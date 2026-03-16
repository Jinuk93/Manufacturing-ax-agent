"""
F5 LLM 자율 판단 — F2+F3+F4 결과를 종합하여 조치 권고

입력: 이상 정보(F2) + 비즈니스 컨텍스트(F3) + 지식 검색(F4)
출력: recommendation(STOP/REDUCE/MONITOR) + action_steps + reasoning

Phase 3 초기: 규칙 기반 Mock (LLM API 연동 전)
Phase 3 후반: 실제 LLM API 호출로 전환
"""
import logging
from datetime import datetime
from typing import Optional

from app.config import settings
from app.models.schemas import (
    AnomalyResult,
    ITOTSyncResponse,
    GraphRAGResponse,
    LLMActionResponse,
    PartNeeded,
)

logger = logging.getLogger(__name__)


def generate_action(
    f2_result: AnomalyResult,
    f3_context: ITOTSyncResponse,
    f4_rag_result: GraphRAGResponse,
) -> LLMActionResponse:
    """F5 LLM 자율 판단

    Phase 3 초기: 규칙 기반으로 판단 (LLM API 없이)
    Phase 3 후반: 실제 LLM API 호출로 전환 (config.LLM_PROVIDER)
    """
    if settings.LLM_PROVIDER != "tbd":
        # 실제 LLM API 호출 (Phase 3 후반)
        return _call_llm_api(f2_result, f3_context, f4_rag_result)
    else:
        # 규칙 기반 판단 (LLM 없이)
        return _rule_based_action(f2_result, f3_context, f4_rag_result)


def _rule_based_action(
    f2: AnomalyResult,
    f3: ITOTSyncResponse,
    f4: GraphRAGResponse,
) -> LLMActionResponse:
    """규칙 기반 조치 판단 (LLM 연동 전 대체)

    pipeline-design.md 임계치:
    - anomaly_score >= 0.8 → STOP (즉시 정지)
    - anomaly_score >= 0.6 → REDUCE (감속 운전)
    - anomaly_score <  0.6 → MONITOR (모니터링 강화)
    """
    score = f2.anomaly_score
    failure_code = f2.predicted_failure_code or "UNKNOWN"

    # ── 1. 판단 레벨 결정 ──
    if score >= settings.STOP_THRESHOLD:
        recommendation = "STOP"
    elif score >= settings.REDUCE_THRESHOLD:
        recommendation = "REDUCE"
    else:
        recommendation = "MONITOR"

    # ── 2. 비즈니스 맥락 고려 ──
    has_urgent_work = False
    work_info = ""
    if f3.latest_work_order:
        wo = f3.latest_work_order
        has_urgent_work = wo.priority in ("urgent", "critical")
        work_info = f"현재 작업: {wo.work_order_id} (priority={wo.priority}, 납기={wo.due_date})"

        # urgent 작업 중이면 STOP → REDUCE로 한 단계 완화
        if recommendation == "STOP" and has_urgent_work and score < 0.95:
            recommendation = "REDUCE"
            work_info += " → urgent 작업 중이므로 감속 운전으로 완화"

    # ── 3. 부품 재고 확인 ──
    parts_needed = []
    parts_info = []
    for part in f4.related_parts:
        # F3 재고에서 해당 부품 찾기
        inv_item = next(
            (i for i in f3.inventory if i.part_id == part.part_id), None
        )
        in_stock = inv_item is not None and inv_item.stock_quantity > 0
        parts_needed.append(PartNeeded(
            part_id=part.part_id,
            quantity=part.quantity,
            in_stock=in_stock,
        ))
        stock_str = f"{inv_item.stock_quantity}개" if inv_item else "정보 없음"
        parts_info.append(f"{part.part_id}({part.part_name}): 재고 {stock_str} {'✅' if in_stock else '❌ 발주 필요'}")

    # ── 4. 과거 정비 참고 ──
    avg_duration = None
    if f4.past_maintenance:
        durations = [m.duration_min for m in f4.past_maintenance]
        avg_duration = int(sum(durations) / len(durations))

    # ── 5. 조치 단계 생성 ──
    action_steps = _generate_action_steps(
        recommendation, failure_code, f4, has_urgent_work, parts_needed
    )

    # ── 6. 판단 근거 생성 ──
    reasoning = _generate_reasoning(
        score, recommendation, failure_code, work_info,
        parts_info, avg_duration, f4
    )

    logger.info(
        f"F5 판단: {f2.equipment_id} | {recommendation} | "
        f"score={score:.2f}, failure={failure_code}, "
        f"parts={'OK' if all(p.in_stock for p in parts_needed) else 'SHORTAGE'}"
    )

    return LLMActionResponse(
        equipment_id=f2.equipment_id,
        timestamp=datetime.now(),
        recommendation=recommendation,
        confidence=score,
        reasoning=reasoning,
        action_steps=action_steps,
        parts_needed=parts_needed,
        predicted_failure_code=failure_code,
        estimated_downtime_min=avg_duration,
    )


def _generate_action_steps(
    recommendation: str,
    failure_code: str,
    f4: GraphRAGResponse,
    has_urgent_work: bool,
    parts_needed: list[PartNeeded],
) -> list[str]:
    """상황에 맞는 구체적 조치 단계 생성"""
    steps = []

    if recommendation == "STOP":
        steps.append("가공을 즉시 중단하고 안전 정지합니다.")
    elif recommendation == "REDUCE":
        steps.append("feedrate를 50%로 감속하여 운전합니다.")
        if has_urgent_work:
            steps.append("현재 작업을 감속 상태로 완료합니다.")
    else:
        steps.append("현재 가공을 계속하되 모니터링을 강화합니다.")

    # 관련 매뉴얼 참조
    if f4.related_documents:
        doc = f4.related_documents[0]  # 가장 관련도 높은 문서
        steps.append(f"{doc.manual_id} ({doc.title}) 절차를 따릅니다.")

    # 부품 준비
    for part in parts_needed:
        if part.in_stock:
            steps.append(f"{part.part_id} {part.quantity}개 준비합니다. (재고 확인됨)")
        else:
            steps.append(f"{part.part_id} {part.quantity}개 긴급 발주가 필요합니다. (재고 없음)")

    return steps


def _generate_reasoning(
    score: float,
    recommendation: str,
    failure_code: str,
    work_info: str,
    parts_info: list[str],
    avg_duration: Optional[int],
    f4: GraphRAGResponse,
) -> str:
    """판단 근거 텍스트 생성"""
    lines = []
    lines.append(f"anomaly_score {score:.2f}로 {recommendation} 판단.")
    lines.append(f"예측 고장: {failure_code}.")

    if work_info:
        lines.append(work_info)

    if avg_duration:
        lines.append(f"과거 동일 고장 정비 평균 {avg_duration}분 소요.")

    if parts_info:
        lines.append("부품 현황: " + ", ".join(parts_info))

    if f4.related_documents:
        doc_titles = [d.title for d in f4.related_documents[:2]]
        lines.append(f"참조 매뉴얼: {', '.join(doc_titles)}")

    return " ".join(lines)


def _call_llm_api(
    f2: AnomalyResult,
    f3: ITOTSyncResponse,
    f4: GraphRAGResponse,
) -> LLMActionResponse:
    """실제 LLM API 호출 (Phase 3 후반에 구현)

    TODO:
    - 프롬프트 구성 (F2+F3+F4 결과를 구조화)
    - LLM API 호출 (temperature=0.1)
    - JSON 응답 파싱
    - 환각 검증 (failure_code, part_id 존재 확인)
    - 재시도 로직 (E4, E6 에러 대응)
    """
    raise NotImplementedError(
        f"LLM API 연동은 Phase 3 후반에 구현 예정. "
        f"현재 config.LLM_PROVIDER={settings.LLM_PROVIDER}"
    )
