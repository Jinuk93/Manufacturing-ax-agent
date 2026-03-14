"""
Phase 1 EDA 대시보드 — Kaggle CNC Mill Tool Wear
Streamlit으로 18개 실험의 센서 데이터를 한눈에 탐색합니다.
데이터 설명 + 분석 해석 + 인사이트를 함께 제공합니다.

실행: streamlit run dashboards/eda_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CNC Mill EDA Dashboard",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 커스텀 CSS — 세련된 디자인
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; }
    h1 { color: #e2e8f0 !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    h2, h3 { color: #cbd5e1 !important; font-weight: 600 !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important; font-size: 0.85rem !important;
        font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        color: #f1f5f9 !important; font-size: 1.8rem !important; font-weight: 700 !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stRadio > div { gap: 2px; }
    [data-testid="stSidebar"] .stRadio label {
        background: transparent; border-radius: 8px; padding: 8px 12px;
        transition: all 0.2s ease; color: #94a3b8 !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: #1e293b; color: #e2e8f0 !important;
    }
    [data-testid="stDataFrame"] {
        border-radius: 10px; overflow: hidden; border: 1px solid #334155;
    }
    hr { border-color: #334155 !important; opacity: 0.5; }
    .streamlit-expanderHeader {
        background: #1e293b !important; border-radius: 8px; color: #e2e8f0 !important;
    }
    .stSelectbox > div > div, .stMultiSelect > div > div { border-radius: 8px !important; }
    .stAlert { border-radius: 10px !important; }
    [data-testid="stPlotlyChart"] {
        border-radius: 12px; overflow: hidden; border: 1px solid #1e293b;
    }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }

    /* 인포 카드 스타일 */
    .info-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 12px;
        padding: 20px; margin: 8px 0;
    }
    .info-card h4 { color: #60a5fa !important; margin: 0 0 8px 0; font-size: 1rem; }
    .info-card p { color: #94a3b8; margin: 0; font-size: 0.9rem; line-height: 1.6; }
    .insight-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #f59e0b; border-radius: 8px;
        padding: 16px 20px; margin: 12px 0;
    }
    .insight-box p { color: #e2e8f0; margin: 0; font-size: 0.9rem; line-height: 1.6; }
    .sensor-badge {
        display: inline-block; background: #1e293b; border: 1px solid #475569;
        border-radius: 6px; padding: 2px 8px; margin: 2px;
        font-size: 0.8rem; color: #cbd5e1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# 센서 사전 (센서가 뭔지 설명)
# ─────────────────────────────────────────────
SENSOR_DESC = {
    "ActualPosition": ("실제 위치 (mm)", "CNC 컨트롤러가 측정한 축의 현재 물리적 위치. CommandPosition과의 차이가 크면 위치 오차(서보 지연) 발생."),
    "CommandPosition": ("명령 위치 (mm)", "G-code에서 CNC에 지시한 목표 위치. ActualPosition과 비교하여 추종 오차를 확인."),
    "ActualVelocity": ("실제 속도 (mm/s)", "축이 실제로 이동하는 속도. 급격한 변동은 진동이나 기계적 문제를 암시."),
    "CommandVelocity": ("명령 속도 (mm/s)", "G-code가 지시한 목표 이동 속도. ActualVelocity와의 차이가 클수록 제어 지연."),
    "ActualAcceleration": ("실제 가속도 (mm/s²)", "축의 가속/감속 정도. 급격한 가속도는 공구나 워크피스에 충격을 줄 수 있음."),
    "CommandAcceleration": ("명령 가속도 (mm/s²)", "컨트롤러가 계획한 가속도 프로파일. 실제 가속도와의 차이로 관성 보상 성능 평가."),
    "CurrentFeedback": ("모터 전류 피드백 (A)", "서보 모터에 흐르는 전류. 부하(절삭력)에 비례하므로 마모/이상 감지의 핵심 지표."),
    "DCBusVoltage": ("DC 버스 전압 (V)", "서보 드라이브의 전원 전압. 안정적이어야 하며, 급격한 변동은 전원 품질 문제."),
    "OutputCurrent": ("출력 전류 (A)", "서보 드라이브가 모터로 출력하는 전류. CurrentFeedback과 함께 모터 부하 분석에 활용."),
    "OutputVoltage": ("출력 전압 (V)", "서보 드라이브가 모터에 인가하는 전압. 속도 제어에 직접 관련."),
    "OutputPower": ("출력 전력 (W)", "모터가 소비하는 전력 (전압×전류). 절삭 에너지 소비량으로, 마모 시 증가하는 경향."),
    "SystemInertia": ("시스템 관성", "축 구동계의 관성 모멘트 추정값. 이 데이터셋에서는 상수(변화 없음)로 제거 대상."),
    "CURRENT_PROGRAM_NUMBER": ("현재 프로그램 번호", "CNC가 실행 중인 NC 프로그램 번호. 공정 식별에 활용 가능."),
}

AXIS_DESC = {
    "X축": ("좌우 이동 (테이블)", "워크피스를 좌우로 이동시키는 축. 밀링에서 가장 긴 이동 거리를 담당하며, 평면 절삭 시 주요 이송축."),
    "Y축": ("전후 이동 (테이블)", "워크피스를 전후로 이동시키는 축. X축과 함께 2D 평면 윤곽 가공을 수행."),
    "Z축": ("상하 이동 (주축두)", "주축(스핀들)을 상하로 이동시키는 축. 절삭 깊이(depth of cut)를 결정하며, 공구-워크 접촉력에 직접 영향."),
    "S축 (주축)": ("스핀들 회전", "공구를 회전시키는 주축(Spindle). RPM(분당 회전수)으로 제어하며, 절삭 성능의 핵심. 마모 시 전류/전력이 증가하는 경향."),
    "M1 (기타)": ("기계 레벨 정보", "축 단위가 아닌 기계 전체 레벨의 데이터. 현재 실행 중인 NC 프로그램 번호 등."),
}

META_DESC = {
    "material": ("소재 종류", "가공 대상 소재. 이 데이터셋은 wax(왁스) 단일 소재. 실제 현장에서는 철강, 알루미늄, 티타늄 등 다양."),
    "feedrate": ("이송속도 (mm/min)", "공구가 워크피스를 깎아나가는 속도. 높을수록 빠른 가공이지만 공구 마모가 빨라짐."),
    "clamp_pressure": ("클램프 압력 (bar)", "워크피스를 고정하는 지그의 압력. 낮으면 진동/떨림, 너무 높으면 워크피스 변형."),
    "tool_condition": ("공구 상태", "worn(마모됨) 또는 unworn(정상). 이 프로젝트의 예측 대상(Target Label)."),
    "Machining_Process": ("가공 공정 단계", "Prep → Layer 1~3 Roughing/Finishing → End. 각 단계마다 절삭 조건과 센서 패턴이 다름."),
}

def get_sensor_short_name(col_name):
    """X1_ActualPosition → ActualPosition"""
    parts = col_name.split("_", 1)
    return parts[1] if len(parts) > 1 else col_name

def get_sensor_desc(col_name):
    """센서 컬럼명으로 설명을 가져옵니다."""
    short = get_sensor_short_name(col_name)
    if short in SENSOR_DESC:
        return SENSOR_DESC[short]
    return (col_name, "설명 없음")


# ─────────────────────────────────────────────
# 데이터 로딩 (캐싱)
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    """모든 실험 데이터를 로딩하고 전처리합니다."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "raw" / "kaggle-cnc-mill"

    train_df = pd.read_csv(data_dir / "train.csv")
    train_df = train_df.rename(columns={"No": "experiment_no"})
    train_df["experiment_id"] = train_df["experiment_no"].map(lambda v: f"experiment_{v:02d}")
    train_df["equipment_id"] = train_df["experiment_no"].map(lambda v: f"CNC-{v:03d}")

    all_experiments = []
    for path in sorted(data_dir.glob("experiment_*.csv")):
        exp_id = path.stem
        exp_no = int(exp_id.split("_")[-1])
        df = pd.read_csv(path)
        df["experiment_id"] = exp_id
        df["equipment_id"] = f"CNC-{exp_no:03d}"
        df["experiment_no"] = exp_no
        df["sequence"] = range(len(df))
        df["timestamp"] = pd.Timestamp("2026-01-01") + pd.to_timedelta(df["sequence"] * 100, unit="ms")
        row = train_df[train_df["experiment_no"] == exp_no]
        if not row.empty:
            df["tool_condition"] = row.iloc[0]["tool_condition"]
            df["material"] = row.iloc[0]["material"]
            df["feedrate"] = row.iloc[0]["feedrate"]
            df["clamp_pressure"] = row.iloc[0]["clamp_pressure"]
        all_experiments.append(df)

    full_df = pd.concat(all_experiments, ignore_index=True)

    constant_cols = [
        c for c in full_df.columns
        if full_df[c].nunique(dropna=False) == 1
        and c not in ("experiment_id", "equipment_id", "tool_condition", "material")
    ]
    zero_cols = [
        c for c in full_df.select_dtypes(include=[np.number]).columns
        if full_df[c].fillna(0).eq(0).all()
    ]

    meta_cols = [
        "experiment_id", "equipment_id", "experiment_no", "sequence", "timestamp",
        "Machining_Process", "tool_condition", "material", "feedrate", "clamp_pressure",
    ]
    sensor_cols = [c for c in full_df.columns if c not in meta_cols and c not in constant_cols]

    return full_df, train_df, sensor_cols, constant_cols, zero_cols, meta_cols


full_df, train_df, sensor_cols, constant_cols, zero_cols, meta_cols = load_data()

# ─────────────────────────────────────────────
# Plotly 차트 공통 레이아웃 (다크 테마)
# ─────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#1e293b",
    font=dict(color="#cbd5e1", size=12),
    title_font=dict(color="#e2e8f0", size=15),
    xaxis=dict(gridcolor="#334155", zerolinecolor="#475569"),
    yaxis=dict(gridcolor="#334155", zerolinecolor="#475569"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
    coloraxis_colorbar=dict(tickfont=dict(color="#94a3b8")),
)

# 센서를 축별로 그룹화
sensor_groups = {}
for col in sensor_cols:
    if col.startswith("X1_"):
        sensor_groups.setdefault("X축", []).append(col)
    elif col.startswith("Y1_"):
        sensor_groups.setdefault("Y축", []).append(col)
    elif col.startswith("Z1_"):
        sensor_groups.setdefault("Z축", []).append(col)
    elif col.startswith("S1_"):
        sensor_groups.setdefault("S축 (주축)", []).append(col)
    elif col.startswith("M1_"):
        sensor_groups.setdefault("M1 (기타)", []).append(col)
    else:
        sensor_groups.setdefault("기타", []).append(col)

# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
st.sidebar.title("CNC Mill EDA")
st.sidebar.markdown("**Kaggle CNC Mill Tool Wear**")
st.sidebar.markdown("18개 실험 · 42개 유효 센서")
st.sidebar.divider()

tab_names = [
    "데이터 개요",
    "센서 분포",
    "시계열 패턴",
    "Worn vs Unworn",
    "상관관계",
    "공정 단계",
]
selected_tab = st.sidebar.radio("탐색 영역", tab_names, index=0)

# ═════════════════════════════════════════════
# 탭 1: 데이터 개요 (대폭 개선)
# ═════════════════════════════════════════════
if selected_tab == tab_names[0]:
    st.title("데이터 개요")
    st.markdown("이 데이터는 **어디서 나온 어떤 데이터**이고, **각 항목이 무슨 뜻**인지 설명합니다.")

    # ── KPI 카드 ──
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("총 실험 수", f"{train_df.shape[0]}개")
    col2.metric("총 데이터 행", f"{full_df.shape[0]:,}")
    col3.metric("전체 컬럼", f"{full_df.shape[1] - len(meta_cols)}개")
    col4.metric("유효 센서", f"{len(sensor_cols)}개")
    col5.metric("제거 대상", f"{len(constant_cols)}개")

    st.divider()

    # ── 섹션 1: 데이터 출처 Top-Down ──
    st.subheader("데이터 출처 -- 이 데이터는 어디서 오나?")

    st.markdown("""
    <div class="info-card">
    <h4>실제 CNC 밀링 머신 실험 데이터 (Kaggle)</h4>
    <p>
    이 데이터셋은 <b>미시건 대학교(University of Michigan)</b>에서 수행한 CNC 밀링 실험에서 수집되었습니다.<br>
    왁스(wax) 소재를 CNC 밀링 머신으로 가공하면서, <b>CNC 컨트롤러(SCADA 레벨)</b>가 100ms 간격으로 센서값을 기록한 것입니다.<br><br>
    실제 제조 현장의 데이터 흐름으로 보면:
    </p>
    </div>
    """, unsafe_allow_html=True)

    col_src1, col_src2, col_src3 = st.columns(3)

    with col_src1:
        st.markdown("""
        <div class="info-card">
        <h4>SCADA / CNC 컨트롤러</h4>
        <p>
        <b>이 데이터셋의 주요 출처</b><br><br>
        · X, Y, Z축 서보 모터 센서<br>
        · S축 (스핀들) 회전 센서<br>
        · 위치/속도/가속도/전류/전압/전력<br>
        · 100ms 주기로 실시간 수집<br><br>
        → <b>48개 컬럼</b> (센서 데이터)
        </p>
        </div>
        """, unsafe_allow_html=True)

    with col_src2:
        st.markdown("""
        <div class="info-card">
        <h4>MES (실험 메타데이터)</h4>
        <p>
        <b>train.csv에 해당</b><br><br>
        · 실험 번호 (experiment_no)<br>
        · 소재 종류 (material: wax)<br>
        · 이송속도 (feedrate)<br>
        · 클램프 압력 (clamp_pressure)<br>
        · 가공 완료 여부<br><br>
        → <b>실험 조건 + 결과 라벨</b>
        </p>
        </div>
        """, unsafe_allow_html=True)

    with col_src3:
        st.markdown("""
        <div class="info-card">
        <h4>품질 검사 (라벨)</h4>
        <p>
        <b>실험 후 판정 결과</b><br><br>
        · tool_condition: worn / unworn<br>
        · 가공 후 공구 상태를 검사관이 판정<br>
        · 이것이 우리의 <b>예측 대상(Target)</b><br><br>
        → 센서 패턴만 보고<br>
        "이 공구 마모됐나?" 예측하는 것이 목표
        </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── 섹션 2: MES 메타데이터 설명 ──
    st.subheader("실험 조건 (MES 레벨) -- 각 항목이 뭔지")

    meta_explain_cols = st.columns(4)
    for i, (key, (title, desc)) in enumerate(META_DESC.items()):
        with meta_explain_cols[i % 4]:
            st.markdown(f"""
            <div class="info-card">
            <h4>{title}</h4>
            <p><code>{key}</code><br>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # 실험 메타데이터 테이블
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("**실험별 메타데이터 테이블**")
        meta_display = train_df[
            ["experiment_id", "equipment_id", "material", "feedrate",
             "clamp_pressure", "tool_condition", "machining_finalized"]
        ].copy()
        meta_display.columns = ["실험 ID", "설비 ID", "소재", "이송속도", "클램프 압력", "공구 상태", "가공 완료"]

        st.dataframe(
            meta_display.style.apply(
                lambda row: [
                    "background-color: #7f1d1d; color: #fca5a5"
                    if row["공구 상태"] == "worn"
                    else "background-color: #14532d; color: #86efac"
                ] * len(row),
                axis=1,
            ),
            width="stretch",
            height=350,
        )

    with col_right:
        fig_label = px.pie(
            train_df, names="tool_condition", color="tool_condition",
            color_discrete_map={"worn": "#ef4444", "unworn": "#22c55e"},
            title="공구 상태 분포",
        )
        fig_label.update_layout(**CHART_LAYOUT, height=180, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_label, width="stretch")

        exp_sizes = full_df.groupby(["experiment_id", "tool_condition"]).size().reset_index(name="rows")
        fig_sizes = px.bar(
            exp_sizes, x="experiment_id", y="rows", color="tool_condition",
            color_discrete_map={"worn": "#ef4444", "unworn": "#22c55e"},
            title="실험별 데이터 크기 (행 수)",
        )
        fig_sizes.update_layout(
            **CHART_LAYOUT, height=180, margin=dict(t=30, b=0, l=0, r=0),
            xaxis_tickangle=-45, showlegend=False,
        )
        st.plotly_chart(fig_sizes, width="stretch")

    st.markdown("""
    <div class="insight-box">
    <p>
    [TIP] <b>해석 포인트:</b> worn 10개 vs unworn 8개로 약간 불균형이지만 심하지 않음.
    실험별 행 수(462~2332)가 다른 이유는 가공 시간이 다르기 때문.
    짧은 실험(04, 05, 07, 08)은 가공이 중단(<code>machining_finalized=no</code>)된 경우일 수 있으므로 확인 필요.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 섹션 3: 센서 데이터 구조 (SCADA 레벨) ──
    st.subheader("[SCADA] 센서 데이터 구조 (SCADA 레벨) — 42개 센서가 뭔지")

    st.markdown("""
    CNC 밀링 머신의 **4개 축(X, Y, Z, S)** 에서 각각 **10~11개 센서**가 데이터를 수집합니다.
    각 센서의 역할을 이해하면, 어떤 센서가 마모 감지에 유용할지 판단할 수 있습니다.
    """)

    # 축별 설명 + 센서 목록
    for group_name in ["X축", "Y축", "Z축", "S축 (주축)", "M1 (기타)"]:
        if group_name not in sensor_groups:
            continue
        cols = sensor_groups[group_name]
        axis_title, axis_desc = AXIS_DESC.get(group_name, (group_name, ""))

        with st.expander(f"**{group_name}** — {axis_title} ({len(cols)}개 센서)", expanded=(group_name == "X축")):
            st.markdown(f"*{axis_desc}*")
            st.markdown("")

            # 센서 목록을 테이블로
            sensor_info_rows = []
            for c in cols:
                short = get_sensor_short_name(c)
                title, desc = SENSOR_DESC.get(short, (c, ""))
                val_mean = full_df[c].mean()
                val_std = full_df[c].std()
                sensor_info_rows.append({
                    "센서 컬럼": c,
                    "의미": title,
                    "평균": f"{val_mean:.2f}",
                    "표준편차": f"{val_std:.2f}",
                    "설명": desc,
                })
            sensor_info_df = pd.DataFrame(sensor_info_rows)
            st.dataframe(sensor_info_df, width="stretch", hide_index=True)

    st.divider()

    # ── 섹션 4: 센서 관계도 ──
    st.subheader("- 센서 간 관계 — 어떤 센서끼리 조화를 이루나?")

    st.markdown("""
    <div class="info-card">
    <h4>센서 간 핵심 관계</h4>
    <p>
    <b>① Command vs Actual (명령 vs 실제)</b><br>
    · Position, Velocity, Acceleration 각각에 Command(목표)와 Actual(실제)가 쌍으로 존재<br>
    · 두 값의 차이 = <b>추종 오차(Following Error)</b> → 기계 상태/마모 판단의 핵심 지표<br>
    · 정상이면 거의 동일, 마모/이상 시 차이 증가<br><br>
    <b>② 전류/전압/전력 (부하 3형제)</b><br>
    · CurrentFeedback ≈ OutputCurrent (모터에 흐르는 전류)<br>
    · OutputPower = OutputVoltage × OutputCurrent (전력 = 전압 × 전류)<br>
    · 절삭 부하가 클수록 전류/전력 증가 → <b>마모된 공구는 더 많은 전력 소비</b><br><br>
    <b>③ 축 간 관계</b><br>
    · X-Y축은 평면 이동을 함께 수행 → 동시에 값이 변하는 구간이 많음<br>
    · Z축은 절삭 깊이 → 다른 축과 독립적으로 움직이는 경우가 많음<br>
    · S축(주축)은 항상 회전 → 절삭 중 전류/전력이 핵심
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 섹션 5: 제거 대상 컬럼 ──
    st.subheader("[X] 제거 대상 컬럼")
    for c in constant_cols:
        short = get_sensor_short_name(c)
        title, desc = SENSOR_DESC.get(short, (c, ""))
        val = full_df[c].iloc[0] if len(full_df) > 0 else "N/A"
        reason = "전체 0값 (센서 미연결)" if c in zero_cols else f"상수값 고정 ({val})"
        st.markdown(f"- `{c}` — **{title}** → {reason}")

    st.info(f"원본 48컬럼 → 상수/0값 {len(constant_cols)}개 제거 → **유효 {len(sensor_cols)}개**")


# ═════════════════════════════════════════════
# 탭 2: 센서 분포
# ═════════════════════════════════════════════
elif selected_tab == tab_names[1]:
    st.title("- 센서 분포")
    st.markdown("각 센서의 값 분포를 확인하고, **이 분포가 의미하는 바**를 해석합니다.")

    # 축 그룹 선택
    selected_group = st.selectbox("축 그룹 선택", list(sensor_groups.keys()))
    group_cols = sensor_groups[selected_group]

    # 선택한 축의 설명
    axis_title, axis_desc = AXIS_DESC.get(selected_group, (selected_group, ""))
    st.markdown(f"""
    <div class="info-card">
    <h4>{selected_group} — {axis_title}</h4>
    <p>{axis_desc}</p>
    </div>
    """, unsafe_allow_html=True)

    # 분포 타입 선택
    dist_type = st.radio("시각화 방식", ["Box Plot", "Histogram", "Violin Plot"], horizontal=True)

    st.subheader(f"{selected_group} — 전체 실험 통합 분포")

    if dist_type == "Box Plot":
        fig = go.Figure()
        for col in group_cols:
            fig.add_trace(go.Box(y=full_df[col], name=col.replace("_", " "), boxmean=True))
        fig.update_layout(**CHART_LAYOUT, height=500, showlegend=False)
        st.plotly_chart(fig, width="stretch")
    elif dist_type == "Histogram":
        n_cols = min(3, len(group_cols))
        n_rows = (len(group_cols) + n_cols - 1) // n_cols
        fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=group_cols)
        for i, col in enumerate(group_cols):
            r, c = i // n_cols + 1, i % n_cols + 1
            fig.add_trace(
                go.Histogram(x=full_df[col], nbinsx=50, name=col, showlegend=False),
                row=r, col=c,
            )
        fig.update_layout(**CHART_LAYOUT, height=300 * n_rows)
        st.plotly_chart(fig, width="stretch")
    else:
        fig = go.Figure()
        for col in group_cols:
            fig.add_trace(go.Violin(y=full_df[col], name=col.replace("_", " "), box_visible=True))
        fig.update_layout(**CHART_LAYOUT, height=500, showlegend=False)
        st.plotly_chart(fig, width="stretch")

    # 센서별 설명 + 통계
    st.subheader("센서별 상세 설명 + 기초 통계량")

    stats = full_df[group_cols].describe().T
    stats["missing"] = full_df[group_cols].isnull().sum()
    stats["missing%"] = (stats["missing"] / len(full_df) * 100).round(2)

    for col in group_cols:
        short = get_sensor_short_name(col)
        title, desc = SENSOR_DESC.get(short, (col, ""))
        s = stats.loc[col]

        with st.expander(f"**{col}** — {title}"):
            st.markdown(f"*{desc}*")
            col_s1, col_s2 = st.columns([1, 2])
            with col_s1:
                st.markdown(f"""
                | 지표 | 값 |
                |------|-----|
                | 평균 | {s['mean']:.4f} |
                | 표준편차 | {s['std']:.4f} |
                | 최솟값 | {s['min']:.4f} |
                | 25% | {s['25%']:.4f} |
                | 50% (중앙) | {s['50%']:.4f} |
                | 75% | {s['75%']:.4f} |
                | 최댓값 | {s['max']:.4f} |
                | 결측 | {int(s['missing'])}개 ({s['missing%']:.1f}%) |
                """)
            with col_s2:
                # 해석 자동 생성
                skew_val = full_df[col].skew()
                kurt_val = full_df[col].kurtosis()
                cv = (s['std'] / abs(s['mean']) * 100) if abs(s['mean']) > 1e-10 else float('inf')

                interpretations = []
                if s['missing%'] == 0:
                    interpretations.append("[OK] 결측값 없음 — 전처리 불필요")
                else:
                    interpretations.append(f"[WARN] 결측 {s['missing%']:.1f}% — 보간 또는 제거 필요")

                if cv < 10:
                    interpretations.append(f"- 변동계수(CV) {cv:.1f}% — 매우 안정적 (변화 적음)")
                elif cv < 50:
                    interpretations.append(f"- 변동계수(CV) {cv:.1f}% — 적당한 변동 (분석에 유용)")
                else:
                    interpretations.append(f"- 변동계수(CV) {cv:.1f}% — 변동이 큼 (이상치 확인 필요)")

                if abs(skew_val) < 0.5:
                    interpretations.append(f"- 왜도 {skew_val:.2f} — 대칭 분포 (정규분포에 가까움)")
                elif skew_val > 0:
                    interpretations.append(f"- 왜도 {skew_val:.2f} — 오른쪽 꼬리 (고값 이상치 가능)")
                else:
                    interpretations.append(f"- 왜도 {skew_val:.2f} — 왼쪽 꼬리 (저값 이상치 가능)")

                if "Position" in short:
                    interpretations.append("- 위치 센서 — Command와의 차이(추종오차)가 마모 지표")
                elif "Current" in short or "Power" in short:
                    interpretations.append("- 부하 관련 — 마모 시 증가하는 경향, 이상탐지 유력 후보")
                elif "Velocity" in short:
                    interpretations.append("- 속도 센서 — 급격한 변동은 진동/채터링 가능성")

                st.markdown("**자동 해석:**")
                for interp in interpretations:
                    st.markdown(f"- {interp}")


# ═════════════════════════════════════════════
# 탭 3: 시계열 패턴
# ═════════════════════════════════════════════
elif selected_tab == tab_names[2]:
    st.title("- 시계열 패턴")
    st.markdown("실험별 센서의 시간에 따른 변화를 확인합니다.")

    st.markdown("""
    <div class="insight-box">
    <p>
    [TIP] <b>보는 법:</b> 시계열에서 주목할 것은 ① 공정 단계별 패턴 변화 (계단식 변화가 정상)
    ② 비정상적 진동이나 스파이크 ③ worn vs unworn 실험을 번갈아 보며 차이 관찰.
    센서를 선택할 때, Position + CurrentFeedback 조합이 마모 탐지에 가장 유용합니다.
    </p>
    </div>
    """, unsafe_allow_html=True)

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        selected_exp = st.selectbox(
            "실험 선택", sorted(full_df["experiment_id"].unique()), index=0,
        )
    with col_sel2:
        available_sensors = [c for c in sensor_cols if c != "M1_CURRENT_PROGRAM_NUMBER"]
        selected_sensors = st.multiselect(
            "센서 선택 (최대 4개)", available_sensors,
            default=available_sensors[:4], max_selections=4,
        )

    exp_data = full_df[full_df["experiment_id"] == selected_exp]
    tool_cond = exp_data["tool_condition"].iloc[0]
    status_color = "[WORN]" if tool_cond == "worn" else "[OK]"

    st.markdown(
        f"**{selected_exp}** ({exp_data['equipment_id'].iloc[0]}) — "
        f"{status_color} {tool_cond} · {len(exp_data):,}행 · "
        f"{exp_data['material'].iloc[0]} · feedrate={exp_data['feedrate'].iloc[0]}"
    )

    # 선택된 센서 설명
    if selected_sensors:
        with st.expander("선택한 센서 설명 보기"):
            for sensor in selected_sensors:
                title, desc = get_sensor_desc(sensor)
                st.markdown(f"- **{sensor}** ({title}): {desc}")

        fig = make_subplots(
            rows=len(selected_sensors), cols=1,
            shared_xaxes=True, subplot_titles=selected_sensors, vertical_spacing=0.05,
        )
        colors = px.colors.qualitative.Set2
        for i, sensor in enumerate(selected_sensors):
            fig.add_trace(
                go.Scatter(
                    x=exp_data["sequence"], y=exp_data[sensor],
                    mode="lines", name=sensor,
                    line=dict(color=colors[i % len(colors)], width=1),
                    showlegend=False,
                ),
                row=i + 1, col=1,
            )
        fig.update_layout(**CHART_LAYOUT, height=250 * len(selected_sensors))
        fig.update_xaxes(title_text="Sequence (×100ms)", row=len(selected_sensors), col=1)
        st.plotly_chart(fig, width="stretch")

        # 공정 단계 오버레이
        st.subheader("공정 단계 (Machining Process)")
        process_fig = px.scatter(
            exp_data, x="sequence", y="Machining_Process",
            color="Machining_Process", height=150,
        )
        process_fig.update_layout(
            **CHART_LAYOUT, margin=dict(t=10, b=0), showlegend=False, yaxis_title=""
        )
        st.plotly_chart(process_fig, width="stretch")

        st.markdown("""
        <div class="insight-box">
        <p>
        [TIP] <b>공정 단계 해석:</b><br>
        · <b>Prep</b>: 초기 세팅, 센서값이 안정적이어야 함<br>
        · <b>Layer N Roughing</b>: 황삭(거친 절삭), 전류/전력이 높음 — 빠르게 깎는 단계<br>
        · <b>Layer N Finishing</b>: 정삭(미세 절삭), 전류/전력 낮음 — 정밀 마무리 단계<br>
        · <b>End</b>: 가공 종료, 센서값이 초기값으로 복귀<br>
        → worn 공구는 특히 <b>Finishing 단계에서 전류/전력이 비정상적으로 높을 수 있음</b>
        </p>
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════
# 탭 4: Worn vs Unworn
# ═════════════════════════════════════════════
elif selected_tab == tab_names[3]:
    st.title("[WORN] Worn vs Unworn 비교")

    st.markdown("""
    <div class="info-card">
    <h4>이 탭이 가장 중요한 이유</h4>
    <p>
    이 프로젝트의 핵심 질문: <b>"센서 데이터만 보고 공구가 마모되었는지 알 수 있는가?"</b><br>
    여기서 worn과 unworn의 센서값 차이를 확인합니다. 차이가 큰 센서 = 이상탐지 모델의 유력 입력 후보.<br><br>
    <b>기준점:</b> 차이(%)가 ±5% 이상이면 의미 있는 차이, ±10% 이상이면 강한 차이로 판단합니다.<br>
    표준편차(std)가 worn에서 더 크면 → 마모된 공구의 불안정성을 의미합니다.
    </p>
    </div>
    """, unsafe_allow_html=True)

    compare_group = st.selectbox("축 그룹 선택", list(sensor_groups.keys()), key="compare")
    compare_cols = sensor_groups[compare_group]

    # worn / unworn 통계 비교
    st.subheader("통계 비교")
    worn_df = full_df[full_df["tool_condition"] == "worn"]
    unworn_df = full_df[full_df["tool_condition"] == "unworn"]

    comparison_rows = []
    for col in compare_cols:
        diff_pct = (
            (worn_df[col].mean() - unworn_df[col].mean())
            / (abs(unworn_df[col].mean()) + 1e-10) * 100
        )
        std_ratio = worn_df[col].std() / (unworn_df[col].std() + 1e-10)
        comparison_rows.append({
            "센서": col,
            "의미": get_sensor_desc(col)[0],
            "unworn 평균": unworn_df[col].mean(),
            "worn 평균": worn_df[col].mean(),
            "차이(%)": diff_pct,
            "unworn std": unworn_df[col].std(),
            "worn std": worn_df[col].std(),
            "std 비율": std_ratio,
        })
    comp_df = pd.DataFrame(comparison_rows)
    st.dataframe(
        comp_df.style.format({
            "unworn 평균": "{:.3f}", "worn 평균": "{:.3f}",
            "차이(%)": "{:+.1f}%",
            "unworn std": "{:.3f}", "worn std": "{:.3f}",
            "std 비율": "{:.2f}×",
        }).background_gradient(subset=["차이(%)"], cmap="RdYlGn_r"),
        width="stretch",
    )

    # 자동 해석
    significant = comp_df[comp_df["차이(%)"].abs() > 5].sort_values("차이(%)", key=abs, ascending=False)
    if not significant.empty:
        insights = []
        for _, row in significant.iterrows():
            direction = "높음 ↑" if row["차이(%)"] > 0 else "낮음 ↓"
            strength = "강한" if abs(row["차이(%)"]) > 10 else "의미 있는"
            insights.append(
                f"<b>{row['센서']}</b> ({row['의미']}): worn이 {abs(row['차이(%)']):.1f}% {direction} — {strength} 차이"
            )
        st.markdown(f"""
        <div class="insight-box">
        <p>
        [TIP] <b>자동 분석 결과 (차이 > 5% 센서):</b><br>
        {'<br>'.join(f'· {ins}' for ins in insights)}<br><br>
        → 이 센서들이 <b>마모 감지 모델의 유력 피처(feature) 후보</b>입니다.
        </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="insight-box">
        <p>
        [TIP] 이 축 그룹에서는 worn/unworn 평균 차이가 5% 미만입니다.
        다른 축을 확인하거나, 평균이 아닌 분포/시계열 패턴 차이를 살펴보세요.
        </p>
        </div>
        """, unsafe_allow_html=True)

    # Box Plot 비교
    st.subheader("분포 비교 (Box Plot)")
    n_cols_plot = min(3, len(compare_cols))
    n_rows_plot = (len(compare_cols) + n_cols_plot - 1) // n_cols_plot
    fig = make_subplots(rows=n_rows_plot, cols=n_cols_plot, subplot_titles=compare_cols)
    for i, col in enumerate(compare_cols):
        r, c = i // n_cols_plot + 1, i % n_cols_plot + 1
        for cond, color in [("unworn", "#22c55e"), ("worn", "#ef4444")]:
            subset = full_df[full_df["tool_condition"] == cond]
            fig.add_trace(
                go.Box(y=subset[col], name=cond, marker_color=color, showlegend=(i == 0)),
                row=r, col=c,
            )
    fig.update_layout(**CHART_LAYOUT, height=350 * n_rows_plot)
    st.plotly_chart(fig, width="stretch")

    # 시계열 오버레이
    st.subheader("시계열 오버레이 (대표 실험)")
    overlay_sensor = st.selectbox("비교할 센서", compare_cols, key="overlay")

    title, desc = get_sensor_desc(overlay_sensor)
    st.markdown(f"*{overlay_sensor}: {title} — {desc}*")

    worn_exp = full_df[full_df["tool_condition"] == "worn"].groupby("experiment_id").size().idxmax()
    unworn_exp = full_df[full_df["tool_condition"] == "unworn"].groupby("experiment_id").size().idxmax()

    fig_overlay = go.Figure()
    for exp_id, color, label in [
        (unworn_exp, "#22c55e", f"unworn ({unworn_exp})"),
        (worn_exp, "#ef4444", f"worn ({worn_exp})"),
    ]:
        d = full_df[full_df["experiment_id"] == exp_id]
        fig_overlay.add_trace(
            go.Scatter(
                x=d["sequence"], y=d[overlay_sensor],
                mode="lines", name=label,
                line=dict(color=color, width=1.5),
            )
        )
    fig_overlay.update_layout(
        **CHART_LAYOUT, height=350,
        xaxis_title="Sequence (×100ms)", yaxis_title=overlay_sensor,
    )
    st.plotly_chart(fig_overlay, width="stretch")


# ═════════════════════════════════════════════
# 탭 5: 상관관계
# ═════════════════════════════════════════════
elif selected_tab == tab_names[4]:
    st.title("- 센서 간 상관관계")

    st.markdown("""
    <div class="info-card">
    <h4>상관관계를 왜 보나?</h4>
    <p>
    <b>① 중복 제거:</b> 상관계수 |r| > 0.9인 센서 쌍은 거의 같은 정보 → 하나만 남겨도 됨 (피처 축소)<br>
    <b>② 물리적 검증:</b> Command↔Actual이 r≈1.0이면 기계가 정상 추종 중. r이 낮으면 기계 문제<br>
    <b>③ 숨은 관계 발견:</b> 예상 못한 센서 간 상관 → 새로운 파생 피처 아이디어<br><br>
    <b>기준:</b> |r| > 0.8 강한 상관 · 0.5~0.8 중간 · < 0.5 약한 상관
    </p>
    </div>
    """, unsafe_allow_html=True)

    corr_option = st.radio("범위", ["축 그룹별", "전체 센서 (상위 20개)"], horizontal=True)

    if corr_option == "축 그룹별":
        corr_group = st.selectbox("축 그룹", list(sensor_groups.keys()), key="corr")
        corr_cols = sensor_groups[corr_group]
    else:
        variances = full_df[sensor_cols].var().sort_values(ascending=False)
        corr_cols = variances.head(20).index.tolist()

    corr_matrix = full_df[corr_cols].corr()

    fig_corr = px.imshow(
        corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1, aspect="auto",
    )
    fig_corr.update_layout(**CHART_LAYOUT, height=max(400, len(corr_cols) * 30))
    st.plotly_chart(fig_corr, width="stretch")

    # 강한 상관관계 목록
    st.subheader("강한 상관관계 (|r| > 0.8)")
    strong_pairs = []
    for i in range(len(corr_cols)):
        for j in range(i + 1, len(corr_cols)):
            r = corr_matrix.iloc[i, j]
            if abs(r) > 0.8:
                strong_pairs.append({"센서 A": corr_cols[i], "센서 B": corr_cols[j], "상관계수": r})

    if strong_pairs:
        strong_df = pd.DataFrame(strong_pairs).sort_values("상관계수", key=abs, ascending=False)
        st.dataframe(
            strong_df.style.format({"상관계수": "{:.3f}"}).background_gradient(
                subset=["상관계수"], cmap="RdBu_r", vmin=-1, vmax=1
            ),
            width="stretch",
        )

        # 자동 해석
        very_high = strong_df[strong_df["상관계수"].abs() > 0.95]
        if not very_high.empty:
            pairs_text = ", ".join(
                f"{row['센서 A']} ↔ {row['센서 B']} (r={row['상관계수']:.3f})"
                for _, row in very_high.head(5).iterrows()
            )
            st.markdown(f"""
            <div class="insight-box">
            <p>
            [TIP] <b>거의 동일한 정보 (|r| > 0.95):</b> {pairs_text}<br>
            → 이 쌍에서 하나씩 제거하면 피처 수를 줄일 수 있음 (차원 축소).<br>
            특히 Command↔Actual 쌍은 물리적으로 같은 것을 측정하므로, <b>차이값(오차)</b>을 새 피처로 만드는 것이 더 유용합니다.
            </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("|r| > 0.8인 상관관계가 없습니다.")


# ═════════════════════════════════════════════
# 탭 6: 공정 단계
# ═════════════════════════════════════════════
elif selected_tab == tab_names[5]:
    st.title("- 공정 단계 (Machining Process)")

    st.markdown("""
    <div class="info-card">
    <h4>공정 단계란?</h4>
    <p>
    CNC 밀링은 하나의 실험 안에서 여러 단계를 거칩니다:<br><br>
    <b>Prep</b> (준비) → <b>Layer 1 Roughing</b> (1차 황삭) → <b>Layer 1 Finishing</b> (1차 정삭)
    → <b>Layer 2 Roughing</b> → <b>Layer 2 Finishing</b> → <b>Layer 3 Roughing</b> → <b>Layer 3 Finishing</b> → <b>End</b> (종료)<br><br>
    · <b>Roughing (황삭)</b>: 빠르게 많이 깎음 → 높은 이송속도, 높은 절삭력, 높은 전류/전력<br>
    · <b>Finishing (정삭)</b>: 느리게 정밀하게 → 낮은 이송속도, 낮은 절삭력, 낮은 전류/전력<br><br>
    → 공정별로 센서 "정상 범위"가 다르므로, 이상탐지 시 <b>공정 단계를 반드시 고려</b>해야 합니다.
    </p>
    </div>
    """, unsafe_allow_html=True)

    # 공정 단계 분포
    st.subheader("공정 단계 분포")
    process_counts = full_df["Machining_Process"].value_counts().reset_index()
    process_counts.columns = ["공정 단계", "행 수"]
    process_counts["비율(%)"] = (process_counts["행 수"] / len(full_df) * 100).round(1)

    col_p1, col_p2 = st.columns([2, 3])
    with col_p1:
        st.dataframe(process_counts, width="stretch", height=400)
    with col_p2:
        fig_proc = px.bar(
            process_counts, x="공정 단계", y="행 수",
            color="행 수", color_continuous_scale="Blues",
        )
        fig_proc.update_layout(**CHART_LAYOUT, height=400)
        st.plotly_chart(fig_proc, width="stretch")

    # 공정별 센서 평균
    st.subheader("공정 단계별 센서 평균값")
    proc_sensor = st.selectbox("센서 선택", sensor_cols, key="proc_sensor")

    title, desc = get_sensor_desc(proc_sensor)
    st.markdown(f"*{proc_sensor}: {title} — {desc}*")

    process_stats = (
        full_df.groupby("Machining_Process")[proc_sensor]
        .agg(["mean", "std", "min", "max"]).reset_index()
    )

    fig_proc_sensor = px.bar(
        process_stats, x="Machining_Process", y="mean", error_y="std",
        title=f"{proc_sensor} — 공정별 평균 ± 표준편차",
    )
    fig_proc_sensor.update_layout(**CHART_LAYOUT, height=400)
    st.plotly_chart(fig_proc_sensor, width="stretch")

    # 공정별 worn/unworn 비교
    st.subheader("공정별 Worn vs Unworn")
    process_cond = (
        full_df.groupby(["Machining_Process", "tool_condition"])[proc_sensor]
        .mean().reset_index()
    )
    fig_proc_cond = px.bar(
        process_cond, x="Machining_Process", y=proc_sensor,
        color="tool_condition", barmode="group",
        color_discrete_map={"worn": "#ef4444", "unworn": "#22c55e"},
    )
    fig_proc_cond.update_layout(**CHART_LAYOUT, height=400)
    st.plotly_chart(fig_proc_cond, width="stretch")

    # 공정별 차이 자동 해석
    process_diff = (
        full_df.groupby(["Machining_Process", "tool_condition"])[proc_sensor]
        .mean().unstack(fill_value=0)
    )
    if "worn" in process_diff.columns and "unworn" in process_diff.columns:
        process_diff["차이(%)"] = (
            (process_diff["worn"] - process_diff["unworn"])
            / (process_diff["unworn"].abs() + 1e-10) * 100
        )
        max_diff_proc = process_diff["차이(%)"].abs().idxmax()
        max_diff_val = process_diff.loc[max_diff_proc, "차이(%)"]

        st.markdown(f"""
        <div class="insight-box">
        <p>
        [TIP] <b>공정별 분석:</b> <code>{proc_sensor}</code>의 worn/unworn 차이가 가장 큰 공정은
        <b>{max_diff_proc}</b> ({max_diff_val:+.1f}%).<br>
        → 이 공정 구간의 센서 데이터가 마모 감지에 가장 유용할 수 있습니다.<br>
        → 모든 공정을 통합 분석하는 것보다, <b>특정 공정 구간만 집중 분석</b>하는 것이 더 효과적일 수 있습니다.
        </p>
        </div>
        """, unsafe_allow_html=True)
