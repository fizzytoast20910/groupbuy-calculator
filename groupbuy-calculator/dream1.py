import streamlit as st
import pandas as pd
from io import BytesIO

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
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
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
    unsafe_allow_html=True,
)

# ------------------------------------------------
# 상수
# ------------------------------------------------
REQUIRED_COLUMNS = ["구매자", "구매 개수", "개인 상품금액"]
MAX_QUANTITY = 1_000_000_000


# ------------------------------------------------
# 데이터 정리 함수
# ------------------------------------------------
def normalize_dataframe(dataframe):
    """직접 입력과 Excel 입력 데이터를 같은 형식으로 정리."""
    df = dataframe.copy()

    # 필요한 열만 사용
    df = df[REQUIRED_COLUMNS].copy()

    # 구매자 이름 정리
    df["구매자"] = df["구매자"].fillna("").astype(str).str.strip()

    empty_names = df["구매자"] == ""
    if empty_names.any():
        df.loc[empty_names, "구매자"] = [
            f"구매자 {i + 1}"
            for i in range(empty_names.sum())
        ]

    # 구매 개수 정리
    df["구매 개수"] = pd.to_numeric(
        df["구매 개수"],
        errors="coerce"
    ).fillna(1)

    df.loc[df["구매 개수"] < 1, "구매 개수"] = 1
    df["구매 개수"] = df["구매 개수"].astype(int)

    # 개인 상품금액 정리
    df["개인 상품금액"] = pd.to_numeric(
        df["개인 상품금액"],
        errors="coerce"
    ).fillna(0)

    df.loc[df["개인 상품금액"] < 0, "개인 상품금액"] = 0

    return df


# ------------------------------------------------
# 경고 팝업 함수
# ------------------------------------------------
def quantity_warning_dialog(too_large_df):
    """10억 이상 구매 개수 입력 시 표시."""
    st.markdown("### ⚠️ 구매 개수 입력 오류")

    st.error(
        "구매 개수가 10억 개 이상으로 입력되었습니다.\n\n"
        "현실적인 범위를 초과하는 값이므로 "
        "구매 개수를 수정해주세요."
    )

    st.write("문제가 있는 구매자:")

    st.dataframe(
        too_large_df[["구매자", "구매 개수"]],
        use_container_width=True,
        hide_index=True,
    )


def discount_warning_dialog(total_discount, max_possible_discount):
    """전체 할인금액이 과도한 경우 표시."""
    st.markdown("### ❌ 할인금액 입력 오류")

    st.error(
        f"전체 할인금액은 {total_discount:,.0f}원입니다.\n\n"
        f"할인 적용 전 총 지출 가능 금액은 "
        f"{max_possible_discount:,.0f}원입니다.\n\n"
        "할인금액은 할인 적용 전 총 지출 가능 금액보다 "
        "클 수 없습니다."
    )


def negative_warning_dialog(negative_df):
    """개인별 최종 부담금이 음수인 경우 표시."""
    st.markdown("### ❌ 정산 금액 오류")

    st.error(
        "일부 구매자의 최종 부담금이 0원보다 작습니다.\n\n"
        "할인금액이나 구매 개수를 확인해주세요."
    )

    warning_df = negative_df[
        ["구매자", "구매 개수", "최종 부담금"]
    ].copy()

    warning_df["최종 부담금"] = warning_df[
        "최종 부담금"
    ].map(lambda x: f"{x:,.0f}원")

    st.dataframe(
        warning_df,
        use_container_width=True,
        hide_index=True,
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
    unsafe_allow_html=True,
)


# ------------------------------------------------
# 입력 영역
# ------------------------------------------------
left, right = st.columns([1, 2], gap="large")


# ------------------------------------------------
# 왼쪽: 물품 정보
# ------------------------------------------------
with left:
    st.markdown(
        "<div class='section-card'><div class='section-title'>⚙️ 물품 정보</div>",
        unsafe_allow_html=True,
    )

    shipping_cost = st.number_input(
        "배송비 (원)",
        min_value=0,
        value=3000,
        step=100,
    )

    other_cost = st.number_input(
        "기타 공동비용 (원)",
        min_value=0,
        value=0,
        step=100,
    )

    total_discount = st.number_input(
        "전체 할인금액 (원)",
        min_value=0,
        value=0,
        step=100,
    )

    distribution_method = st.selectbox(
        "공동비용 분배 방법",
        [
            "균등 분배",
            "구매 개수 비례",
            "구매 금액 비례",
        ],
    )

    st.caption(
        "균등 분배는 모든 참여자가 같은 금액을 부담합니다. "
        "구매 개수 비례는 구매 수량 비율로, "
        "구매 금액 비례는 개인 상품금액 비율로 공동비용을 분담합니다."
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------
# 오른쪽: 구매자 입력
# ------------------------------------------------
with right:
    st.markdown(
        "<div class='section-card'><div class='section-title'>👥 구매자 입력</div>",
        unsafe_allow_html=True,
    )

    # 처음에는 직접 입력이 기본값
    input_method = st.radio(
        "입력 방법",
        ["직접 입력", "파일 입력"],
        horizontal=True,
        index=0,
    )

    # --------------------------------------------
    # 직접 입력
    # --------------------------------------------
    if input_method == "직접 입력":

        people_count = st.slider(
            "구매 인원 수",
            min_value=1,
            max_value=50,
            value=5,
        )

        default_df = pd.DataFrame({
            "구매자": [
                f"구매자 {i + 1}"
                for i in range(people_count)
            ],
            "구매 개수": [1] * people_count,
            "개인 상품금액": [0] * people_count,
        })

        df = st.data_editor(
            default_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "구매자": st.column_config.TextColumn(
                    "구매자 이름",
                    required=True,
                ),
                "구매 개수": st.column_config.NumberColumn(
                    "구매 개수",
                    min_value=1,
                    step=1,
                    required=True,
                ),
                "개인 상품금액": st.column_config.NumberColumn(
                    "개인 상품금액 (원)",
                    min_value=0,
                    step=100,
                    required=True,
                ),
            },
            key="direct_input_table",
        )

        df = normalize_dataframe(df)

    # --------------------------------------------
    # 파일 입력
    # --------------------------------------------
    else:

        st.info(
            "Excel 파일의 첫 번째 시트에서 아래 3개 열을 읽습니다: "
            "구매자 / 구매 개수 / 개인 상품금액"
        )

        uploaded_file = st.file_uploader(
            "Excel 파일 업로드",
            type=["xlsx", "xls"],
            help="지원 형식: .xlsx, .xls",
            key="buyer_excel_upload",
        )

        # 파일을 아직 업로드하지 않은 경우
        if uploaded_file is None:
            st.info(
                "Excel 파일을 업로드하면 구매자 입력표가 "
                "파일의 내용으로 교체됩니다."
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()

        # Excel 파일 읽기
        try:
            df = pd.read_excel(uploaded_file)

        except ImportError:
            st.error(
                "Excel 파일을 읽기 위한 라이브러리가 없습니다. "
                "requirements.txt에 openpyxl과 xlrd를 추가해주세요."
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()

        except Exception as error:
            st.error(
                f"Excel 파일을 읽는 중 오류가 발생했습니다.\n\n{error}"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()

        # 필수 열 검사
        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing_columns:
            st.error(
                "Excel 파일에 필요한 열이 없습니다: "
                + ", ".join(missing_columns)
            )

            st.caption(
                "필수 열: 구매자 / 구매 개수 / 개인 상품금액"
            )

            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()

        # 필요한 열만 가져오기
        df = normalize_dataframe(df)

        # 빈 파일 검사
        if df.empty:
            st.error(
                "Excel 파일에 구매자 데이터가 없습니다."
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()

        st.success(
            f"Excel 파일에서 {len(df)}명의 구매자 정보를 불러왔습니다."
        )

        # 불러온 데이터 미리보기
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------
# 기본 검증
# ------------------------------------------------
if df.empty:
    st.error("구매자 데이터가 없습니다.")
    st.stop()

# 10억 이상 구매 개수 검사
too_large = df[
    df["구매 개수"] >= MAX_QUANTITY
]

if not too_large.empty:

    @st.dialog("⚠️ 구매 개수 입력 경고")
    def open_quantity_warning():
        quantity_warning_dialog(too_large)

    open_quantity_warning()
    st.stop()


# ------------------------------------------------
# 전체 정보 계산
# ------------------------------------------------
total_people = len(df)
total_quantity = int(df["구매 개수"].sum())
total_product_cost = float(
    df["개인 상품금액"].sum()
)

total_common_cost = float(
    shipping_cost + other_cost
)

# 할인 적용 전 총 지출 가능 금액
max_possible_discount = (
    total_product_cost
    + total_common_cost
)


# ------------------------------------------------
# 할인금액 검증
# ------------------------------------------------
if total_discount > max_possible_discount:

    @st.dialog("❌ 할인금액 입력 경고")
    def open_discount_warning():
        discount_warning_dialog(
            total_discount,
            max_possible_discount,
        )

    open_discount_warning()
    st.stop()


# ------------------------------------------------
# 공동비용 계산
# ------------------------------------------------
if distribution_method == "균등 분배":

    # 모든 참여자에게 동일하게 분배
    df["공동비용 부담"] = (
        total_common_cost
        / total_people
    )

elif distribution_method == "구매 개수 비례":

    # 구매 개수 비율에 따라 분배
    if total_quantity <= 0:
        st.error("총 구매 개수가 0개입니다.")
        st.stop()

    df["공동비용 부담"] = (
        total_common_cost
        * df["구매 개수"]
        / total_quantity
    )

else:

    # 구매 금액 비율에 따라 분배
    if total_product_cost > 0:

        df["공동비용 부담"] = (
            total_common_cost
            * df["개인 상품금액"]
            / total_product_cost
        )

    else:

        # 모든 상품금액이 0원이면 금액 비례 계산 불가
        if total_common_cost > 0:
            st.error(
                "구매 금액 비례 방식은 "
                "개인 상품금액이 0원일 때 사용할 수 없습니다."
            )
            st.stop()

        df["공동비용 부담"] = 0.0


# ------------------------------------------------
# 할인금액 계산
# ------------------------------------------------
if total_product_cost > 0:

    # 개인 상품금액 비율로 할인금액 배분
    df["할인 배분"] = (
        total_discount
        * df["개인 상품금액"]
        / total_product_cost
    )

else:

    # 상품금액 합계가 0인데 할인금액이 있다면 계산 불가
    if total_discount > 0:

        @st.dialog("❌ 할인금액 입력 경고")
        def open_zero_product_discount_warning():
            st.error(
                "개인 상품금액의 합계가 0원인데 "
                "전체 할인금액이 입력되었습니다.\n\n"
                "개인 상품금액을 입력하거나 할인금액을 0원으로 설정해주세요."
            )

        open_zero_product_discount_warning()
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
# 음수 부담금 검증
# ------------------------------------------------
negative_df = df[
    df["최종 부담금"] < 0
]

if not negative_df.empty:

    @st.dialog("❌ 정산 금액 오류")
    def open_negative_warning():
        negative_warning_dialog(negative_df)

    open_negative_warning()
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
# 소수점 오차 보정
# ------------------------------------------------
difference = (
    total_final_cost
    - df["최종 부담금"].sum()
)

if abs(difference) > 0.0001:

    # 원 단위 반올림 과정에서 발생할 수 있는 오차 보정
    df.loc[
        df.index[-1],
        "최종 부담금"
    ] += difference


# ------------------------------------------------
# 전체 요약
# ------------------------------------------------
st.markdown("### 📊 전체 요약")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "총 구매 인원",
        f"{total_people:,}명"
    )

with col2:
    st.metric(
        "총 구매 개수",
        f"{total_quantity:,}개"
    )

with col3:
    st.metric(
        "최종 지출금액",
        f"{total_final_cost:,.0f}원"
    )


col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        "상품 총액",
        f"{total_product_cost:,.0f}원"
    )

with col5:
    st.metric(
        "공동비용",
        f"{total_common_cost:,.0f}원"
    )

with col6:
    st.metric(
        "전체 할인금액",
        f"{total_discount:,.0f}원"
    )


# ------------------------------------------------
# 결과 표
# ------------------------------------------------
st.markdown("### 💰 개인별 정산 결과")

display_df = df.copy()

for col in [
    "개인 상품금액",
    "공동비용 부담",
    "할인 배분",
    "최종 부담금",
]:
    display_df[col] = display_df[col].map(
        lambda value: f"{value:,.0f}원"
    )

st.dataframe(
    display_df[
        [
            "구매자",
            "구매 개수",
            "개인 상품금액",
            "공동비용 부담",
            "할인 배분",
            "최종 부담금",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


# ------------------------------------------------
# 전체 금액 무결성 검증
# ------------------------------------------------
final_sum = df["최종 부담금"].sum()

if abs(final_sum - total_final_cost) < 0.01:

    st.success(
        "✅ 개인별 최종 부담금의 합계가 "
        "전체 최종 지출금액과 정확하게 일치합니다."
    )

else:

    st.error(
        "❌ 개인별 금액의 합계와 "
        "전체 지출금액이 일치하지 않습니다."
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
        "최종 부담금",
    ]
].copy()

# UTF-8 BOM을 포함한 bytes로 변환
# Windows Excel에서 한글이 깨지는 문제를 방지
csv_bytes = csv_df.to_csv(
    index=False,
    encoding="utf-8-sig",
).encode("utf-8-sig")

st.download_button(
    "📥 정산 결과 CSV 다운로드",
    data=csv_bytes,
    file_name="공동구매_정산결과.csv",
    mime="text/csv; charset=utf-8",
)


# ------------------------------------------------
# Excel 다운로드
# ------------------------------------------------
excel_buffer = BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    csv_df.to_excel(
        writer,
        index=False,
        sheet_name="정산결과",
    )

st.download_button(
    "📊 정산 결과 Excel 다운로드",
    data=excel_buffer.getvalue(),
    file_name="공동구매_정산결과.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
)


# ------------------------------------------------
# 하단 설명
# ------------------------------------------------
st.markdown("---")

st.caption(
    "행사 운영, 동아리 공동구매, 단체 물품 구매 등의 상황에서 "
    "개인별 부담금을 계산하기 위한 Streamlit 기반 공동구매 정산 시스템"
)
