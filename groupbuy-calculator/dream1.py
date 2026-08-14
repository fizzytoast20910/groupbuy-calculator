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

    /* 전체 요약 카드 */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1rem 1.2rem;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.06);
        min-height: 105px;
    }

    div[data-testid="stMetricLabel"] {
        color: #6b7280;
        font-size: 0.9rem;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #111827;
        font-size: 1.5rem;
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
# 경고 팝업 함수
# ------------------------------------------------
def show_quantity_warning(too_large_df):
    """구매 개수가 10억 이상일 때 표시하는 팝업"""
    st.markdown(
        """
        <div style="
            background-color:#fff7ed;
            border:1px solid #fed7aa;
            border-radius:14px;
            padding:10px 14px;
            margin-bottom:10px;
        ">
            <h3 style="color:#c2410c; margin:0;">
                ⚠️ 구매 개수 입력 오류
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.error(
        "구매 개수가 10억 개 이상으로 입력되었습니다.\n\n"
        "현실적으로 사용할 수 있는 범위를 초과한 값이므로 "
        "구매 개수를 수정해주세요."
    )

    st.write("문제가 있는 구매자:")

    warning_df = too_large_df[
        ["구매자", "구매 개수"]
    ].copy()

    st.dataframe(
        warning_df,
        use_container_width=True,
        hide_index=True
    )

    st.warning(
        "구매 개수를 수정한 뒤 다시 계산해주세요."
    )


def show_discount_warning(total_discount, max_possible_discount):
    """할인금액이 전체 지출 가능 금액보다 클 때 표시하는 팝업"""
    st.markdown(
        """
        <div style="
            background-color:#fef2f2;
            border:1px solid #fecaca;
            border-radius:14px;
            padding:10px 14px;
            margin-bottom:10px;
        ">
            <h3 style="color:#b91c1c; margin:0;">
                ❌ 할인금액 입력 오류
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.error(
        f"전체 할인금액은 {total_discount:,.0f}원입니다.\n\n"
        f"할인 적용 전 총 지출 가능 금액은 "
        f"{max_possible_discount:,.0f}원입니다.\n\n"
        "할인금액은 할인 적용 전 총 지출 가능 금액보다 "
        "클 수 없습니다."
    )


def show_negative_warning(negative_df):
    """개인별 최종 부담금이 음수일 때 표시하는 팝업"""
    st.markdown(
        """
        <div style="
            background-color:#fef2f2;
            border:1px solid #fecaca;
            border-radius:14px;
            padding:10px 14px;
            margin-bottom:10px;
        ">
            <h3 style="color:#b91c1c; margin:0;">
                ❌ 정산 금액 오류
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.error(
        "일부 구매자의 최종 부담금이 0원보다 작습니다.\n\n"
        "할인금액이나 구매 개수를 확인해주세요."
    )

    st.write("문제가 있는 구매자:")

    warning_df = negative_df[
        ["구매자", "구매 개수", "최종 부담금"]
    ].copy()

    warning_df["최종 부담금"] = warning_df[
        "최종 부담금"
    ].map(lambda x: f"{x:,.0f}원")

    st.dataframe(
        warning_df,
        use_container_width=True,
        hide_index=True
    )


# ------------------------------------------------
# 헤더
# ------------------------------------------------
st.markdown(
    """
<div class="hero">
    <h1>🧾 공동구매 정산 시스템</h1>
    <p>
        구매 개수, 배송비, 공동비용, 할인금액을 반영하여
        개인별 최종 부담금을 자동으로 계산합니다.
    </p>
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

    # 배송비
    shipping_cost = st.number_input(
        "배송비 (원)",
        min_value=0,
        value=3000,
        step=100
    )

    # 기타 공동비용
    other_cost = st.number_input(
        "기타 공동비용 (원)",
        min_value=0,
        value=0,
        step=100
    )

    # 전체 할인금액
    total_discount = st.number_input(
        "전체 할인금액 (원)",
        min_value=0,
        value=0,
        step=100
    )

    # 공동비용 분배 방법
    distribution_method = st.radio(
        "공동비용 분배 방법",
        ["균등 분배", "구매 금액 비례"],
        horizontal=True
    )

    st.caption(
        "균등 분배는 모든 참여자가 같은 금액을 부담하고, "
        "구매 금액 비례는 개인 상품금액의 비율에 따라 공동비용을 분담합니다."
    )

    st.markdown("</div>", unsafe_allow_html=True)


with right:
    st.markdown(
        "<div class='section-card'><div class='section-title'>👥 구매자 입력</div>",
        unsafe_allow_html=True
    )

    # 구매 인원 수
    people_count = st.slider(
        "구매 인원 수",
        min_value=1,
        max_value=50,
        value=5
    )

    # 기본 구매자 데이터
    default_df = pd.DataFrame({
        "구매자": [f"구매자 {i + 1}" for i in range(people_count)],
        "구매 개수": [1 for _ in range(people_count)],
        "개인 상품금액": [0 for _ in range(people_count)]
    })

    # 구매자별 정보 입력
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
                max_value=10000,
                step=1,
                required=True
            ),
            "개인 상품금액": st.column_config.NumberColumn(
                "개인 상품금액 (원)",
                min_value=0,
                step=100,
                required=True
            )
        }
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------
# 기본 입력값 검증
# ------------------------------------------------

# 구매 개수 숫자 변환
try:
    df["구매 개수"] = pd.to_numeric(
        df["구매 개수"],
        errors="coerce"
    ).fillna(1)

    # 1개 미만이면 1개로 처리
    df.loc[df["구매 개수"] < 1, "구매 개수"] = 1
    df["구매 개수"] = df["구매 개수"].astype(int)

    # 개인 상품금액 숫자 변환
    df["개인 상품금액"] = pd.to_numeric(
        df["개인 상품금액"],
        errors="coerce"
    ).fillna(0)

    # 음수 금액 방지
    df.loc[df["개인 상품금액"] < 0, "개인 상품금액"] = 0

except Exception:
    st.error("입력값을 확인하는 과정에서 문제가 발생했습니다.")
    st.stop()


# ------------------------------------------------
# 기본 정보 계산
# ------------------------------------------------
total_people = len(df)
total_quantity = int(df["구매 개수"].sum())
total_product_cost = float(df["개인 상품금액"].sum())

# 배송비 + 기타 공동비용
total_common_cost = shipping_cost + other_cost


# ------------------------------------------------
# 구매 개수 10억 이상 검증
# ------------------------------------------------
MAX_QUANTITY = 1_000_000_000

too_large = df[df["구매 개수"] >= MAX_QUANTITY]

if not too_large.empty:

    @st.dialog("⚠️ 구매 개수 입력 경고")
    def quantity_warning_dialog():
        show_quantity_warning(too_large)

    quantity_warning_dialog()
    st.stop()


# ------------------------------------------------
# 할인금액 검증
# ------------------------------------------------
# 할인 적용 전 총 지출 가능 금액
max_possible_discount = total_product_cost + total_common_cost

if total_discount > max_possible_discount:

    @st.dialog("❌ 할인금액 입력 경고")
    def discount_warning_dialog():
        show_discount_warning(
            total_discount,
            max_possible_discount
        )

    discount_warning_dialog()
    st.stop()


# ------------------------------------------------
# 공동비용 계산
# ------------------------------------------------
if distribution_method == "균등 분배":

    # 모든 참여자가 동일한 금액을 부담
    df["공동비용 부담"] = (
        total_common_cost / total_people
    )

else:

    # 개인 상품금액 비율에 따라 공동비용을 분배
    if total_product_cost > 0:
        df["공동비용 부담"] = (
            total_common_cost
            * df["개인 상품금액"]
            / total_product_cost
        )
    else:
        # 상품금액이 모두 0원이라면 균등 분배
        df["공동비용 부담"] = (
            total_common_cost / total_people
        )


# ------------------------------------------------
# 할인금액 계산
# ------------------------------------------------
# 개인 상품금액 비율에 따라 전체 할인금액을 배분
if total_product_cost > 0:
    df["할인 배분"] = (
        total_discount
        * df["개인 상품금액"]
        / total_product_cost
    )
else:
    # 상품금액이 모두 0원이면 할인금액도 배분할 기준이 없으므로 오류 처리
    if total_discount > 0:
        @st.dialog("❌ 할인금액 입력 경고")
        def zero_product_discount_dialog():
            st.error(
                "개인 상품금액의 합계가 0원인데 전체 할인금액이 입력되었습니다.\n\n"
                "개인 상품금액을 먼저 입력하거나 할인금액을 0원으로 설정해주세요."
            )

        zero_product_discount_dialog()
        st.stop()

    df["할인 배분"] = 0.0


# ------------------------------------------------
# 최종 부담금 계산
# ------------------------------------------------
df["최종 부담금"] = (
    df["개인 상품금액"]
    + df["공동비용 부담"]
    - df["할인 배분"]
)


# ------------------------------------------------
# 개인별 최종 부담금 음수 검증
# ------------------------------------------------
negative_df = df[df["최종 부담금"] < 0]

if not negative_df.empty:

    @st.dialog("❌ 정산 금액 오류")
    def negative_warning_dialog():
        show_negative_warning(negative_df)

    negative_warning_dialog()
    st.stop()


# ------------------------------------------------
# 전체 금액 계산
# ------------------------------------------------
total_final_cost = (
    total_product_cost
    + shipping_cost
    + other_cost
    - total_discount
)


# ------------------------------------------------
# 소수점 차이 보정
# ------------------------------------------------
difference = (
    total_final_cost
    - df["최종 부담금"].sum()
)

if abs(difference) > 0.0001:

    # 계산 과정에서 발생하는 소수점 차이를 마지막 구매자에게 조정
    df.loc[df.index[-1], "최종 부담금"] += difference


# ------------------------------------------------
# 전체 요약
# ------------------------------------------------
st.markdown("### 📊 전체 요약")

# 첫 번째 줄
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="총 구매 인원",
        value=f"{total_people:,}명"
    )

with col2:
    st.metric(
        label="총 구매 개수",
        value=f"{total_quantity:,}개"
    )

with col3:
    st.metric(
        label="최종 지출금액",
        value=f"{total_final_cost:,.0f}원"
    )


# 두 번째 줄
col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        label="상품 총액",
        value=f"{total_product_cost:,.0f}원"
    )

with col5:
    st.metric(
        label="공동비용",
        value=f"{total_common_cost:,.0f}원"
    )

with col6:
    st.metric(
        label="전체 할인금액",
        value=f"{total_discount:,.0f}원"
    )


# ------------------------------------------------
# 결과 표
# ------------------------------------------------
st.markdown("### 💰 개인별 정산 결과")

display_df = df.copy()

# 금액을 보기 좋은 문자열로 변환
for col in [
    "개인 상품금액",
    "공동비용 부담",
    "할인 배분",
    "최종 부담금"
]:
    display_df[col] = display_df[col].map(
        lambda x: f"{x:,.0f}원"
    )


st.dataframe(
    display_df[
        [
            "구매자",
            "구매 개수",
            "개인 상품금액",
            "공동비용 부담",
            "할인 배분",
            "최종 부담금"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


# ------------------------------------------------
# 전체 금액 검증
# ------------------------------------------------
final_sum = df["최종 부담금"].sum()

if abs(final_sum - total_final_cost) < 0.01:
    st.success(
        "✅ 개인별 최종 부담금의 합계가 "
        "전체 최종 지출금액과 정확하게 일치합니다."
    )
else:
    st.error(
        "❌ 개인별 금액의 합계와 전체 지출금액이 "
        "일치하지 않습니다."
    )


# ------------------------------------------------
# CSV 다운로드
# ------------------------------------------------
csv_df = df[
    [
        "구매자",
        "구매 개수",
        "개인 상품금액",
        "공동비용 부담",
        "할인 배분",
        "최종 부담금"
    ]
].copy()

csv = csv_df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

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
    "행사 운영, 동아리 공동구매, 단체 물품 구매 등의 상황에서 "
    "개인별 부담금을 계산하기 위한 Streamlit 기반 공동구매 정산 시스템"
)
