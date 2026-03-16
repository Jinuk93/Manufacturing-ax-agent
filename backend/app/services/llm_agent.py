"""
F5 LLM 자율 판단 — F2+F3+F4 결과를 종합하여 조치 권고

입력: 이상 정보(F2) + 비즈니스 컨텍스트(F3) + 지식 검색(F4)
출력: recommendation(STOP/REDUCE/MONITOR) + action_steps + reasoning

LLM_PROVIDER 설정:
- "tbd": 규칙 기반 Mock (LLM 없이)
- "openai": OpenAI GPT-4o-mini API 호출
"""
import json
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


SYSTEM_PROMPT = """당신은 CNC 밀링 머신의 예지보전 AI 에이전트입니다.
센서 이상 감지 결과, 현재 작업 상황, 관련 정비 매뉴얼을 종합하여
현장 기술자가 즉시 실행할 수 있는 조치를 권고합니다.

판단 기준:
- anomaly_score >= 0.8: STOP (즉시 정지) — 심각한 고장 위험
- anomaly_score >= 0.6: REDUCE (감속 운전) — 위험하지만 여유 있음
- anomaly_score < 0.6: MONITOR (모니터링 강화) — 주시하며 가동 유지

반드시 아래 JSON 형식으로 응답하세요:
{
  "recommendation": "STOP" | "REDUCE" | "MONITOR",
  "confidence": 0.0~1.0,
  "reasoning": "판단 근거 상세 설명. 왜 이 판단을 했는지, 다른 대안은 왜 배제했는지.",
  "action_steps": ["구체적 조치 1", "구체적 조치 2", ...],
  "parts_needed": [{"part_id": "P001", "quantity": 1}],
  "predicted_failure_code": "TOOL_WEAR_001",
  "estimated_downtime_min": 30
}

주의: failure_code는 반드시 TOOL_WEAR_001, SPINDLE_OVERHEAT_001, CLAMP_PRESSURE_001, COOLANT_LOW_001 중 하나여야 합니다.
part_id는 반드시 P001~P005 중 하나여야 합니다. 존재하지 않는 코드를 사용하지 마세요."""

USER_PROMPT_TEMPLATE = """현재 상황:

[F2 이상탐지 결과]
- 설비: {equipment_id}
- 시각: {timestamp}
- anomaly_score: {anomaly_score}
- 예측 고장: {predicted_failure_code}
- 신뢰도: {confidence}

[F3 비즈니스 컨텍스트]
- 현재 작업: {work_order_info}
- 최근 정비 이력: {maintenance_info}
- 부품 재고: {inventory_info}

[F4 GraphRAG 검색 결과]
- 필요 부품: {related_parts}
- 관련 매뉴얼: {related_documents}
- 과거 동일 고장 정비: {past_maintenance}

위 정보를 종합하여 조치를 권고하세요."""


def _build_user_prompt(f2: AnomalyResult, f3: ITOTSyncResponse, f4: GraphRAGResponse) -> str:
    """F2+F3+F4 결과를 USER_PROMPT_TEMPLATE에 채움"""
    # 작업 정보
    if f3.latest_work_order:
        wo = f3.latest_work_order
        work_order_info = f"{wo.work_order_id} (priority={wo.priority}, 납기={wo.due_date}, status={wo.status})"
    else:
        work_order_info = f"없음 ({f3.work_order_note or '해당 시각에 작업 없음'})"

    # 정비 이력
    maint_lines = []
    for m in f3.recent_maintenance[:3]:
        maint_lines.append(f"{m.event_id}: {m.event_type}, {m.duration_min}분, 부품={m.parts_used or '없음'}")
    maintenance_info = "\n".join(maint_lines) if maint_lines else "최근 이력 없음"

    # 재고
    inv_lines = []
    for i in f3.inventory:
        status = "⚠️ 부족" if i.stock_quantity <= i.reorder_point else "OK"
        inv_lines.append(f"{i.part_id}({i.part_name}): {i.stock_quantity}개 [{status}]")
    inventory_info = "\n".join(inv_lines)

    # F4 부품
    parts_lines = [f"{p.part_id}({p.part_name}): {p.quantity}개, urgency={p.urgency}" for p in f4.related_parts]
    related_parts = "\n".join(parts_lines) if parts_lines else "없음"

    # F4 문서
    doc_lines = [f"{d.manual_id}: {d.title} (score={d.hybrid_score})" for d in f4.related_documents]
    related_documents = "\n".join(doc_lines) if doc_lines else "없음"

    # F4 과거 정비
    past_lines = [f"{m.event_id}: {m.event_type}, {m.duration_min}분" for m in f4.past_maintenance]
    past_maintenance = "\n".join(past_lines) if past_lines else "없음"

    return USER_PROMPT_TEMPLATE.format(
        equipment_id=f2.equipment_id,
        timestamp=f2.timestamp,
        anomaly_score=f2.anomaly_score,
        predicted_failure_code=f2.predicted_failure_code or "UNKNOWN",
        confidence=f2.confidence or 0.0,
        work_order_info=work_order_info,
        maintenance_info=maintenance_info,
        inventory_info=inventory_info,
        related_parts=related_parts,
        related_documents=related_documents,
        past_maintenance=past_maintenance,
    )


# 유효한 코드 목록 (환각 검증용)
VALID_FAILURE_CODES = {"TOOL_WEAR_001", "SPINDLE_OVERHEAT_001", "CLAMP_PRESSURE_001", "COOLANT_LOW_001"}
VALID_PART_IDS = {"P001", "P002", "P003", "P004", "P005"}


def _validate_llm_response(data: dict) -> list[str]:
    """LLM 응답의 환각 검증 — 존재하지 않는 코드 감지"""
    errors = []
    fc = data.get("predicted_failure_code", "")
    if fc and fc not in VALID_FAILURE_CODES:
        errors.append(f"존재하지 않는 failure_code: {fc}")

    for part in data.get("parts_needed", []):
        pid = part.get("part_id", "")
        if pid and pid not in VALID_PART_IDS:
            errors.append(f"존재하지 않는 part_id: {pid}")

    rec = data.get("recommendation", "")
    if rec not in ("STOP", "REDUCE", "MONITOR"):
        errors.append(f"유효하지 않은 recommendation: {rec}")

    return errors


def _call_llm_api(
    f2: AnomalyResult,
    f3: ITOTSyncResponse,
    f4: GraphRAGResponse,
    max_retries: int = 2,
) -> LLMActionResponse:
    """OpenAI GPT-4o-mini API 호출

    에러 대응 (pipeline-design.md E4, E6):
    - E4 타임아웃/429: 최대 max_retries회 재시도
    - E6 환각: failure_code/part_id 검증 → 실패 시 재시도
    """
    import openai

    client = openai.OpenAI()  # OPENAI_API_KEY 환경변수에서 자동 로드

    user_prompt = _build_user_prompt(f2, f3, f4)

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"F5 LLM 호출 (시도 {attempt + 1}/{max_retries + 1})")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.TEMPERATURE,
                response_format={"type": "json_object"},
                timeout=30,
            )

            raw_text = response.choices[0].message.content
            data = json.loads(raw_text)

            # 환각 검증 (E6)
            validation_errors = _validate_llm_response(data)
            if validation_errors:
                logger.warning(f"F5 환각 감지: {validation_errors}")
                if attempt < max_retries:
                    continue  # 재시도
                else:
                    logger.error("F5 환각 재시도 실패 — 규칙 기반 폴백")
                    return _rule_based_action(f2, f3, f4)

            # 부품 재고 확인 (LLM 응답의 parts_needed에 in_stock 추가)
            parts_needed = []
            for part in data.get("parts_needed", []):
                pid = part.get("part_id", "")
                qty = part.get("quantity", 1)
                inv_item = next((i for i in f3.inventory if i.part_id == pid), None)
                in_stock = inv_item is not None and inv_item.stock_quantity > 0
                parts_needed.append(PartNeeded(part_id=pid, quantity=qty, in_stock=in_stock))

            result = LLMActionResponse(
                equipment_id=f2.equipment_id,
                timestamp=datetime.now(),
                recommendation=data.get("recommendation", "MONITOR"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                action_steps=data.get("action_steps", []),
                parts_needed=parts_needed,
                predicted_failure_code=data.get("predicted_failure_code", f2.predicted_failure_code or "UNKNOWN"),
                estimated_downtime_min=data.get("estimated_downtime_min"),
            )

            logger.info(f"F5 LLM 판단 완료: {result.recommendation} (confidence={result.confidence})")
            return result

        except (openai.APITimeoutError, openai.RateLimitError) as e:
            # E4: 타임아웃/429 → 재시도
            logger.warning(f"F5 LLM API 오류 (시도 {attempt + 1}): {e}")
            if attempt >= max_retries:
                logger.error("F5 LLM 재시도 실패 — 규칙 기반 폴백")
                return _rule_based_action(f2, f3, f4)

        except Exception as e:
            logger.error(f"F5 LLM 예외: {e}")
            return _rule_based_action(f2, f3, f4)
