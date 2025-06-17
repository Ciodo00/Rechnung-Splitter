import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="WG-Rechnung Splitter", layout="wide")
st.title("WG-Rechnung Splitter")

# --- Eingaben ---
names_input = st.text_input(
    "Mitbewohner:innen (durch Komma getrennt, z.B. Ich, Daniel, Thalia, Greta):",
    "Ich, Daniel, Thalia, Greta"
)
names = [n.strip() for n in names_input.split(',') if n.strip()]

receipt_text = st.text_area(
    "Rechnungstext hier einfügen:", height=200
)

# Analyse-Button
def analyze():
    raw_lines = [l.strip() for l in receipt_text.splitlines() if l.strip()]
    # 1) Kombiniere Zeilen: Name ohne Preis + Folgelinie mit Menge/Preis
    combined = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        # detect next line as qty x unit total
        if i + 1 < len(raw_lines) and re.match(r"^\d+\s*x\s*[\d,]+\s+[\d,]+", raw_lines[i+1]):
            combined.append(f"{line} {raw_lines[i+1]}")
            i += 2
        else:
            combined.append(line)
            i += 1
    # 2) Parsen
    items = []
    detected_sum = None
    # pattern: desc + optional qty x unit + optional total
    pat = re.compile(r"^(.+?)\s+(?:(\d+)\s*x\s*)?([\d,]+)(?:\s+([\d,]+))?\s*(?:€|A)?$")
    for line in combined:
        if line.upper().startswith('SUMME'):
            m_sum = re.search(r"([\d\.,]+)", line)
            if m_sum:
                detected_sum = float(m_sum.group(1).replace(',', '.'))
            continue
        m = pat.match(line)
        if not m:
            continue
        desc = m.group(1).strip()
        qty = int(m.group(2)) if m.group(2) else 1
        num1 = float(m.group(3).replace(',', '.'))
        if m.group(4):
            unit_price = num1
            total_price = float(m.group(4).replace(',', '.'))
        else:
            total_price = num1
            unit_price = total_price / qty
        items.append({
            "Position": desc,
            "Menge": qty,
            "Gesamtpreis (€)": round(total_price, 2)
        })
    st.session_state.df = pd.DataFrame(items)
    st.session_state.detected_sum = detected_sum
    # init selection
    for i in range(len(st.session_state.df)):
        for n in names:
            key = f"sel_{i}_{n}"
            if key not in st.session_state:
                st.session_state[key] = True

if st.button("Rechnung analysieren") and receipt_text:
    analyze()

# Anzeige & Zuordnung
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
                cols[2+idx].checkbox(label=n, key=key)
            sel_group = tuple(sorted([n for n in names if st.session_state.get(f"sel_{i}_{n}", False)]))
            if sel_group:
                group_map.setdefault(sel_group, 0)
                group_map[sel_group] += row['Gesamtpreis (€)']
        st.write("#### Pakete für Splitwise")
        for grp, tot in group_map.items():
            people = ' '.join(grp)
            st.write(f"{tot:.2f} € an {people}")
        # optional: Summe prüfen
        if detected_sum is not None:
            calc = df['Gesamtpreis (€)'].sum().round(2)
            if abs(calc - detected_sum) > 0.01:
                st.warning(f"Berechnete Summe {calc} € stimmt nicht mit Rechnungssumme {detected_sum} € überein.")
            else:
                st.success(f"Berechnete Summe {calc} € stimmt mit Rechnungssumme überein.")
# Anleitung
st.markdown("---")
st.markdown(
"""
**Anleitung:**
1. Speichere als `wg_rechnung_splitter.py`.
2. Erstelle `requirements.txt` mit:
```
streamlit
pandas
```
3. Installiere:
```
pip install -r requirements.txt
```
4. Starte:
```
streamlit run wg_rechnung_splitter.py
```
"""
)
