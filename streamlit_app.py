import streamlit as st
import datetime
import json
import gspread
import base64
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAZIONE GOOGLE SHEETS ---
ID_FOGLIO_GOOGLE = "METTI_QUI_IL_TUO_ID" 

def connetti_foglio():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_FOGLIO_GOOGLE).sheet1
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
        return None

def caricare_dati():
    sheet = connetti_foglio()
    if sheet:
        contenuto = sheet.cell(1, 1).value
        if contenuto:
            dati = json.loads(contenuto)
            # Verifica che le chiavi esistano
            for k in ["storico_minutaggio", "storico_titolari", "storico_moduli", "storico_numeri", "storico_gol", "storico_risultati"]:
                if k not in dati: dati[k] = {}
            return dati
    return {
        "ragazzi": ["Luca R.", "Matteo V.", "Alessandro M.", "Filippo T.", "Gabriele L.", "Tommaso N."],
        "eventi": [
            {"id": "1", "data": "2026-06-23", "tipo": "Allenamento", "nota": "Campo Principale - ore 17:30"},
            {"id": "2", "data": "2026-06-27", "tipo": "Partita", "avversario": "Real City", "luogo": "Trasferta", "ora_partita": "15:00", "ora_convocazione": "14:00", "indirizzo": "Via Stadio 5, Torino", "nota": "Campionato"}
        ],
        "storico_presenze": {}, "storico_minutaggio": {}, "storico_titolari": {},
        "storico_moduli": {}, "storico_numeri": {}, "storico_gol": {}, "storico_risultati": {}
    }

def salvare_dati():
    sheet = connetti_foglio()
    if sheet:
        stringa_json = json.dumps(st.session_state.db, ensure_ascii=False)
        sheet.update_cell(1, 1, stringa_json)

# --- SETUP PAGINA ---
st.set_page_config(page_title="MisterApp - Settore Giovanile", layout="centered")

st.markdown("""
    <style>
    .card { background-color: var(--secondary-background-color); color: var(--text-color); border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }
    [data-testid="stSidebar"] div[role="radiogroup"] label { padding: 12px 15px !important; margin-bottom: 10px !important; background-color: var(--secondary-background-color); border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
    [data-testid="stSidebar"] div[role="radiogroup"] label p { font-size: 18px !important; font-weight: 600 !important; color: var(--text-color) !important; }
    </style>
""", unsafe_allow_html=True)

if "db" not in st.session_state:
    st.session_state.db = caricare_dati()

if "edit_mode" not in st.session_state: st.session_state.edit_mode = None
if "edit_evento" not in st.session_state: st.session_state.edit_evento = None

# --- MENU LATERALE ---
menu = st.sidebar.radio("Navigazione", [
    "🔵 Calendario Allenamenti", "🟢 Calendario e Convocazioni", 
    "📊 Statistiche Allenamenti", "🏆 Statistiche Giocatori",
    "📈 Statistiche Squadra", "🏃 Gestione Rosa"
], key="menu_principale")

st.sidebar.write("---")
st.sidebar.info("MisterApp Cloud - Attiva")

def get_logo_html():
    return "<div style='font-size: 50px;'>🛡️</div><div style='color: red; font-weight: bold; font-size: 14px;'>USO</div><div style='color: green; font-weight: bold; font-size: 14px;'>UNITED</div>"

# --- LOGICA APP ---
if menu == "🔵 Calendario Allenamenti":
    st.header("🔵 Calendario e Presenze Allenamenti")
    eventi_allenamento = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] == "Allenamento"]
    for ev in eventi_allenamento:
        if st.session_state.edit_evento == ev["id"]:
            curr_date = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").date()
            mod_data = st.date_input("Data", curr_date, key=f"mod_d_{ev['id']}")
            mod_nota = st.text_input("Note/Orario", value=ev.get("nota", ""), key=f"mod_n_{ev['id']}")
            if st.button("💾 Salva", key=f"s_{ev['id']}"):
                ev["data"] = str(mod_data); ev["nota"] = mod_nota; st.session_state.edit_evento = None; salvare_dati(); st.rerun()
        else:
            with st.expander(f"🔵 Allenamento del {ev['data']} ({ev.get('nota', '')})"):
                if st.button("✏️ Modifica", key=f"ed_{ev['id']}"): st.session_state.edit_evento = ev["id"]; st.rerun()
                if st.button("🗑️ Elimina", key=f"del_{ev['id']}"):
                    st.session_state.db["eventi"] = [e for e in st.session_state.db["eventi"] if e["id"] != ev["id"]]
                    salvare_dati(); st.rerun()
                appello = st.session_state.db["storico_presenze"].get(ev["id"], {})
                for ragazzo in st.session_state.db["ragazzi"]:
                    appello[ragazzo] = st.radio(ragazzo, ["🟢 Presente", "🔴 Assente", "🟡 Infortunato"], index=["🟢 Presente", "🔴 Assente", "🟡 Infortunato"].index(appello.get(ragazzo, "🟢 Presente")), key=f"p_{ragazzo}_{ev['id']}", horizontal=True)
                if st.button("💾 Salva Registro", key=f"save_{ev['id']}"):
                    st.session_state.db["storico_presenze"][ev["id"]] = appello; salvare_dati(); st.rerun()
    st.subheader("➕ Aggiungi Allenamento")
    nuova_data = st.date_input("Data", datetime.date.today(), key="new_d")
    nuova_nota = st.text_input("Orario/Luogo", key="new_n")
    if st.button("Aggiungi"):
        nuovo_id = str(int(max([int(e["id"]) for e in st.session_state.db["eventi"]], default=0)) + 1)
        st.session_state.db["eventi"].append({"id": nuovo_id, "data": str(nuova_data), "tipo": "Allenamento", "nota": nuova_nota})
        salvare_dati(); st.rerun()

elif menu == "🟢 Calendario e Convocazioni":
    st.header("🟢 Calendario e Convocazioni")
    eventi = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] in ["Partita", "Torneo"]]
    for ev in eventi:
        with st.expander(f"🟢 {ev.get('avversario')} del {ev['data']}"):
            st.write(f"Ora: {ev.get('ora_partita')} | Luogo: {ev.get('indirizzo')}")
            # ... (Qui puoi incollare il resto della tua logica partite) ...

elif menu == "📊 Statistiche Allenamenti":
    st.header("📊 Statistiche Allenamenti")
    storico = st.session_state.db["storico_presenze"]
    id_all = [ev["id"] for ev in st.session_state.db["eventi"] if ev["tipo"] == "Allenamento"]
    tabella = []
    for r in st.session_state.db["ragazzi"]:
        presenti = sum(1 for id in id_all if storico.get(id, {}).get(r) == "🟢 Presente")
        tabella.append({"Giocatore": r, "Presenze": presenti})
    st.table(tabella)

elif menu == "🏆 Statistiche Giocatori":
    st.header("🏆 Statistiche Giocatori")
    st.table(st.session_state.db["storico_gol"])

elif menu == "📈 Statistiche Squadra":
    st.header("📈 Statistiche Squadra")

elif menu == "🏃 Gestione Rosa":
    st.header("🏃 Gestione Rosa")
    for i, ragazzo in enumerate(list(st.session_state.db["ragazzi"])):
        col1, col2 = st.columns([3, 1])
        with col1: st.write(f"• {ragazzo}")
        with col2:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.db["ragazzi"].remove(ragazzo); salvare_dati(); st.rerun()
    nuovo = st.text_input("Nuovo nome")
    if st.button("Aggiungi"):
        if nuovo and nuovo not in st.session_state.db["ragazzi"]:
            st.session_state.db["ragazzi"].append(nuovo); salvare_dati(); st.rerun()