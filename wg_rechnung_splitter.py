import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="WG-Rechnung Splitter", layout="wide")
st.title("WG-Rechnung Splitter")

# --- Eingaben ---
names_input = st.text_input(
    "Mitbewohner:innen (durch Komma getrennt, z.B. Emil, Daniel, Thalia, Greta):",
    "Ich, Daniel, Thalia, Greta"
)
names = [n.strip() for n in names_input.split(",") if n.strip()]

receipt_text = st.text_area(
    "Rechnungstext hier einfügen:", height=200
)

# Analyse-Button
def analyze():
    lines = receipt_text.splitlines()
    items = []
    detected_sum = None
    for line in lines:
        txt = line.strip()
        if not txt or txt.startswith('-'):
            continue
        if 'SUMME' in txt.upper():
            m_sum = re.search(r"([\d\.,]+)", txt)
            if m_sum:
                detected_sum = float(m_sum.group(1).replace(',', '.'))
            continue
        m = re.match(r'(?:(\d+)\s*x\s*)?(.+?)\s+([\d,]+)(?:\s+([\d,]+))?\s*(?:€|A)?$', txt)
        if not m:
            continue
        qty = int(m.group(1)) if m.group(1) else 1
        item = m.group(2).strip()
        p1 = float(m.group(3).replace(',', '.'))
        if m.group(4):
            unit_price = p1
            total_price = float(m.group(4).replace(',', '.'))
        else:
            total_price = p1
            unit_price = total_price / qty
        items.append({
            "Position": item,
            "Menge": qty,
            "Gesamtpreis (€)": round(total_price, 2)
        })
    st.session_state.df = pd.DataFrame(items)
    st.session_state.detected_sum = detected_sum
    # Init selection
    for i in range(len(st.session_state.df)):
        for n in names:
            key = f"sel_{i}_{n}"
            if key not in st.session_state:
                st.session_state[key] = True

if st.button("Rechnung analysieren") and receipt_text:
    analyze()

if 'df' in st.session_state:
    df = st.session_state.df
    detected_sum = st.session_state.detected_sum

    if df.empty:
        st.warning("Keine passenden Einträge gefunden. Bitte Rechnungstext prüfen.")
    else:
        st.write("#### Kosten-Zuordnung")
        cols = st.columns(2 + len(names))
        cols[0].write("**Item**")
        cols[1].write("**Preis**")
        for idx, n in enumerate(names):
            cols[2+idx].write(f"**{n}**")

        group_map = {}
        for i, row in df.iterrows():
            cols = st.columns(2 + len(names))
            cols[0].write(row['Position'])
            cols[1].write(f"{row['Gesamtpreis (€)']:.2f} €")
            for idx, n in enumerate(names):
                key = f"sel_{i}_{n}"
                cols[2+idx].checkbox(
                    label=n,
                    key=key
                )
            sel_group = tuple(sorted([n for n in names if st.session_state.get(f"sel_{i}_{n}", False)]))
            if sel_group:
                group_map.setdefault(sel_group, 0)
                group_map[sel_group] += row['Gesamtpreis (€)']

        st.write("#### Pakete für Splitwise")
        for grp, tot in group_map.items():
            people = ' '.join(grp)
            st.write(f"{tot:.2f} € an {people}")

