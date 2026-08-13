import streamlit as st
import pandas as pd

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="공동구매 비용 계산기",
    page_icon="🧮",
    layout="wide"
)

st.title("🧮 공동구매 비용 계산기")
st.write(
    "구매 개수가 많아질수록 개당 가격이 0.5%씩 할인되도록 계산합니다."
)

# -----------------------------
# 기본 물품 설정
# -----------------------------
st.subheader("물품 정보")

base_price = st.number_input(
    "기준 개당 가격 (원)",
    min_value=1,
    value=10000,
    step=100
)

# 최대 할인율 설정
max_discount = st.number_input(
    "최대 할인율 (%)",
    min_value=0.0,
    max_value=100.0,
    value=50.0,
    step=0.5
)

st.info(
    "1개 구매 시 할인율은 0%이며, 구매 개수가 1개 증가할 때마다 "
    "0.5%씩 할인됩니다."
)

# -----------------------------
# 구매자 수
# -----------------------------
st.subheader("구매자 정보")

people_count = st.number_input(
    "구매 인원",
    min_value=1,
    max_value=100,
    value=5,
    step=1
)

# 기본 데이터 생성
default_data = pd.DataFrame({
    "구매자": [f"구매자 {i+1}" for i in range(people_count)],
    "구매 개수": [1 for _ in range(people_count)]
})

# 표 입력
edited_df = st.data_editor(
    default_data,
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
        )
    }
)

# -----------------------------
# 계산
# -----------------------------
df = edited_df.copy()

# 숫자 변환 및 오류 방지
df["구매 개수"] = pd.to_numeric(
    df["구매 개수"],
    errors="coerce"
).fillna(1)

df["구매 개수"] = df["구매 개수"].astype(int)

# 할인율 계산
df["할인율"] = (df["구매 개수"] - 1) * 0.5

# 최대 할인율 제한
df["할인율"] = df["할인율"].clip(
    upper=max_discount
)

# 개당 가격 계산
df["개당 가격"] = (
    base_price * (1 - df["할인율"] / 100)
)

# 개인 총액
df["개인 총액"] = (
    df["개당 가격"] * df["구매 개수"]
)

# -----------------------------
# 결과 표시
# -----------------------------
st.subheader("계산 결과")

result_df = df[
    ["구매자", "구매 개수", "할인율", "개당 가격", "개인 총액"]
].copy()

# 화면 표시용 포맷
result_df["할인율"] = result_df["할인율"].map(
    lambda x: f"{x:.1f}%"
)

result_df["개당 가격"] = result_df["개당 가격"].map(
    lambda x: f"{x:,.0f}원"
)

result_df["개인 총액"] = result_df["개인 총액"].map(
    lambda x: f"{x:,.0f}원"
)

st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# 전체 통계
# -----------------------------
total_quantity = df["구매 개수"].sum()
total_cost = df["개인 총액"].sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "총 구매 인원",
        f"{len(df)}명"
    )

with col2:
    st.metric(
        "총 구매 개수",
        f"{total_quantity:,}개"
    )

with col3:
    st.metric(
        "전체 지출 금액",
        f"{total_cost:,.0f}원"
    )

# -----------------------------
# CSV 다운로드
# -----------------------------
csv_df = df[
    ["구매자", "구매 개수", "할인율", "개당 가격", "개인 총액"]
].copy()

csv = csv_df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="정산 결과 CSV 다운로드",
    data=csv,
    file_name="공동구매_정산결과.csv",
    mime="text/csv"
)
