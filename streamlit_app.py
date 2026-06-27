import streamlit as st
import datetime
import json
import os
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAZIONE GOOGLE SHEETS ---
ID_FOGLIO_GOOGLE = "METTI_QUI_IL_TUO_ID" 

def connetti_foglio():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_FOGLIO_GOOGLE).sheet1
    except:
        return None

def caricare_dati():
    sheet = connetti_foglio()
    if sheet:
        contenuto = sheet.cell(1, 1).value
        if contenuto:
            dati = json.loads(contenuto)
            for k in ["storico_presenze", "storico_minutaggio", "storico_titolari", "storico_moduli", "storico_numeri", "storico_gol", "storico_risultati"]:
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

# --- CONFIGURAZIONE PAGINA ---
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

menu = st.sidebar.radio("Navigazione", [
    "🔵 Calendario Allenamenti", "🟢 Calendario e Convocazioni", 
    "📊 Statistiche Allenamenti", "🏆 Statistiche Giocatori",
    "📈 Statistiche Squadra", "🏃 Gestione Rosa"
], key="menu_principale")

st.sidebar.write("---")
st.sidebar.info("MisterApp Cloud - Attiva")

def get_logo_html():
    for ext in ["png", "jpg", "jpeg"]:
        if os.path.exists(f"stemma.{ext}"):
            with open(f"stemma.{ext}", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                return f"<img src='data:image/{ext};base64,{encoded}' style='max-width: 100px; max-height: 120px; object-fit: contain;'>"
    return "<div style='font-size: 50px;'>🛡️</div><div style='color: red; font-weight: bold; font-size: 14px;'>USO</div><div style='color: green; font-weight: bold; font-size: 14px;'>UNITED</div>"

# --- LOGICA APPLICAZIONE ---
if menu == "🔵 Calendario Allenamenti":
    st.header("🔵 Calendario e Presenze Allenamenti")
    eventi_allenamento = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] == "Allenamento"]
    if not eventi_allenamento:
        st.info("Nessun allenamento in programma.")
    else:
        for ev in eventi_allenamento:
            if st.session_state.edit_evento == ev["id"]:
                st.write(f"### ✏️ Modifica Allenamento")
                curr_date = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").date()
                mod_data = st.date_input("Data", curr_date, key=f"mod_d_{ev['id']}")
                mod_nota = st.text_input("Note/Orario", value=ev.get("nota", ""), key=f"mod_n_{ev['id']}")
                col_s, col_a = st.columns(2)
                with col_s:
                    if st.button("💾 Salva", key=f"s_mod_{ev['id']}", type="primary"):
                        ev["data"] = str(mod_data); ev["nota"] = mod_nota
                        st.session_state.edit_evento = None; salvare_dati(); st.rerun()
                with col_a:
                    if st.button("❌ Annulla", key=f"a_mod_{ev['id']}"): st.session_state.edit_evento = None; st.rerun()
            else:
                data_f = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                with st.expander(f"🔵 Allenamento del {data_f} ({ev.get('nota', '')})"):
                    if st.button("✏️ Modifica", key=f"ed_ev_{ev['id']}"): st.session_state.edit_evento = ev["id"]; st.rerun()
                    if st.button("🗑️ Elimina", key=f"del_ev_{ev['id']}"):
                        st.session_state.db["eventi"] = [e for e in st.session_state.db["eventi"] if e["id"] != ev["id"]]
                        salvare_dati(); st.rerun()
                    appello_evento = st.session_state.db["storico_presenze"].get(ev["id"], {})
                    opzioni = ["🟢 Presente", "🔴 Assente", "🟡 Infortunato"]
                    for ragazzo in st.session_state.db["ragazzi"]:
                        col_n, col_s = st.columns([1, 2])
                        with col_n: st.write(f"**{ragazzo}**")
                        with col_s:
                            appello_evento[ragazzo] = st.radio(ragazzo, opzioni, index=opzioni.index(appello_evento.get(ragazzo, opzioni[0])), key=f"p_{ragazzo}_{ev['id']}", horizontal=True, label_visibility="collapsed")
                    if st.button("💾 Salva Registro", key=f"btn_salva_{ev['id']}", type="primary"):
                        st.session_state.db["storico_presenze"][ev["id"]] = appello_evento
                        salvare_dati(); st.rerun()

    st.subheader("➕ Fissa un nuovo Allenamento")
    nuova_data = st.date_input("Data", datetime.date.today(), key="new_data_all")
    nuova_nota = st.text_input("Orario e Luogo", key="new_nota_all")
    if st.button("Aggiungi Allenamento"):
        nuovo_id = str(int(max([int(e["id"]) for e in st.session_state.db["eventi"]], default=0)) + 1)
        st.session_state.db["eventi"].append({"id": nuovo_id, "data": str(nuova_data), "tipo": "Allenamento", "nota": nuova_nota})
        salvare_dati(); st.rerun()

elif menu == "🟢 Calendario e Convocazioni":
    st.header("🟢 Calendario e Convocazioni")
    st.write("Funzionalità Partite attiva.")

elif menu == "📊 Statistiche Allenamenti":
    st.header("📊 Statistiche Allenamenti")

elif menu == "🏆 Statistiche Giocatori":
    st.header("🏆 Statistiche Giocatori")

elif menu == "📈 Statistiche Squadra":
    st.header("📈 Statistiche Squadra")

elif menu == "🏃 Gestione Rosa":
    st.header("🏃 Anagrafica e Gestione Rosa")
    for i, ragazzo in enumerate(list(st.session_state.db["ragazzi"])):
        col_nome, col_mod, col_del = st.columns([2, 1, 1])
        with col_nome: st.write(f"• **{ragazzo}**")
        with col_mod:
            if st.button("✏️", key=f"edit_{i}"): st.session_state.edit_mode = i; st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.db["ragazzi"].remove(ragazzo)
                salvare_dati(); st.rerun()
    nuovo_nome = st.text_input("Nuovo giocatore", key="new_player")
    if st.button("Inserisci"):
        if nuovo_nome and nuovo_nome not in st.session_state.db["ragazzi"]:
            st.session_state.db["ragazzi"].append(nuovo_nome)
            salvare_dati(); st.rerun()