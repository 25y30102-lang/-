import streamlit as st
import requests
import datetime
import pytz
import re
import pandas as pd
import plotly.express as px

# --------------------------
# Streamlit 설정
# --------------------------
st.set_page_config(
    page_title="상암고 예술적 급식 대시보드",
    page_icon="🎨🍱",
    layout="wide",
)
st.markdown(
    "<h1 style='text-align:center;color:#FF5733;'>🍱 상암고 주간 급식 & 영양 대시보드</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#555;'>달력에서 날짜 선택 → 이번 주 메뉴와 영양소 추세 확인</p>",
    unsafe_allow_html=True,
)

# --------------------------
# 날짜 선택
# --------------------------
kst = pytz.timezone("Asia/Seoul")
today = datetime.datetime.now(kst).date()
selected_date = st.date_input("📅 날짜 선택", today)

# --------------------------
# 이번 주 월~금 날짜
# --------------------------
monday = today - datetime.timedelta(days=today.weekday())
week_dates = [monday + datetime.timedelta(days=i) for i in range(5)]
week_dates_str = [d.strftime("%y%m%d") for d in week_dates]
week_days = ["월", "화", "수", "목", "금"]

# --------------------------
# 데이터 수집 함수
# --------------------------
def fetch_meal(date_str):
    url = (
        "https://open.neis.go.kr/hub/mealServiceDietInfo"
        "?ATPT_OFCDC_SC_CODE=B10"
        "&SD_SCHUL_CODE=7010806"
        "&Type=json"
        f"&MLSV_YMD={date_str}"
    )
    res = requests.get(url)
    try:
        data = res.json()
        info = data.get("mealServiceDietInfo", None)
        if info is None:
            return None
        return info[1]["row"]
    except:
        return None

# --------------------------
# 선택한 날짜 급식 표시
# --------------------------
selected_str = selected_date.strftime("%y%m%d")
selected_rows = fetch_meal(selected_str)

st.subheader(f"📌 선택한 날짜 ({selected_date.strftime('%Y-%m-%d')}) 급식")
if selected_rows is None:
    st.warning("선택한 날짜 급식 데이터가 없습니다.")
else:
    for idx, row in enumerate(selected_rows):
        dish = row["DDISH_NM"].replace("<br/>", ", ")
        dish_clean = re.sub(r"\d", "", dish).replace("(", "").replace(")", "").replace(".", "")
        st.markdown(f"**{row['MMEAL_SC_NM']}**")
        st.markdown(
            f"""
<div style="
background: linear-gradient(90deg,#ffecd2,#fcb69f);
padding:15px;
border-radius:12px;
font-size:16px;
font-weight:bold;
color:#333;
margin-bottom:10px;
">
{dish_clean}
</div>
""",
            unsafe_allow_html=True,
        )

# --------------------------
# 이번 주 전체 데이터 가져오기
# --------------------------
weekly_data = []
for d_str, d_day in zip(week_dates_str, week_days):
    rows = fetch_meal(d_str)
    if rows is None:
        rows = [{"MMEAL_SC_NM": "중식", "DDISH_NM": "김밥<br/>우동<br/>사과"}]
    for idx, row in enumerate(rows):
        dish = row["DDISH_NM"].replace("<br/>", ", ")
        dish_clean = re.sub(r"\d", "", dish).replace("(", "").replace(")", "").replace(".", "")
        # 영양소
        nutri_keys = ["CAL_INFO", "NTR_INFO_CAR", "NTR_INFO_PRO", "NTR_INFO_FAT", "NTR_INFO_NA"]
        nutri_names = ["칼로리(kcal)", "탄수화물(g)", "단백질(g)", "지방(g)", "나트륨(mg)"]
        numeric_nutri = {}
        for key, name in zip(nutri_keys, nutri_names):
            val = row.get(key, "-")
            try:
                num = float(re.findall(r"[\d.]+", val.replace("-", "0"))[0])
                numeric_nutri[name] = num
            except:
                numeric_nutri[name] = 0
        weekly_data.append({
            "요일": d_day,
            "식사": row["MMEAL_SC_NM"],
            "메뉴": dish_clean,
            "idx": idx,
            **numeric_nutri
        })

df_week = pd.DataFrame(weekly_data)

# --------------------------
# 이번 주 메뉴 카드형 표시
# --------------------------
st.subheader("🍴 이번 주 전체 메뉴")
cols = st.columns(5)
colors = ["#f6d365", "#fda085", "#fbc2eb", "#a1c4fd", "#c2e9fb"]
for i, d_day in enumerate(week_days):
    df_day = df_week[df_week["요일"] == d_day]
    with cols[i]:
        st.markdown(f"### {d_day}요일")
        for _, row in df_day.iterrows():
            st.markdown(
                f"""
<div style="
background: {colors[i]};
padding:12px;
margin-bottom:6px;
border-radius:10px;
font-weight:bold;
color:#222;
">
<b>{row['식사']}</b><br>{row['메뉴']}
</div>
""",
                unsafe_allow_html=True,
            )

# --------------------------
# 영양소 막대그래프
# --------------------------
st.subheader("📊 주간 영양소 막대 그래프")
nutrients = ["칼로리(kcal)", "탄수화물(g)", "단백질(g)", "지방(g)", "나트륨(mg)"]
for nut in nutrients:
    fig = px.bar(
        df_week,
        x="요일",
        y=nut,
        color="식사",
        text=nut,
        title=f"{nut} 주간 비교",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis=dict(title=nut))
    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# 영양소 추세선(Line chart)
# --------------------------
st.subheader("📈 주간 영양소 추세선")
fig_line = px.line(
    df_week,
    x="요일",
    y=nutrients,
    markers=True,
    title="주간 영양소 추세",
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.T10
)
fig_line.update_layout(yaxis_title="영양소 수치")
st.plotly_chart(fig_line, use_container_width=True)
