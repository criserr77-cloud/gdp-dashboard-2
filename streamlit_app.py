import streamlit as st
import pandas as pd
import datetime
import json
import os
import base64
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAZIONE GOOGLE SHEETS ---
ID_FOGLIO_GOOGLE = "1PCmJ9tgv-ohAIuc3CmwP4BOZLg68qSLmkLYwSQ7pSsc" 

# --- CONFIGURAZIONE REGOLAMENTO ---
MAX_TITOLARI = 9  # Numero massimo di titolari selezionabili per partita (es. 9 per il calcio a 9)

# --- CONFIGURAZIONE COLORI (tema Blu/Verde) ---
COLORE_BLU = "#1565C0"          
COLORE_BLU_CHIARO = "#E3F2FD"   
COLORE_VERDE = "#2E7D32"        
COLORE_VERDE_CHIARO = "#E8F5E9" 

# Genera gli orari per la selezione (da 09:00 a 18:00 a step di mezz'ora)
orari_partita = []
for h in range(9, 19):
    orari_partita.append(f"{h:02d}:00")
    if h != 18:
        orari_partita.append(f"{h:02d}:30")

# Opzioni campi per le partite in casa
OPZIONI_CAMPI_CASA = [
    "Campo Prealpino Santa Giulia Via del brolo 7",
    "Campo Comunale Coltrini Parco Urbano Bovezzo"
]

OPZIONI_CAMPI_ALLENAMENTO = [
    "Campo Prealpino Santa Giulia Via del brolo 7",
    "Campo Comunale Coltrini Parco Urbano Bovezzo"
]

orari_allenamento = []
for h in range(14, 22):
    orari_allenamento.append(f"{h:02d}:00")
    orari_allenamento.append(f"{h:02d}:30")

def connetti_foglio():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        return client.open_by_key(ID_FOGLIO_GOOGLE).sheet1
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return None

def caricare_dati():
    sheet = connetti_foglio()
    if sheet:
        try:
            contenuto = sheet.acell('A1').value
            if contenuto:
                dati = json.loads(contenuto)
                # Inizializza nuove chiavi se mancano
                for k in ["storico_presenze", "storico_minutaggio", "storico_titolari", "storico_moduli", 
                          "storico_numeri", "storico_gol", "storico_risultati", "anagrafica_ruolo", 
                          "anagrafica_nascita", "storico_capitano", "storico_vicecapitano"]:
                    if k not in dati: dati[k] = {}
                return dati
        except Exception:
            pass 
            
    return {
        "ragazzi": ["Luca R.", "Matteo V.", "Alessandro M.", "Filippo T.", "Gabriele L.", "Tommaso N."],
        "eventi": [],
        "storico_presenze": {}, "storico_minutaggio": {}, "storico_titolari": {},
        "storico_moduli": {}, "storico_numeri": {}, "storico_gol": {}, "storico_risultati": {},
        "anagrafica_ruolo": {}, "anagrafica_nascita": {}, "storico_capitano": {}, "storico_vicecapitano": {}
    }

def salvare_dati():
    try:
        sheet = connetti_foglio()
        if sheet:
            stringa_json = json.dumps(st.session_state.db, ensure_ascii=False, indent=4)
            sheet.update_acell('A1', stringa_json)
    except Exception as e:
        st.error(f"❌ ERRORE DI SALVATAGGIO: {e}")
        st.stop()

st.set_page_config(page_title="MisterApp", layout="centered")

# --- CSS DEFINITIVO ---
st.markdown(f"""
    <style>
    .card {{ 
        background-color: var(--secondary-background-color); 
        border-radius: 15px; padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        margin-bottom: 20px; 
        border: 1px solid {COLORE_VERDE};
    }}
    
    [data-testid="stSidebar"] {{
        border-right: 2px solid {COLORE_VERDE};
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label {{
        padding: 18px 20px !important;
        margin-bottom: 12px !important;
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        border: 1px solid {COLORE_BLU};
        cursor: pointer;
        transition: border-color 0.2s ease;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        border-color: {COLORE_VERDE};
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label p {{
        font-size: 22px !important;
        font-weight: bold !important;
        color: var(--text-color) !important;
    }}

    button[kind="primary"], .stButton button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORE_BLU} 0%, {COLORE_VERDE} 100%) !important;
        border: none !important;
        color: white !important;
    }}

    h1, h2 {{
        border-left: 5px solid {COLORE_VERDE};
        padding-left: 12px;
    }}
    </style>
""", unsafe_allow_html=True)

def genera_pdf(html_content):
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
    except ImportError:
        st.error("Manca la libreria 'xhtml2pdf'. Aggiungila al file requirements.txt e riavvia l'app.")
        return None
    try:
        documento_completo = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{ size: A4; margin: 1.5cm; }}
    html, body {{ background-color: white; margin: 0; padding: 0; }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(documento_completo.encode("UTF-8")), result)
        if not pdf.err:
            return result.getvalue()
        return None
    except Exception as e:
        st.error(f"Errore nella generazione del PDF: {e}")
        return None

def get_logo_html(per_pdf=False):
    for ext in ["png", "jpg", "jpeg"]:
        if os.path.exists(f"stemma.{ext}"):
            with open(f"stemma.{ext}", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                if per_pdf:
                    return f"<img src='data:image/{ext};base64,{encoded}' width='90' height='100' style='width:90px; height:100px;'>"
                return f"<img src='data:image/{ext};base64,{encoded}' style='max-width: 100px; max-height: 120px; object-fit: contain;'>"
    if per_pdf:
        return "<div style='font-size: 40px;'>&#9812;</div>"
    return "<div style='font-size: 50px;'>🛡️</div>"

def dividi_nome(giocatore):
    parti = str(giocatore).split(" ", 1)
    nome = parti[0]
    cognome = parti[1] if len(parti) > 1 else ""
    return nome, cognome

def cognome_nome(giocatore):
    nome, cognome = dividi_nome(giocatore)
    return f"{cognome} {nome}".strip() if cognome else nome

def ordina_giocatori(lista_giocatori):
    return sorted(lista_giocatori, key=lambda g: (dividi_nome(g)[1].lower(), dividi_nome(g)[0].lower()))

# Inizializzazione Session State
if "db" not in st.session_state: 
    st.session_state.db = caricare_dati()
    if "anagrafica_ruolo" not in st.session_state.db: st.session_state.db["anagrafica_ruolo"] = {}
    if "anagrafica_nascita" not in st.session_state.db: st.session_state.db["anagrafica_nascita"] = {}
    if "storico_capitano" not in st.session_state.db: st.session_state.db["storico_capitano"] = {}
    if "storico_vicecapitano" not in st.session_state.db: st.session_state.db["storico_vicecapitano"] = {}

if "rosa_editor_version" not in st.session_state: st.session_state.rosa_editor_version = 0
if "edit_evento" not in st.session_state: st.session_state.edit_evento = None

menu = st.sidebar.radio("Navigazione", [
    "🔵 Calendario Allenamenti", "🟢 Calendario e Convocazioni", 
    "📊 Statistiche Allenamenti", "🏆 Statistiche Giocatori", 
    "📈 Statistiche Squadra", "🏃 Gestione Rosa"
])

# ==========================================
# SCHERMATA 1: ALLENAMENTI
# ==========================================
if menu == "🔵 Calendario Allenamenti":
    st.header("🔵 Calendario e Presenze Allenamenti")
    
    st.subheader("I tuoi Allenamenti:")
    eventi_allenamento = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] == "Allenamento"]
    
    if not eventi_allenamento:
        st.info("Nessun allenamento in programma.")
    else:
        for ev in eventi_allenamento:
            if st.session_state.edit_evento == ev["id"]:
                st.write(f"### ✏️ Modifica Allenamento")
                curr_date = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").date()
                mod_data = st.date_input("Data", curr_date, key=f"mod_d_{ev['id']}")
                
                ora_attuale = ev.get("ora", "17:30")
                idx_ora = orari_allenamento.index(ora_attuale) if ora_attuale in orari_allenamento else 0
                mod_ora = st.selectbox("Orario", orari_allenamento, index=idx_ora, key=f"mod_o_{ev['id']}")
                
                campo_attuale = ev.get("indirizzo", OPZIONI_CAMPI_ALLENAMENTO[0])
                idx_campo = OPZIONI_CAMPI_ALLENAMENTO.index(campo_attuale) if campo_attuale in OPZIONI_CAMPI_ALLENAMENTO else 0
                mod_campo = st.selectbox("Campo", OPZIONI_CAMPI_ALLENAMENTO, index=idx_campo, key=f"mod_c_{ev['id']}")
                
                mod_nota = st.text_input("Note aggiuntive (opzionale)", value=ev.get("nota", ""), key=f"mod_n_{ev['id']}")
                
                col_s, col_a = st.columns(2)
                with col_s:
                    if st.button("💾 Salva", key=f"s_mod_{ev['id']}", type="primary"):
                        ev["data"] = str(mod_data)
                        ev["nota"] = mod_nota
                        ev["ora"] = mod_ora
                        ev["indirizzo"] = mod_campo
                        st.session_state.edit_evento = None
                        salvare_dati()
                        st.rerun()
                with col_a:
                    if st.button("❌ Annulla", key=f"a_mod_{ev['id']}"):
                        st.session_state.edit_evento = None
                        st.rerun()
                st.write("---")
            else:
                data_f = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                dettagli = []
                if "ora" in ev: dettagli.append(ev["ora"])
                if "indirizzo" in ev: dettagli.append(ev["indirizzo"])
                if ev.get("nota", ""): dettagli.append(ev["nota"])
                titolo_box = f"🔵 Allenamento del {data_f}"
                if dettagli:
                    titolo_box += " - " + " | ".join(dettagli)
                else:
                    titolo_box += f" ({ev.get('nota', '')})"
                
                with st.expander(titolo_box):
                    col_mod, col_del = st.columns([1, 1])
                    with col_mod:
                        if st.button("✏️ Modifica", key=f"ed_ev_{ev['id']}"):
                            st.session_state.edit_evento = ev["id"]
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Elimina", key=f"del_ev_{ev['id']}"):
                            st.session_state.db["eventi"] = [e for e in st.session_state.db["eventi"] if e["id"] != ev["id"]]
                            if ev["id"] in st.session_state.db["storico_presenze"]: del st.session_state.db["storico_presenze"][ev["id"]]
                            salvare_dati()
                            st.rerun()
                    
                    st.write("---")
                    
                    wa_text = f"Ciao a tutti,\n\n🔵 *PROSSIMO ALLENAMENTO* 🔵\n📅 *Data:* {data_f}\n"
                    if ev.get('ora', ''): wa_text += f"⏰ *Ora:* {ev['ora']}\n"
                    if ev.get('indirizzo', ''): wa_text += f"📍 *Luogo:* {ev['indirizzo']}\n"
                    if ev.get("nota", "").strip(): wa_text += f"📝 *Note:* {ev['nota'].strip()}\n"
                    wa_text += "\nGrazie 💚💙"
                    st.code(wa_text, language="markdown")
                    wa_url = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(wa_text)
                    if hasattr(st, "link_button"):
                        st.link_button("📲 Apri WhatsApp con questo messaggio", wa_url, key=f"wa_all_{ev['id']}")
                    else:
                        st.markdown(f"[📲 Apri WhatsApp con questo messaggio]({wa_url})")

                    st.write("---")
                    st.write(f"#### 📋 Registro Presenze")
                    
                    if not st.session_state.db["ragazzi"]:
                        st.warning("Rosa vuota.")
                    else:
                        appello_evento = st.session_state.db["storico_presenze"].get(ev["id"], {})
                        resoconto_corrente = {}
                        opzioni = ["🟢 Presente", "🔴 Assente", "🟡 Infortunato"]
                        
                        for ragazzo in ordina_giocatori(st.session_state.db["ragazzi"]):
                            col_nome, col_stato = st.columns([1, 2])
                            with col_nome: st.write(f"**{cognome_nome(ragazzo)}**")
                            with col_stato:
                                stato_precedente = appello_evento.get(ragazzo, opzioni[0])
                                indice_default = opzioni.index(stato_precedente) if stato_precedente in opzioni else 0
                                stato = st.radio(f"Stato_{ragazzo}_{ev['id']}", opzioni, index=indice_default, horizontal=True, label_visibility="collapsed", key=f"p_{ragazzo}_{ev['id']}")
                                resoconto_corrente[ragazzo] = stato
                        
                        st.write("")
                        if st.button("💾 Salva Registro", key=f"btn_salva_{ev['id']}", type="primary"):
                            st.session_state.db["storico_presenze"][ev["id"]] = resoconto_corrente
                            salvare_dati()
                            st.success("Presenze salvate!")
                            st.rerun()

    st.write("---")
    st.subheader("➕ Fissa un nuovo Allenamento")
    nuova_data = st.date_input("Data", datetime.date.today(), key="new_data_all")
    nuovo_orario = st.selectbox("Orario", orari_allenamento, index=orari_allenamento.index("17:30") if "17:30" in orari_allenamento else 0, key="new_ora_all")
    nuovo_campo = st.selectbox("Campo", OPZIONI_CAMPI_ALLENAMENTO, key="new_campo_all")
    nuova_nota = st.text_input("Note aggiuntive (opzionale)", key="new_nota_all")
    if st.button("Aggiungi Allenamento"):
        nuovo_id = str(int(max([int(e["id"]) for e in st.session_state.db["eventi"]], default=0)) + 1)
        st.session_state.db["eventi"].append({
            "id": nuovo_id, 
            "data": str(nuova_data), 
            "tipo": "Allenamento", 
            "nota": nuova_nota,
            "ora": nuovo_orario,
            "indirizzo": nuovo_campo
        })
        salvare_dati()
        st.rerun()

# ==========================================
# SCHERMATA 2: PARTITE E DISTINTA UFFICIALE
# ==========================================
elif menu == "🟢 Calendario e Convocazioni":
    st.header("🟢 Calendario e Convocazioni")
    
    st.subheader("Le tue Gare:")
    eventi_partita = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] in ["Partita", "Torneo"]]
    opzioni_tipo_partita = ["Campionato", "Amichevole", "Coppa Brescia"]
    
    if not eventi_partita:
        st.info("Nessuna partita in programma.")
    else:
        for ev in eventi_partita:
            if st.session_state.edit_evento == ev["id"]:
                st.write(f"### ✏️ Modifica Partita")
                curr_date = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").date()
                
                col1, col2 = st.columns(2)
                with col1:
                    mod_data = st.date_input("Data", curr_date, key=f"mod_dp_{ev['id']}")
                    mod_avv = st.text_input("Avversario", value=ev.get("avversario", ""), key=f"mod_avv_{ev['id']}")
                    mod_luogo = st.selectbox("Luogo", ["Casa", "Trasferta"], index=0 if ev.get("luogo", "Casa")=="Casa" else 1, key=f"mod_lu_{ev['id']}")
                    if mod_luogo == "Trasferta":
                        mod_indirizzo = st.text_input("Indirizzo del campo", value=ev.get("indirizzo", ""), key=f"mod_ind_{ev['id']}")
                    else:
                        val_ind = ev.get("indirizzo", OPZIONI_CAMPI_CASA[0])
                        idx_ind = OPZIONI_CAMPI_CASA.index(val_ind) if val_ind in OPZIONI_CAMPI_CASA else 0
                        mod_indirizzo = st.selectbox("Indirizzo del campo (Casa)", OPZIONI_CAMPI_CASA, index=idx_ind, key=f"mod_ind_{ev['id']}")
                with col2:
                    # Logica Orario Partita e Convocazione automatica
                    ora_attuale = ev.get("ora_partita", "15:00")
                    idx_ora = orari_partita.index(ora_attuale) if ora_attuale in orari_partita else 12 # Default 15:00
                    mod_orap = st.selectbox("Ora Partita", orari_partita, index=idx_ora, key=f"mod_op_{ev['id']}")
                    
                    h_p, m_p = map(int, mod_orap.split(":"))
                    h_c = h_p - 1
                    mod_orac = f"{h_c:02d}:{m_p:02d}"
                    st.write(f"**Ora Ritrovo (automatica):** {mod_orac}")
                    
                    valore_attuale_nota = ev.get("nota", "Campionato")
                    indice_nota = opzioni_tipo_partita.index(valore_attuale_nota) if valore_attuale_nota in opzioni_tipo_partita else 0
                    mod_nota = st.selectbox("Tipo Partita", opzioni_tipo_partita, index=indice_nota, key=f"mod_np_{ev['id']}")
                    mod_note_agg = st.text_input("Note aggiuntive", value=ev.get("note_aggiuntive", ""), key=f"mod_na_{ev['id']}")
                
                col_s, col_a = st.columns(2)
                with col_s:
                    if st.button("💾 Salva Modifiche", key=f"s_modp_{ev['id']}", type="primary"):
                        ev["data"] = str(mod_data)
                        ev["avversario"] = mod_avv
                        ev["luogo"] = mod_luogo
                        ev["indirizzo"] = mod_indirizzo
                        ev["ora_partita"] = mod_orap
                        ev["ora_convocazione"] = mod_orac
                        ev["nota"] = mod_nota
                        ev["note_aggiuntive"] = mod_note_agg
                        st.session_state.edit_evento = None
                        salvare_dati()
                        st.rerun()
                with col_a:
                    if st.button("❌ Annulla", key=f"a_modp_{ev['id']}"):
                        st.session_state.edit_evento = None
                        st.rerun()
                st.write("---")
            else:
                data_f = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                sq_casa = "USO UNITED" if ev.get("luogo", "Casa") == "Casa" else ev.get("avversario", "Avversario")
                sq_trasf = ev.get("avversario", "Avversario") if ev.get("luogo", "Casa") == "Casa" else "USO UNITED"
                
                with st.expander(f"🟢 {sq_casa}-{sq_trasf} del {data_f}"):
                    col_mod, col_del = st.columns([1, 1])
                    with col_mod:
                        if st.button("✏️ Modifica Gara", key=f"ed_evp_{ev['id']}"):
                            st.session_state.edit_evento = ev["id"]
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Elimina Gara", key=f"del_evp_{ev['id']}"):
                            st.session_state.db["eventi"] = [e for e in st.session_state.db["eventi"] if e["id"] != ev["id"]]
                            if ev["id"] in st.session_state.db["storico_presenze"]: del st.session_state.db["storico_presenze"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_titolari"]: del st.session_state.db["storico_titolari"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_numeri"]: del st.session_state.db["storico_numeri"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_gol"]: del st.session_state.db["storico_gol"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_risultati"]: del st.session_state.db["storico_risultati"][ev["id"]]
                            if ev["id"] in st.session_state.db.get("storico_capitano", {}): del st.session_state.db["storico_capitano"][ev["id"]]
                            if ev["id"] in st.session_state.db.get("storico_vicecapitano", {}): del st.session_state.db["storico_vicecapitano"][ev["id"]]
                            salvare_dati()
                            st.rerun()
                    
                    st.write("---")
                    
                    appello_evento = st.session_state.db["storico_presenze"].get(ev["id"], {})
                    gol_evento = st.session_state.db["storico_gol"].get(ev["id"], {})
                    ris_evento = st.session_state.db["storico_risultati"].get(ev["id"], {})
                    titolari_evento = st.session_state.db["storico_titolari"].get(ev["id"], [])
                    numeri_evento = st.session_state.db["storico_numeri"].get(ev["id"], {})
                    capitano_evento = st.session_state.db.get("storico_capitano", {}).get(ev["id"], "")
                    vice_evento = st.session_state.db.get("storico_vicecapitano", {}).get(ev["id"], "")
                    
                    ind_campo = ev.get("indirizzo", OPZIONI_CAMPI_CASA[0] if ev.get("luogo", "Casa") == "Casa" else "")
                    tipo_partita = ev.get("nota", "Campionato")
                    note_agg = ev.get("note_aggiuntive", "")
                    
                    righe_giocatori = ""
                    convocati_list = []
                    riga_num = 1
                    
                    for ragazzo in ordina_giocatori(st.session_state.db["ragazzi"]):
                        stato = appello_evento.get(ragazzo, "🟢 Convocato")
                        is_convocato = "Convocato" in stato and "Non" not in stato
                        
                        c_mark = "X" if is_convocato else ""
                        nc_mark = "X" if not is_convocato else ""
                        
                        if is_convocato:
                            convocati_list.append(ragazzo)
                            
                        righe_giocatori += f"<tr><td width='10%' style='border: 1px solid black; padding: 5px;'>{riga_num}</td><td width='50%' style='border: 1px solid black; padding: 5px; text-align: left;'>{cognome_nome(ragazzo)}</td><td width='20%' style='border: 1px solid black; padding: 5px; color: green; font-weight: bold;'>{c_mark}</td><td width='20%' style='border: 1px solid black; padding: 5px; color: red; font-weight: bold;'>{nc_mark}</td></tr>"
                        riga_num += 1
                    
                    righe_formazione = ""
                    if titolari_evento:
                        def sorting_key(t):
                            num_str = numeri_evento.get(t, '-')
                            try:
                                n = int(num_str)
                                return n if n > 0 else 999
                            except ValueError:
                                return 999
                        titolari_validi = sorted([t for t in titolari_evento if t in convocati_list], key=sorting_key)
                        for t in titolari_validi:
                            num = numeri_evento.get(t, '-')
                            nome_t, cognome_t = dividi_nome(t)
                            
                            badge = ""
                            if t == capitano_evento: badge = f" <span style='color: {COLORE_BLU}; font-weight: bold;'>(C)</span>"
                            elif t == vice_evento: badge = f" <span style='color: {COLORE_VERDE}; font-weight: bold;'>(VC)</span>"
                            
                            righe_formazione += f"<tr><td width='10%' style='border: 1px solid black; padding: 5px; font-weight: bold;'>{num}</td><td width='45%' style='border: 1px solid black; padding: 5px; text-align: left;'>{cognome_t}</td><td width='45%' style='border: 1px solid black; padding: 5px; text-align: left;'>{nome_t}{badge}</td></tr>"
                    else:
                        righe_formazione = "<tr><td colspan='3' style='border: 1px solid black; padding: 5px; font-style: italic;'>Nessun titolare selezionato</td></tr>"
                    
                    logo_immagine = get_logo_html()
                    
                    html_distinta = f"""<div style='background-color: white; color: black; padding: 10px; font-family: Arial, sans-serif; width: 100%;'>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid {COLORE_BLU};'>
<tr>
<td style='padding: 0; border: none;'>
    <table style='width: 100%; border-collapse: collapse; text-align: center;'>
        <tr>
            <td width='30%' style='border: 1px solid black; vertical-align: middle; padding: 10px;'>{logo_immagine}</td>
            <td width='70%' style='border: 1px solid black; padding: 0;'>
                <table style='width: 100%; border-collapse: collapse; text-align: center;'>
                    <tr><td style='padding: 5px; font-weight: bold; font-size: 16px; background-color: {COLORE_BLU_CHIARO}; border-bottom: 1px solid black;'>CONVOCAZIONI</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid black;'>PARTITA: {sq_casa} - {sq_trasf}</td></tr>
                    <tr><td style='padding: 5px; font-weight: bold; border-bottom: 1px solid black;'>TIPO PARTITA: {tipo_partita}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid black;'>DATA: {data_f}</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid black;'>ORA PARTITA: {ev.get("ora_partita", "___")} - ORA RITROVO: {ev.get("ora_convocazione", "___")}</td></tr>
                    <tr><td style='padding: 5px; font-weight: bold; background-color: {COLORE_BLU_CHIARO};'>LUOGO: {ind_campo}</td></tr>
                </table>
            </td>
        </tr>
    </table>
    <table style='width: 100%; border-collapse: collapse; text-align: center; border-top: none;'>
        <tr style='font-weight: bold; background-color: {COLORE_BLU_CHIARO};'>
            <td width='10%' style='border: 1px solid black; padding: 5px;'>N°</td>
            <td width='50%' style='border: 1px solid black; padding: 5px;'>Cognome e Nome</td>
            <td width='20%' style='border: 1px solid black; padding: 5px;' title='Convocato'>C</td>
            <td width='20%' style='border: 1px solid black; padding: 5px;' title='Non Convocato'>NC</td>
        </tr>
        {righe_giocatori}
    </table>
</td>
</tr>
</table>
</div>"""

                    html_formazione = f"""<div style='background-color: white; color: black; padding: 10px; font-family: Arial, sans-serif; width: 100%;'>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid {COLORE_VERDE};'>
<tr>
<td style='padding: 0; border: none;'>
    <table style='width: 100%; border-collapse: collapse; text-align: center;'>
        <tr>
            <td width='30%' style='border: 1px solid black; vertical-align: middle; padding: 10px;'>{logo_immagine}</td>
            <td width='70%' style='border: 1px solid black; padding: 0;'>
                <table style='width: 100%; border-collapse: collapse; text-align: center;'>
                    <tr><td style='padding: 5px; font-weight: bold; font-size: 16px; background-color: {COLORE_VERDE_CHIARO}; border-bottom: 1px solid black;'>FORMAZIONE UFFICIALE</td></tr>
                    <tr><td style='padding: 5px; border-bottom: 1px solid black;'>PARTITA: {sq_casa} - {sq_trasf}</td></tr>
                    <tr><td style='padding: 5px; font-weight: bold; border-bottom: 1px solid black;'>TIPO PARTITA: {tipo_partita}</td></tr>
                    <tr><td style='padding: 5px;'>DATA: {data_f}</td></tr>
                </table>
            </td>
        </tr>
    </table>
    <table style='width: 100%; border-collapse: collapse; text-align: center; border-top: none;'>
        <tr style='font-weight: bold; background-color: {COLORE_VERDE_CHIARO};'>
            <td width='10%' style='border: 1px solid black; padding: 5px;'>N°</td>
            <td width='45%' style='border: 1px solid black; padding: 5px;'>Cognome</td>
            <td width='45%' style='border: 1px solid black; padding: 5px;'>Nome</td>
        </tr>
        {righe_formazione}
    </table>
</td>
</tr>
</table>
</div>"""
                    
                    whatsapp_text = f"Ciao a tutti,\n\n"
                    whatsapp_text += f"⚽ *CONVOCAZIONI* ⚽\n"
                    whatsapp_text += f"⚽ *{sq_casa}-{sq_trasf}*\n"
                    whatsapp_text += f"🏆 *{tipo_partita}*\n"
                    whatsapp_text += f"📅 *Data:* {data_f}\n"
                    whatsapp_text += f"⏰ *Ora Partita:* {ev.get('ora_partita', '___')}\n"
                    whatsapp_text += f"📍 *Ora Ritrovo:* {ev.get('ora_convocazione', '___')}\n"
                    whatsapp_text += f"🏟️ *Luogo:* {ind_campo}\n"
                    if note_agg and note_agg.strip(): whatsapp_text += f"📝 *Note:* {note_agg.strip()}\n"
                        
                    whatsapp_text += f"\n*CONVOCAZIONI:*\n"
                    whatsapp_text += "```\n"
                    
                    max_len = max([len(cognome_nome(r)) for r in st.session_state.db["ragazzi"]]) if st.session_state.db["ragazzi"] else 12
                    max_len = min(max_len, 15) # limite per evitare a capo su schermi piccoli
                    
                    header_nome = "Giocatore".ljust(max_len)
                    whatsapp_text += f" {header_nome} | C  | NC\n"
                    whatsapp_text += " " + "-" * (max_len + 12) + "\n"
                    
                    if not st.session_state.db["ragazzi"]:
                        whatsapp_text += " (Nessun giocatore in rosa)\n"
                    else:
                        for ragazzo in ordina_giocatori(st.session_state.db["ragazzi"]):
                            stato = appello_evento.get(ragazzo, "🟢 Convocato")
                            is_convocato = "Convocato" in stato and "Non" not in stato
                            c_mark = "✅" if is_convocato else "➖"
                            nc_mark = "✅" if not is_convocato else "➖"
                            
                            nome = cognome_nome(ragazzo)
                            if len(nome) > max_len:
                                nome_pad = nome[:max_len-1] + "."
                            else:
                                nome_pad = nome.ljust(max_len)
                                
                            whatsapp_text += f" {nome_pad} | {c_mark} | {nc_mark}\n"
                    
                    whatsapp_text += "```\n"
                    whatsapp_text += "\nGrazie 💚💙"

                    tab1, tab2, tab_formazione, tab3 = st.tabs(["⚙️ Compila Elenco", "📄 Convocazioni Ufficiali", "⚽ Formazione e Dati Partita", "📱 Messaggio WhatsApp"])
                    
                    with tab1:
                        if not st.session_state.db["ragazzi"]:
                            st.warning("Rosa vuota.")
                        else:
                            st.write("#### 🏃 Seleziona Convocati")
                            resoconto_corrente = {}
                            opzioni = ["🟢 Convocato", "🔴 Non Convocato"]
                            
                            for ragazzo in ordina_giocatori(st.session_state.db["ragazzi"]):
                                col_nome, col_stato = st.columns([1, 2])
                                with col_nome: st.write(f"**{cognome_nome(ragazzo)}**")
                                with col_stato:
                                    stato_precedente = appello_evento.get(ragazzo, opzioni[0])
                                    indice_default = opzioni.index(stato_precedente) if stato_precedente in opzioni else 0
                                    stato = st.radio(f"Stato_{ragazzo}_{ev['id']}", opzioni, index=indice_default, horizontal=True, label_visibility="collapsed", key=f"p_{ragazzo}_{ev['id']}")
                                    resoconto_corrente[ragazzo] = stato
                                    
                            st.write("")
                            if st.button("💾 Salva Convocazioni", key=f"btn_salva_conv_{ev['id']}", type="primary"):
                                st.session_state.db["storico_presenze"][ev["id"]] = resoconto_corrente
                                salvare_dati()
                                st.success("Convocazioni salvate con successo!")
                                st.rerun()

                    with tab_formazione:
                        st.write("#### 🏆 Risultato Gara")
                        col_t1, col_t2, col_t3 = st.columns(3)
                        with col_t1:
                            ris_t1 = st.text_input("1° Tempo (es. 1-0)", value=ris_evento.get("t1", ""), key=f"ris_t1_{ev['id']}")
                        with col_t2:
                            ris_t2 = st.text_input("2° Tempo (es. 2-2)", value=ris_evento.get("t2", ""), key=f"ris_t2_{ev['id']}")
                        with col_t3:
                            ris_t3 = st.text_input("3° Tempo (es. 0-1)", value=ris_evento.get("t3", ""), key=f"ris_t3_{ev['id']}")
                        
                        st.write("---")
                        st.write("#### ⚽ Inserisci Formazione e Prestazioni")
                        
                        if not convocati_list:
                            st.warning("⚠️ Prima devi selezionare i convocati nella scheda 'Compila Elenco'.")
                        else:
                            titolari_salvati = st.session_state.db["storico_titolari"].get(ev["id"], [])
                            numeri_salvati = st.session_state.db["storico_numeri"].get(ev["id"], {})

                            righe_tabella = []
                            for c in convocati_list:
                                nome_str, cogn_str = dividi_nome(c)
                                try:
                                    num_prec = int(numeri_salvati.get(c, 0)) if str(numeri_salvati.get(c, "")).strip() != "" else 0
                                except ValueError:
                                    num_prec = 0
                                try:
                                    gol_prec = int(gol_evento.get(c, 0))
                                except (ValueError, TypeError):
                                    gol_prec = 0

                                righe_tabella.append({
                                    "Giocatore": c,
                                    "N°": num_prec,
                                    "Cognome": cogn_str,
                                    "Nome": nome_str,
                                    "Tit.": c in titolari_salvati,
                                    "Gol": gol_prec,
                                })

                            df_formazione = pd.DataFrame(righe_tabella)
                            df_formazione["sort_num"] = df_formazione["N°"].apply(lambda x: x if x > 0 else 999)
                            df_formazione = df_formazione.sort_values(by=["sort_num", "Cognome", "Nome"]).drop(columns=["sort_num"]).reset_index(drop=True)

                            st.caption("Tocca una cella per modificarla. N° a 0 = numero di maglia non ancora assegnato.")

                            df_edit = st.data_editor(
                                df_formazione,
                                key=f"data_editor_form_{ev['id']}",
                                hide_index=True,
                                use_container_width=True,
                                column_order=["N°", "Cognome", "Nome", "Tit.", "Gol"],
                                column_config={
                                    "N°": st.column_config.NumberColumn("N°", min_value=0, max_value=99, step=1, width="small", format="%d"),
                                    "Cognome": st.column_config.TextColumn("Cognome", disabled=True, width="medium"),
                                    "Nome": st.column_config.TextColumn("Nome", disabled=True, width="medium"),
                                    "Tit.": st.column_config.CheckboxColumn("Tit.", width="small"),
                                    "Gol": st.column_config.NumberColumn("Gol", min_value=0, max_value=99, step=1, width="small", format="%d"),
                                },
                            )

                            df_edit = df_edit.copy()
                            df_edit["Giocatore"] = df_formazione["Giocatore"].values

                            nuovi_titolari = df_edit.loc[df_edit["Tit."] == True, "Giocatore"].tolist()
                            nuovi_numeri = {row["Giocatore"]: str(int(row["N°"])) for _, row in df_edit.iterrows() if int(row["N°"]) > 0}
                            resoconto_gol = {row["Giocatore"]: int(row["Gol"]) for _, row in df_edit.iterrows()}

                            numero_titolari = len(nuovi_titolari)
                            titolari_ok = numero_titolari <= MAX_TITOLARI

                            if numero_titolari > MAX_TITOLARI:
                                st.error(f"⚠️ Hai selezionato **{numero_titolari}** titolari, ma il massimo è **{MAX_TITOLARI}**. Deseleziona almeno {numero_titolari - MAX_TITOLARI} giocatore/i in tabella prima di salvare.")
                            elif numero_titolari == MAX_TITOLARI:
                                st.success(f"✅ Titolari selezionati: {numero_titolari}/{MAX_TITOLARI} — formazione completa.")
                            else:
                                st.info(f"ℹ️ Titolari selezionati: {numero_titolari}/{MAX_TITOLARI}")

                            st.write("---")
                            st.write("#### © Assegna Fasce")
                            opzioni_fasce = ["Nessuno"] + convocati_list
                            idx_cap = opzioni_fasce.index(capitano_evento) if capitano_evento in opzioni_fasce else 0
                            idx_vice = opzioni_fasce.index(vice_evento) if vice_evento in opzioni_fasce else 0
                            
                            col_cap, col_vice = st.columns(2)
                            with col_cap:
                                input_capitano = st.selectbox("Capitano (C)", opzioni_fasce, index=idx_cap, key=f"cap_{ev['id']}", format_func=lambda x: cognome_nome(x) if x != "Nessuno" else x)
                            with col_vice:
                                input_vice = st.selectbox("Vice-Capitano (VC)", opzioni_fasce, index=idx_vice, key=f"vice_{ev['id']}", format_func=lambda x: cognome_nome(x) if x != "Nessuno" else x)
                            
                            st.write("")
                            if st.button("💾 Salva Formazione e Dati", key=f"btn_salva_form_{ev['id']}", type="primary"):
                                if not titolari_ok:
                                    st.error(f"❌ Impossibile salvare: hai {numero_titolari} titolari selezionati, il massimo consentito è {MAX_TITOLARI}. Correggi la tabella e riprova.")
                                else:
                                    st.session_state.db["storico_titolari"][ev["id"]] = nuovi_titolari
                                    st.session_state.db["storico_numeri"][ev["id"]] = nuovi_numeri
                                    st.session_state.db["storico_risultati"][ev["id"]] = {"t1": ris_t1, "t2": ris_t2, "t3": ris_t3}
                                    st.session_state.db["storico_gol"][ev["id"]] = resoconto_gol
                                    st.session_state.db.setdefault("storico_capitano", {})[ev["id"]] = input_capitano if input_capitano != "Nessuno" else ""
                                    st.session_state.db.setdefault("storico_vicecapitano", {})[ev["id"]] = input_vice if input_vice != "Nessuno" else ""
                                    salvare_dati()
                                    st.success("Formazione e Dati salvati con successo!")
                                    st.rerun()

                            st.write("---")
                            st.markdown(html_formazione, unsafe_allow_html=True)
                            st.write("")
                            st.download_button(
                                label="⬇️ Scarica Modulo Formazione (.html)",
                                data=html_formazione,
                                file_name=f"Formazione_{sq_casa}_{sq_trasf}.html",
                                mime="text/html",
                                key=f"dl_html_form_{ev['id']}"
                            )

                    with tab2:
                        st.markdown(html_distinta, unsafe_allow_html=True)
                        st.write("")
                        logo_immagine_pdf = get_logo_html(per_pdf=True)
                        html_distinta_pdf = html_distinta.replace(logo_immagine, logo_immagine_pdf)
                        pdf_convocazioni = genera_pdf(html_distinta_pdf)
                        if pdf_convocazioni:
                            st.download_button(
                                label="⬇️ Scarica Convocazioni (PDF)",
                                data=pdf_convocazioni,
                                file_name=f"Convocazioni_{sq_casa}_{sq_trasf}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_conv_{ev['id']}"
                            )
                        else:
                            st.warning("⚠️ Non sono riuscito a generare il PDF. Assicurati che xhtml2pdf sia installato.")
                            st.download_button(
                                label="⬇️ Scarica Convocazioni (.html)",
                                data=html_distinta,
                                file_name=f"Convocazioni_{sq_casa}_{sq_trasf}.html",
                                mime="text/html",
                                key=f"dl_html_conv_fallback_{ev['id']}"
                            )

                    with tab3:
                        st.code(whatsapp_text, language="markdown")
                        st.write("---")
                        wa_url = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(whatsapp_text)
                        if hasattr(st, "link_button"):
                            st.link_button("📲 Apri WhatsApp con questo messaggio", wa_url)
                        else:
                            st.markdown(f"[📲 Apri WhatsApp con questo messaggio]({wa_url})")

    st.write("---")
    st.subheader("➕ Inserisci una Nuova Partita")
    col1, col2 = st.columns(2)
    with col1:
        nuova_data = st.date_input("Data", datetime.date.today(), key="new_data_p")
        nuovo_avversario = st.text_input("Avversario (es. Real City)", key="new_avv")
        nuovo_luogo = st.selectbox("Dove si gioca?", ["Casa", "Trasferta"], key="new_luogo")
        
        if nuovo_luogo == "Trasferta":
            nuovo_indirizzo = st.text_input("Indirizzo del campo (es. Via Roma 10)", key="new_indirizzo")
        else:
            nuovo_indirizzo = st.selectbox("Indirizzo del campo (Casa)", OPZIONI_CAMPI_CASA, key="new_indirizzo_casa")
    with col2:
        nuova_orap = st.selectbox("Ora Partita", orari_partita, index=12, key="new_orap")
        h_p, m_p = map(int, nuova_orap.split(":"))
        h_c = h_p - 1
        nuova_orac = f"{h_c:02d}:{m_p:02d}"
        st.write(f"**Ora Ritrovo (automatica):** {nuova_orac}")
        
        nuova_nota = st.selectbox("Tipo Partita", ["Campionato", "Amichevole", "Coppa Brescia"], key="new_notap")
        nuova_nota_agg = st.text_input("Note aggiuntive", key="new_nota_agg")
        
    if st.button("Aggiungi Partita a Calendario"):
        if nuovo_avversario.strip() == "":
            st.error("Inserisci il nome dell'avversario!")
        else:
            nuovo_id = str(int(max([int(e["id"]) for e in st.session_state.db["eventi"]], default=0)) + 1)
            st.session_state.db["eventi"].append({
                "id": nuovo_id, "data": str(nuova_data), "tipo": "Partita", 
                "avversario": nuovo_avversario, "luogo": nuovo_luogo, 
                "ora_partita": nuova_orap, "ora_convocazione": nuova_orac, 
                "indirizzo": nuovo_indirizzo if nuovo_luogo == "Trasferta" else st.session_state.new_indirizzo_casa, 
                "nota": nuova_nota, "note_aggiuntive": nuova_nota_agg
            })
            salvare_dati()
            st.rerun()

# ==========================================
# SCHERMATA 3: STATISTICHE ALLENAMENTI
# ==========================================
elif menu == "📊 Statistiche Allenamenti":
    st.header("📊 Statistiche Allenamenti")
    
    storico = st.session_state.db["storico_presenze"]
    id_allenamenti = [ev["id"] for ev in st.session_state.db["eventi"] if ev["tipo"] == "Allenamento"]
    totale_allenamenti = sum(1 for ev_id in storico if ev_id in id_allenamenti)
    
    st.metric(label="Totale Allenamenti Svolti", value=totale_allenamenti)
    st.write("---")
    
    if totale_allenamenti == 0:
        st.info("📊 Nessun dato di allenamento registrato.")
    else:
        tabella_all = []
        for ragazzo in ordina_giocatori(st.session_state.db["ragazzi"]):
            presenti, assenti, infortunati = 0, 0, 0
            for ev_id, appello in storico.items():
                if ev_id in id_allenamenti:
                    stato = appello.get(ragazzo, "")
                    if "Presente" in stato: presenti += 1
                    elif "Assente" in stato: assenti += 1
                    elif "Infortunato" in stato: infortunati += 1
            
            pct = (presenti / totale_allenamenti) * 100 if totale_allenamenti > 0 else 0.00
            tabella_all.append({
                "Giocatore": cognome_nome(ragazzo),
                "🟢 Presenze": presenti,
                "🔴 Assenze": assenti,
                "🟡 Infortuni": infortunati,
                "📈 % Presenza": f"{pct:.2f}%"
            })
        st.table(tabella_all)
        
        if tabella_all:
            html_all = f"<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Allenamenti</h2><table border='1' style='border-collapse: collapse; text-align: center; width:100%;'><tr><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>Giocatore</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🟢 Presenze</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🔴 Assenze</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🟡 Infortuni</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>📈 % Presenza</th></tr>"
            for row in tabella_all:
                html_all += f"<tr><td style='padding:8px;'>{row['Giocatore']}</td><td style='padding:8px;'>{row['🟢 Presenze']}</td><td style='padding:8px;'>{row['🔴 Assenze']}</td><td style='padding:8px;'>{row['🟡 Infortuni']}</td><td style='padding:8px;'>{row['📈 % Presenza']}</td></tr>"
            html_all += "</table></body></html>"
            
            st.download_button(
                label="⬇️ Scarica Statistiche Allenamenti (.html)",
                data=html_all,
                file_name="Statistiche_Allenamenti.html",
                mime="text/html"
            )

# ==========================================
# SCHERMATA 4: STATISTICHE GIOCATORI
# ==========================================
elif menu == "🏆 Statistiche Giocatori":
    st.header("🏆 Statistiche Giocatori (Partite)")
    
    storico = st.session_state.db["storico_presenze"]
    id_gare = [ev["id"] for ev in st.session_state.db["eventi"] if ev["tipo"] in ["Partita", "Torneo"]]
    totale_gare = sum(1 for ev_id in storico if ev_id in id_gare)
    
    st.metric(label="Totale Gare Archiviate", value=totale_gare)
    st.write("---")
    
    if totale_gare == 0:
        st.info("📊 Nessun dato sulle partite presente in archivio.")
    else:
        tabella_gare = []
        for ragazzo in ordina_giocatori(st.session_state.db["ragazzi"]):
            convocati, non_convocati, presenze_titolare = 0, 0, 0
            for ev_id, appello in storico.items():
                if ev_id in id_gare:
                    stato = appello.get(ragazzo, "")
                    if "Convocato" in stato and "Non" not in stato: 
                        convocati += 1
                        if ragazzo in st.session_state.db["storico_titolari"].get(ev_id, []):
                            presenze_titolare += 1
                    elif "Non Convocato" in stato: 
                        non_convocati += 1
            
            pct_conv = (convocati / totale_gare) * 100 if totale_gare > 0 else 0.00
            pct_tit = (presenze_titolare / convocati) * 100 if convocati > 0 else 0.00
            gol_tot = 0
            for ev_id in id_gare:
                gol_tot += st.session_state.db["storico_gol"].get(str(ev_id), {}).get(ragazzo, 0)

            tabella_gare.append({
                "Giocatore": cognome_nome(ragazzo),
                "🟢 Convocato": convocati,
                "🔴 Non Conv.": non_convocati,
                "👕 Titolare": presenze_titolare,
                "📈 % Conv.": f"{pct_conv:.2f}%",
                "🏅 % Titolare": f"{pct_tit:.2f}%",
                "⚽ Gol Fatti": gol_tot
            })
        st.table(tabella_gare)
        
        if tabella_gare:
            html_giocatori = f"<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Giocatori</h2><table border='1' style='border-collapse: collapse; text-align: center; width:100%;'><tr><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>Giocatore</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🟢 Convocato</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🔴 Non Conv.</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>👕 Titolare</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>📈 % Conv.</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🏅 % Titolare</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>⚽ Gol Fatti</th></tr>"
            for row in tabella_gare:
                html_giocatori += f"<tr><td style='padding:8px;'>{row['Giocatore']}</td><td style='padding:8px;'>{row['🟢 Convocato']}</td><td style='padding:8px;'>{row['🔴 Non Conv.']}</td><td style='padding:8px;'>{row['👕 Titolare']}</td><td style='padding:8px;'>{row['📈 % Conv.']}</td><td style='padding:8px;'>{row['🏅 % Titolare']}</td><td style='padding:8px;'>{row['⚽ Gol Fatti']}</td></tr>"
            html_giocatori += "</table></body></html>"
            
            st.download_button(
                label="⬇️ Scarica Statistiche Giocatori (.html)",
                data=html_giocatori,
                file_name="Statistiche_Giocatori.html",
                mime="text/html"
            )

# ==========================================
# SCHERMATA 5: STATISTICHE SQUADRA
# ==========================================
elif menu == "📈 Statistiche Squadra":
    st.header("📈 Statistiche di Squadra")
    
    def parse_tempo(ris_str, luogo="Casa"):
        if not ris_str: return 0, 0, 0, 0
        s = str(ris_str).replace(":", "-").replace(" ", "").replace("/", "-")
        try:
            if "-" in s:
                g_casa, g_trasf = map(int, s.split("-")[:2])
                if luogo == "Casa":
                    gf = g_casa   
                    gs = g_trasf  
                else:
                    gf = g_trasf  
                    gs = g_casa   
                
                if gf > gs: return 1, 0, gf, gs    
                elif gf == gs: return 1, 1, gf, gs 
                else: return 0, 1, gf, gs          
        except:
            pass
        return 0, 0, 0, 0
        
    eventi_partita = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] in ["Partita", "Torneo"]]
    
    tot_partite = 0
    tot_gf = 0
    tot_gs = 0
    vittorie = 0
    pareggi = 0
    sconfitte = 0
    
    partite_t1 = 0; v_t1 = 0; p_t1 = 0; s_t1 = 0; gf_t1 = 0; gs_t1 = 0
    partite_t2 = 0; v_t2 = 0; p_t2 = 0; s_t2 = 0; gf_t2 = 0; gs_t2 = 0
    partite_t3 = 0; v_t3 = 0; p_t3 = 0; s_t3 = 0; gf_t3 = 0; gs_t3 = 0
    
    righe_partite = ""
    
    for ev in eventi_partita:
        ris_evento = st.session_state.db["storico_risultati"].get(ev["id"], {})
        t1 = ris_evento.get("t1", "")
        t2 = ris_evento.get("t2", "")
        t3 = ris_evento.get("t3", "")
        
        if t1 or t2 or t3:
            tot_partite += 1
            luogo_gara = ev.get("luogo", "Casa")
            pu1, pa1, gf1, gs1 = parse_tempo(t1, luogo_gara)
            pu2, pa2, gf2, gs2 = parse_tempo(t2, luogo_gara)
            pu3, pa3, gf3, gs3 = parse_tempo(t3, luogo_gara)
            
            p_uso_tot = pu1 + pu2 + pu3
            p_avv_tot = pa1 + pa2 + pa3
            
            gf_partita = gf1 + gf2 + gf3
            gs_partita = gs1 + gs2 + gs3
            
            tot_gf += gf_partita
            tot_gs += gs_partita
            
            esito_tabella = f"{p_uso_tot} - {p_avv_tot}"
            
            if p_uso_tot > p_avv_tot:
                vittorie += 1
            elif p_uso_tot < p_avv_tot:
                sconfitte += 1
            else:
                if gf_partita > gs_partita:
                    vittorie += 1
                    esito_tabella += " <br><span style='font-size:12px; color: #4CAF50;'>(V per Diff. Reti)</span>"
                elif gf_partita < gs_partita:
                    sconfitte += 1
                    esito_tabella += " <br><span style='font-size:12px; color: #F44336;'>(S per Diff. Reti)</span>"
                else:
                    pareggi += 1
                    
            if t1:
                partite_t1 += 1
                gf_t1 += gf1; gs_t1 += gs1
                if gf1 > gs1: v_t1 += 1
                elif gf1 < gs1: s_t1 += 1
                else: p_t1 += 1
            if t2:
                partite_t2 += 1
                gf_t2 += gf2; gs_t2 += gs2
                if gf2 > gs2: v_t2 += 1
                elif gf2 < gs2: s_t2 += 1
                else: p_t2 += 1
            if t3:
                partite_t3 += 1
                gf_t3 += gf3; gs_t3 += gs3
                if gf3 > gs3: v_t3 += 1
                elif gf3 < gs3: s_t3 += 1
                else: p_t3 += 1
                
            data_f = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
            sq_casa = "USO UNITED" if luogo_gara == "Casa" else ev.get("avversario", "Avversario")
            sq_trasf = ev.get("avversario", "Avversario") if luogo_gara == "Casa" else "USO UNITED"
            stringa_partita = f"{sq_casa}-{sq_trasf}"
            
            righe_partite += f"<tr><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{data_f}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{stringa_partita}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t1 if t1 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t2 if t2 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t3 if t3 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px; font-weight: bold;'>{esito_tabella}</td></tr>"

    def genera_riepilogo_html(titolo, giocate, v, p, s, gf, gs):
        return f"""<h4 style="color: var(--text-color); margin-top: 20px;">{titolo}</h4>
<table style="width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; color: var(--text-color);">
<tr style="background-color: rgba(128,128,128,0.2); font-weight: bold;">
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Gare</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Vittorie</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Pareggi</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Sconfitte</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Gol Fatti</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Gol Subiti</td>
</tr>
<tr>
<td style="padding: 15px; font-size: 24px; font-weight: bold; border: 1px solid rgba(128,128,128,0.3);">{giocate}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #4CAF50; border: 1px solid rgba(128,128,128,0.3);">{v}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #FF9800; border: 1px solid rgba(128,128,128,0.3);">{p}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #F44336; border: 1px solid rgba(128,128,128,0.3);">{s}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #4CAF50; border: 1px solid rgba(128,128,128,0.3);">{gf}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #F44336; border: 1px solid rgba(128,128,128,0.3);">{gs}</td>
</tr>
</table>"""

    riepilogo_html = genera_riepilogo_html("⚽ Statistiche Generali (Intera Partita)", tot_partite, vittorie, pareggi, sconfitte, tot_gf, tot_gs)
    riepilogo_t1_html = genera_riepilogo_html("⏱️ Statistiche 1° Tempo", partite_t1, v_t1, p_t1, s_t1, gf_t1, gs_t1)
    riepilogo_t2_html = genera_riepilogo_html("⏱️ Statistiche 2° Tempo", partite_t2, v_t2, p_t2, s_t2, gf_t2, gs_t2)
    riepilogo_t3_html = genera_riepilogo_html("⏱️ Statistiche 3° Tempo", partite_t3, v_t3, p_t3, s_t3, gf_t3, gs_t3)

    st.markdown(riepilogo_html, unsafe_allow_html=True)
    
    with st.expander("📊 Vedi Statistiche per Singolo Tempo", expanded=True):
        st.markdown(riepilogo_t1_html, unsafe_allow_html=True)
        st.markdown(riepilogo_t2_html, unsafe_allow_html=True)
        st.markdown(riepilogo_t3_html, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📝 Dettaglio Risultati Partite")
    if not righe_partite:
        st.info("Nessun risultato inserito nelle partite in calendario.")
    else:
        tabella_html = f"""<table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; color: var(--text-color);">
<tr style="background-color: rgba(128,128,128,0.2); font-weight: bold;">
<td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">Data</td>
<td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">Partita</td>
<td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">1° T</td>
<td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">2° T</td>
<td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">3° T</td>
<td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3); color: #4CAF50;">Punti Tempi</td>
</tr>
{righe_partite}
</table>"""
        st.markdown(tabella_html, unsafe_allow_html=True)
        
        if tot_partite > 0:
            html_squadra = f"<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Squadra</h2>{riepilogo_html}{riepilogo_t1_html}{riepilogo_t2_html}{riepilogo_t3_html}<h2>Dettaglio Partite</h2>{tabella_html}</body></html>"
            html_squadra = html_squadra.replace('var(--text-color)', 'black').replace('rgba(128,128,128,0.2)', '#f0f0f0').replace('rgba(128,128,128,0.3)', 'black')
            
            st.download_button(
                label="⬇️ Scarica Statistiche Squadra (.html)",
                data=html_squadra,
                file_name="Statistiche_Squadra.html",
                mime="text/html"
            )

# ==========================================
# SCHERMATA 6: GESTIONE ROSA
# ==========================================
elif menu == "🏃 Gestione Rosa":
    st.header("🏃 Anagrafica e Gestione Rosa")
    
    st.subheader("I tuoi giocatori attuali:")
    if not st.session_state.db["ragazzi"]: 
        st.warning("La Rosa è vuota!")
    else:
        st.markdown("### 📋 Elenco Giocatori")
        st.caption("Ordine alfabetico per Cognome. Tocca una cella per modificarla, spunta '🗑️ Elimina' sulle righe da rimuovere, poi premi 'Salva Modifiche Rosa'.")

        ruoli_disp = ["Portiere", "Difensore", "Centrocampista", "Attaccante", "Non definito"]
        nomi_originali = ordina_giocatori(st.session_state.db["ragazzi"])

        righe_rosa = []
        for ragazzo in nomi_originali:
            nome_r, cognome_r = dividi_nome(ragazzo)

            nascita_prec = st.session_state.db.get("anagrafica_nascita", {}).get(ragazzo, "")
            if nascita_prec:
                try:
                    d_obj = datetime.datetime.strptime(nascita_prec, "%Y-%m-%d").date()
                except ValueError:
                    d_obj = datetime.date(2014, 1, 1)
            else:
                d_obj = datetime.date(2014, 1, 1)

            ruolo_prec = st.session_state.db.get("anagrafica_ruolo", {}).get(ragazzo, "Non definito")
            if ruolo_prec not in ruoli_disp:
                ruolo_prec = "Non definito"

            righe_rosa.append({
                "Cognome": cognome_r,
                "Nome": nome_r,
                "Data di Nascita": d_obj,
                "Ruolo": ruolo_prec,
                "🗑️ Elimina": False,
            })

        df_rosa = pd.DataFrame(righe_rosa)

        df_rosa_edit = st.data_editor(
            df_rosa,
            key=f"data_editor_rosa_{st.session_state.rosa_editor_version}",
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            column_order=["Cognome", "Nome", "Data di Nascita", "Ruolo", "🗑️ Elimina"],
            column_config={
                "Cognome": st.column_config.TextColumn("Cognome", width="medium"),
                "Nome": st.column_config.TextColumn("Nome", width="medium"),
                "Data di Nascita": st.column_config.DateColumn("Data di Nascita", format="DD/MM/YYYY", width="small"),
                "Ruolo": st.column_config.SelectboxColumn("Ruolo", options=ruoli_disp, width="medium"),
                "🗑️ Elimina": st.column_config.CheckboxColumn("🗑️ Elimina", width="small"),
            },
        )

        if st.button("💾 Salva Modifiche Rosa", key="btn_salva_rosa", type="primary"):
            nomi_superstiti = []
            errori = []
            for idx, row in df_rosa_edit.iterrows():
                if bool(row["🗑️ Elimina"]):
                    continue
                nome_pulito = str(row["Nome"]).strip()
                cognome_pulito = str(row["Cognome"]).strip()
                if nome_pulito == "":
                    errori.append(f"Riga {idx + 1}: il campo 'Nome' non può essere vuoto.")
                    continue
                nomi_superstiti.append(f"{nome_pulito} {cognome_pulito}".strip())

            duplicati = {n for n in nomi_superstiti if nomi_superstiti.count(n) > 1}
            if duplicati:
                errori.append(f"Giocatori duplicati non ammessi: {', '.join(sorted(cognome_nome(d) for d in duplicati))}.")

            if errori:
                for e in errori:
                    st.error(f"❌ {e}")
            else:
                nuova_lista_ragazzi = []
                for idx, row in df_rosa_edit.iterrows():
                    nome_originale = nomi_originali[idx]

                    if bool(row["🗑️ Elimina"]):
                        if nome_originale in st.session_state.db.get("anagrafica_ruolo", {}):
                            del st.session_state.db["anagrafica_ruolo"][nome_originale]
                        if nome_originale in st.session_state.db.get("anagrafica_nascita", {}):
                            del st.session_state.db["anagrafica_nascita"][nome_originale]
                        continue

                    nome_pulito = str(row["Nome"]).strip()
                    cognome_pulito = str(row["Cognome"]).strip()
                    nome_nuovo = f"{nome_pulito} {cognome_pulito}".strip()
                    nascita_nuova = row["Data di Nascita"]
                    ruolo_nuovo = row["Ruolo"]

                    if nome_nuovo != nome_originale:
                        for _, appello in st.session_state.db["storico_presenze"].items():
                            if nome_originale in appello:
                                appello[nome_nuovo] = appello.pop(nome_originale)
                        for _, titolari_list in st.session_state.db["storico_titolari"].items():
                            if nome_originale in titolari_list:
                                titolari_list.remove(nome_originale)
                                titolari_list.append(nome_nuovo)
                        for _, numeri_dict in st.session_state.db["storico_numeri"].items():
                            if numeri_dict and nome_originale in numeri_dict:
                                numeri_dict[nome_nuovo] = numeri_dict.pop(nome_originale)
                        for _, gol_dict in st.session_state.db["storico_gol"].items():
                            if gol_dict and nome_originale in gol_dict:
                                gol_dict[nome_nuovo] = gol_dict.pop(nome_originale)
                        for campo_fascia in ("storico_capitano", "storico_vicecapitano"):
                            for ev_id_f, nome_assegnato in st.session_state.db.get(campo_fascia, {}).items():
                                if nome_assegnato == nome_originale:
                                    st.session_state.db[campo_fascia][ev_id_f] = nome_nuovo
                        if nome_originale in st.session_state.db.get("anagrafica_ruolo", {}):
                            st.session_state.db["anagrafica_ruolo"].pop(nome_originale)
                        if nome_originale in st.session_state.db.get("anagrafica_nascita", {}):
                            st.session_state.db["anagrafica_nascita"].pop(nome_originale)

                    st.session_state.db.setdefault("anagrafica_ruolo", {})[nome_nuovo] = ruolo_nuovo
                    nascita_str = nascita_nuova.strftime("%Y-%m-%d") if hasattr(nascita_nuova, "strftime") else str(nascita_nuova)
                    st.session_state.db.setdefault("anagrafica_nascita", {})[nome_nuovo] = nascita_str
                    nuova_lista_ragazzi.append(nome_nuovo)

                st.session_state.db["ragazzi"] = ordina_giocatori(nuova_lista_ragazzi)
                st.session_state.rosa_editor_version += 1
                salvare_dati()
                st.success("✅ Rosa aggiornata con successo!")
                st.rerun()

    st.subheader("➕ Aggiungi un nuovo giocatore")
    with st.container():
        col_c, col_n, col_d, col_r = st.columns([2, 2, 1.5, 1.5])
        with col_c: nuovo_cognome_ins = st.text_input("Cognome:", key="nuovo_ins_cognome")
        with col_n: nuovo_nome_ins = st.text_input("Nome:", key="nuovo_ins_nome")
        with col_d: nuova_nascita_ins = st.date_input("Data di Nascita", datetime.date(2014, 1, 1))
        with col_r: nuovo_ruolo_ins = st.selectbox("Ruolo", ["Portiere", "Difensore", "Centrocampista", "Attaccante", "Non definito"])
        
        if st.button("Inserisci in Squadra", type="primary"):
            nome_completo_ins = f"{nuovo_nome_ins.strip()} {nuovo_cognome_ins.strip()}".strip()
            if nuovo_nome_ins.strip() == "":
                st.error("Il campo 'Nome' non può essere vuoto.")
            elif nome_completo_ins in st.session_state.db["ragazzi"]:
                st.error(f"'{cognome_nome(nome_completo_ins)}' è già presente in rosa.")
            else:
                st.session_state.db["ragazzi"].append(nome_completo_ins)
                st.session_state.db.setdefault("anagrafica_ruolo", {})[nome_completo_ins] = nuovo_ruolo_ins
                st.session_state.db.setdefault("anagrafica_nascita", {})[nome_completo_ins] = str(nuova_nascita_ins)
                salvare_dati()
                st.success(f"⚽ {cognome_nome(nome_completo_ins)} aggiunto alla rosa!")
                st.rerun()
