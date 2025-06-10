import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# 🔐 أدخل مفتاح API الخاص بك هنا (من football-data.org)
API_KEY = "6a1e99653712411aa2fce7ffe14f78a7"
HEADERS = {"X-Auth-Token": API_KEY}

# الاستراتيجيات

def strategy_1(data):
    return all(match['goals_scored'] > 0 for match in data)

def strategy_2(data):
    wins = sum(1 for match in data if match['result'] == 'W')
    return wins >= 4

def strategy_3(data):
    clean_sheets = sum(1 for match in data if match['goals_conceded'] == 0)
    return clean_sheets >= 3

def strategy_4(data):
    last_3 = data[-3:]
    return all(match['result'] == 'W' and match['goals_scored'] > 0 for match in last_3)

def strategy_5(data):
    avg_goals = sum(match['goals_scored'] for match in data) / len(data)
    return avg_goals >= 2.5

strategies = {
    "الاستقرار الهجومي": strategy_1,
    "قوة الفوز": strategy_2,
    "الأداء الدفاعي": strategy_3,
    "الفورمة المتكاملة": strategy_4,
    "ارتفاع متوسط الأهداف": strategy_5
}

# جلب معرف الفريق ضمن الدوري الإسباني

def get_team_id_from_competition(team_name, competition_code="PD"):
    url = f"https://api.football-data.org/v4/competitions/{competition_code}/teams"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    teams = response.json()
    for team in teams['teams']:
        if team_name.lower() in team['name'].lower():
            return team['id']
    return None

# جلب آخر N مباريات

def get_last_matches(team_id, count=5):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit={count}&status=FINISHED"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    matches = []
    for match in data['matches']:
        is_home = match['homeTeam']['id'] == team_id
        goals_scored = match['score']['fullTime']['home'] if is_home else match['score']['fullTime']['away']
        goals_conceded = match['score']['fullTime']['away'] if is_home else match['score']['fullTime']['home']
        result = "W" if goals_scored > goals_conceded else "L" if goals_scored < goals_conceded else "D"

        matches.append({
            "result": result,
            "goals_scored": goals_scored,
            "goals_conceded": goals_conceded
        })
    return matches

# محاكاة الرصيد

def simulate_balance(matches, bet_amount=100):
    balance = 0
    balance_list = []
    for match in matches:
        if match['result'] == 'W':
            balance += bet_amount * 0.9
        elif match['result'] == 'L':
            balance -= bet_amount
        balance_list.append(balance)
    return balance, balance_list

# حفظ النتائج إلى CSV

def save_matches_to_csv(matches, filename="matches.csv"):
    df = pd.DataFrame(matches)
    df.to_csv(filename, index=False)
    return filename

# واجهة Streamlit

st.title("⚽ محاكي استراتيجيات المراهنة - الدوري الإسباني")

team_name = st.text_input("أدخل اسم الفريق من الدوري الإسباني:", "Real Madrid")
bet_amount = st.number_input("قيمة الرهان لكل مباراة (بالدولار):", min_value=10, value=100, step=10)
match_count = st.slider("عدد المباريات الأخيرة للتحليل:", min_value=3, max_value=20, value=5, step=1)

if st.button("تحليل الفريق"):
    with st.spinner("جارٍ جلب البيانات من الدوري الإسباني..."):
        team_id = get_team_id_from_competition(team_name)
        if team_id:
            matches = get_last_matches(team_id, match_count)
            st.success(f"تم جلب آخر {len(matches)} مباريات لفريق {team_name}.")
            st.subheader("نتائج التحليل:")
            for name, strategy_func in strategies.items():
                result = strategy_func(matches)
                status = "✅ تراهن" if result else "❌ لا تراهن"
                st.write(f"- {name}: {status}")

            st.subheader("📈 محاكاة الرصيد:")
            balance, balance_progression = simulate_balance(matches, bet_amount)
            st.write(f"الربح/الخسارة التراكمية على آخر {len(matches)} مباريات: {balance:.2f} دولار")

            # رسم بياني لتطور الرصيد
            st.markdown("### تطور الرصيد:")
            fig, ax = plt.subplots()
            ax.plot(balance_progression, marker='o')
            ax.set_xlabel("رقم المباراة")
            ax.set_ylabel("الرصيد (دولار)")
            ax.set_title("تطور الرصيد عبر المباريات")
            st.pyplot(fig)

            # حفظ CSV
            st.markdown("### تحميل البيانات:")
            csv_path = save_matches_to_csv(matches)
            with open(csv_path, "rb") as f:
                st.download_button("📥 تحميل بيانات المباريات", data=f, file_name="matches.csv", mime="text/csv")

            # تفاصيل
            st.markdown("### تفاصيل المباريات الأخيرة:")
            for i, match in enumerate(matches, 1):
                st.write(f"{i}. نتيجة: {match['result']} | سجل: {match['goals_scored']} | استقبل: {match['goals_conceded']}")
        else:
            st.error("لم يتم العثور على الفريق ضمن الدوري الإسباني. تأكد من صحة الاسم.")
