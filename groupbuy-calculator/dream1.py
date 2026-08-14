import streamlit as st
import pandas as pd

# ------------------------------------------------
# 페이지 설정
# ------------------------------------------------
st.set_page_config(
    page_title="공동구매 정산 시스템",
    page_icon="🧾",
    layout="wide"
)


# ------------------------------------------------
# 커스텀 스타일
# ------------------------------------------------
st.markdown(
    """
<style>
    .stApp {
        background-color: #f4f7fb;
    }

    .hero {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        padding: 2rem 2.5rem;
        border-radius: 24px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.18);
    }

    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 800;
    }

    .hero p {
        margin-top: 0.6rem;
        font-size: 1rem;
        opacity: 0.92;
    }

    .section-card {
        background: white;
        padding: 1.25rem;
        border-radius: 20px;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.75rem;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.9rem;
        margin: 1rem 0 1.5rem 0;
    }

    .summary-card {
        background: white;
        border-radius: 18px;
        padding: 1rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05);
    }

    .summary-label {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 0.35rem;
    }

    .summary-value {
        color: #111827;
        font-size: 1.35rem;
        font-weight: 800;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }

    .stDownloadButton button {
        width: 100%;
        border-radius: 12px;
        background: #2563eb;
        color: white;
        border: none;
        padding: 0.7rem 1rem;
        font-weight: 600;
    }

    .stDownloadButton button:hover {
        background: #1d4ed8;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True
)


# ------------------------------------------------
# 헤더
# ------------------------------------------------
st.markdown(
    """
<div class="hero">
    <h1>🧾 공동구매 정산 시스템</h1>
    <p>구매 개수, 배송비, 공동비용, 할인금액을 반영하여 개인별 최종 부담금을 자동으로 계산합니다.</p>
</div>
""",
    unsafe_allow_html=True
)


# ------------------------------------------------
# 입력 영역
# ------------------------------------------------
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown(
        "<div class='section-card'><div class='section-title'>⚙️ 물품 정보</div>",
        unsafe_allow_html=True
    )

    base_price = st.number_input(
        "기준 개당 가격 (원)",
        min_value=0,
        value=10000,
        step=100
    )

    shipping_cost = st.number_input(
        "배송비 (원)",
        min_value=0,
        value=3000,
        step=100
    )

    other_cost = st.number_input(
        "기타 공동비용 (원)",
        min_value=0,
        value=0,
        step=100
    )

    total_discount = st.number_input(
        "전체 할인금액 (원)",
        min_value=0,
        value=0,
        step=100
    )

    distribution_method = st.radio(
        "공동비용 분배 방법",
        ["균등 분배", "구매 개수 비례"],
        horizontal=True
    )

    st.caption(
        "균등 분배는 참여자 수로 동일하게 나누고, 구매 개수 비례는 구매 수량 비율에 따라 공동비용을 분담합니다."
    )

    st.markdown("</div>", unsafe_allow_html=True)


with right:
    st.markdown(
        "<div class='section-card'><div class='section-title'>👥 구매자 입력</div>",
        unsafe_allow_html=True
    )

    people_count = st.slider(
        "구매 인원 수",
        min_value=1,
        max_value=50,
        value=5
    )

    default_df = pd.DataFrame({
        "구매자": [f"구매자 {i+1}" for i in range(people_count)],
        "구매 개수": [1] * people_count
    })

    df = st.data_editor(
        default_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "구매자": st.column_config.TextColumn(
                "구매자 이름",
                required=True
            ),
            "구매 개수": st.column_config.NumberColumn(
                "구매 개수",
                min_value=1,
                step=1,
                required=True
            )
        }
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------
# 입력값 검증
# ------------------------------------------------
df["구매 개수"] = pd.to_numeric(df["구매 개수"], errors="coerce").fillna(1)
df.loc[df["구매 개수"] < 1, "구매 개수"] = 1
df["구매 개수"] = df["구매 개수"].astype(int)

total_quantity = int(df["구매 개수"].sum())
total_people = len(df)


# ------------------------------------------------
# 계산
# ------------------------------------------------
df["상품비"] = base_price * df["구매 개수"]

total_common_cost = shipping_cost + other_cost

if distribution_method == "균등 분배":
    df["공동비용 부담"] = total_common_cost / total_people
else:
    df["공동비용 부담"] = (
        total_common_cost * df["구매 개수"] / total_quantity
    )

df["할인 배분"] = (
    total_discount * df["구매 개수"] / total_quantity
)

df["최종 부담금"] = (
    df["상품비"] + df["공동비용 부담"] - df["할인 배분"]
)

total_product_cost = int(df["상품비"].sum())
total_final_cost = (
    total_product_cost + total_common_cost - total_discount
)

difference = total_final_cost - df["최종 부담금"].sum()
if abs(difference) > 0.0001:
    df.loc[df.index[-1], "최종 부담금"] += difference


# ------------------------------------------------
# 요약 카드
# ------------------------------------------------
st.markdown("### 📊 전체 요약")

summary_html = f"""
<div class="summary-grid">
    <div class="summary-card">
        <div class="summary-label">총 구매 인원</div>
        <div class="summary-value">{total_people}명</div>
    </div>
    <div class="summary-card">
        <div class="summary-label">총 구매 개수</div>
        <div class="summary-value">{total_quantity:,}개</div>
    </div>
    <div class="summary-card">
        <div class="summary-label">상품 총액</div>
        <div class="summary-value">{total_product_cost:,.0f}원</div>
    </div>
    <div class="summary-card">
        <div class="summary-label">공동비용</div>
        <div class="summary-value">{total_common_cost:,.0f}원</div>
    </div>
    <div class="summary-card">
        <div class="summary-label">전체 할인금액</div>
        <div class="summary-value">{total_discount:,.0f}원</div>
    </div>
    <div class="summary-card">
        <div class="summary-label">최종 지출금액</div>
        <div class="summary-value">{total_final_cost:,.0f}원</div>
    </div>
</div>
"""

st.markdown(summary_html, unsafe_allow_html=True)


# ------------------------------------------------
# 결과 표
# ------------------------------------------------
st.markdown("### 💰 개인별 정산 결과")

display_df = df.copy()

for col in ["상품비", "공동비용 부담", "할인 배분", "최종 부담금"]:
    display_df[col] = display_df[col].map(lambda x: f"{x:,.0f}원")

st.dataframe(
    display_df[[
        "구매자",
        "구매 개수",
        "상품비",
        "공동비용 부담",
        "할인 배분",
        "최종 부담금"
    ]],
    use_container_width=True,
    hide_index=True
)


# ------------------------------------------------
# CSV 다운로드
# ------------------------------------------------
csv_df = df[[
    "구매자",
    "구매 개수",
    "상품비",
    "공동비용 부담",
    "할인 배분",
    "최종 부담금"
]].copy()

csv = csv_df.to_csv(index=False, encoding="utf-8-sig")

st.download_button(
    "📥 정산 결과 CSV 다운로드",
    data=csv,
    file_name="공동구매_정산결과.csv",
    mime="text/csv"
)


# ------------------------------------------------
# 하단 설명
# ------------------------------------------------
st.markdown("---")
st.caption(
    "행사 운영, 동아리 공동구매, 단체 물품 구매 등의 상황에서 개인별 부담금을 계산하기 위한 Streamlit 기반 공동구매 정산 시스템"
)
