import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="WG-Rechnung Splitter", layout="wide")
st.title("WG-Rechnung Splitter")

# 1. Namen der Mitbewohner:innen
names_input = st.text_input(
    "Mitbewohner:innen (durch Komma getrennt, z.B. Ich, Daniel, Thalia, Greta):",
    "Ich, Daniel, Thalia, Greta"
)
names = [n.strip() for n in names_input.split(",") if n.strip()]

st.markdown("### 2. Rechnungstext einfügen")
receipt_text = st.text_area(
    "Hier den kopierten Text der digitalen Rechnung einfügen:",
    height=200
)

if st.button("3. Rechnung analysieren"):
    # 3. Parsen der Zeilen
    lines = receipt_text.splitlines()
    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('-') or 'SUMME' in line.upper():
            continue
        # Erkennung von "2 x 1,99 3,98" oder "SPAR VOGERLSALAT 1,79"
        m = re.match(r'(?:(\d+)\s*x\s*)?(.+?)\s+([\d,]+)\s*(?:€|A)?$', line)
        if m:
            qty = int(m.group(1)) if m.group(1) else 1
            item = m.group(2)
            price_str = m.group(3).replace(',', '.')
            total_price = float(price_str)
            unit_price = total_price / qty
            data.append({
                "Position": item,
                "Menge": qty,
                "Einzelpreis (€)": round(unit_price, 2),
                "Gesamtpreis (€)": round(total_price, 2)
            })

    df = pd.DataFrame(data)
    if df.empty:
        st.warning("Keine passenden Einträge gefunden. Bitte Text überprüfen.")
    else:
        # 4. Anzeige der geparsten Positionen
        st.write("#### Gefundene Positionen")
        st.dataframe(df)

        # 5. Zuordnung der Kosten
        st.markdown("#### Kosten-Zuordnung")
        assignments = {}
        for idx, row in df.iterrows():
            sel = st.multiselect(
                f"Wem zuordnen: **{row['Position']}** ({row['Gesamtpreis (€)']:.2f} €)",
                names,
                default=names,
                key=f"sel_{idx}"
            )
            assignments[idx] = sel

        # 6. Summen berechnen
        sums = {name: 0.0 for name in names}
        for idx, sel in assignments.items():
            if sel:
                share = df.loc[idx, 'Gesamtpreis (€)'] / len(sel)
                for name in sel:
                    sums[name] += share

        summary_df = pd.DataFrame(
            [(n, round(s, 2)) for n, s in sums.items()],
            columns=["Name", "Betrag (€)"]
        )
        st.write("#### Zusammenfassung")
        st.dataframe(summary_df)

        st.markdown(
            "**Fertig!** Kopiere die Beträge und trage sie in Splitwise ein."
        )

# 7. Hinweis zur lokalen Nutzung
st.markdown("---\n\n"
    "**Anleitung:**\n\n"
    "1. Speichere dieses Skript als `wg_rechnung_splitter.py`.\n"
    "2. Installiere Python-Pakete:  `pip install streamlit pandas`\n"
    "3. Starte die App mit:\n"
    "   ```bash\n"
    "   streamlit run wg_rechnung_splitter.py\n"
    "   ```\n"
)
