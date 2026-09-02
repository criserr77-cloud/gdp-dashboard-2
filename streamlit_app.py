import streamlit as st
import pandas as pd
import datetime
import json
import os
import re
import base64
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import firebase_admin
from firebase_admin import credentials, firestore

# --- CONFIGURAZIONE GOOGLE SHEETS ---
ID_FOGLIO_GOOGLE = "1PCmJ9tgv-ohAIuc3CmwP4BOZLg68qSLmkLYwSQ7pSsc" 

# --- CONFIGURAZIONE FIREBASE (backup, oltre a Google Sheets) ---
FIREBASE_ATTIVO = False  # In pausa: rimetti a True quando vuoi riattivare il backup su Firebase
FIREBASE_COLLECTION = "misterapp"
FIREBASE_DOCUMENTO = "db_squadra"

def connetti_firebase():
    """Inizializza (una sola volta per sessione del server) l'app Firebase Admin e restituisce il client Firestore.
    Usa un account di servizio (bypassa le regole di sicurezza, niente scadenza a 30gg come la modalità test).
    Non intercetta gli errori qui: li lascia gestire a chi chiama (salvare_dati/caricare_dati),
    così l'errore arriva davvero visibile invece di sparire in un avviso lampo prima del rerun."""
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets["firebase_service_account"]))
        firebase_admin.initialize_app(cred)
    return firestore.client()

# --- CONFIGURAZIONE REGOLAMENTO ---
MAX_TITOLARI = 9  # Numero massimo di titolari selezionabili per partita (es. 9 per il calcio a 9)

# --- CONFIGURAZIONE COLORI (tema Blu/Verde) ---
# Cambia solo questi valori per modificare la palette in tutta l'app e nei documenti scaricabili.
COLORE_BLU = "#002255"          # Blu navy esatto dello stemma (campionato dall'immagine) — colore principale
COLORE_BLU_CHIARO = "#E7ECF5"   # Blu chiaro (sfondo intestazioni documento Convocazioni)
COLORE_BLU_ACCENTO = "#1E4D8C"  # Blu royal più chiaro, accento secondario (Formazione, sfumature pulsanti)
COLORE_BLU_ACCENTO_CHIARO = "#DCE6F5" # Blu accento chiaro (sfondo intestazioni documento Formazione)

# --- CONFIGURAZIONE CAMPI DI CASA ---
# Aggiungi/modifica qui se cambiano i campi disponibili per le partite in casa.
CAMPI_CASA = [
    "Campo Santa Giulia - Via del Brolo 7, Villaggio Prealpino",
    "Campo Comunale - Parco Urbano, Bovezzo",
]

# --- CONFIGURAZIONE CAMPI ALLENAMENTO ---
CAMPI_ALLENAMENTO = [
    "Campo Comunale Bovezzo",
    "Campo Prealpino",
    "Campo S.Andrea",
    "Ritiro Bagolino",
]

def connetti_foglio():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_FOGLIO_GOOGLE).sheet1
        st.session_state.pop("ultimo_errore_sheets", None)
        return sheet
    except Exception as e:
        st.session_state["ultimo_errore_sheets"] = str(e)
        return None

CHIAVI_DATI_DEFAULT = ["storico_presenze", "storico_minutaggio", "storico_titolari", "storico_moduli",
                       "storico_numeri", "storico_gol", "storico_risultati", "anagrafica_ruolo",
                       "anagrafica_nascita", "storico_capitano", "storico_vicecapitano"]

def caricare_dati():
    # 1) Fonte principale: Google Sheets (storicamente affidabile)
    sheet = connetti_foglio()
    if sheet:
        try:
            contenuto = sheet.acell('A1').value
            if contenuto:
                dati = json.loads(contenuto)
                for k in CHIAVI_DATI_DEFAULT:
                    if k not in dati: dati[k] = {}
                return dati
        except Exception:
            pass

    # 2) Backup: se Google Sheets non ha dati validi, prova Firebase (se attivo)
    if FIREBASE_ATTIVO:
        try:
            db_firebase = connetti_firebase()
            if db_firebase:
                doc = db_firebase.collection(FIREBASE_COLLECTION).document(FIREBASE_DOCUMENTO).get()
                if doc.exists:
                    dati = doc.to_dict()
                    if dati:
                        for k in CHIAVI_DATI_DEFAULT:
                            if k not in dati: dati[k] = {}
                        st.info("ℹ️ Dati recuperati da Firebase (Google Sheets non era disponibile).")
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

MAX_BACKUP_STORICO = 10  # Quante versioni precedenti tenere nella scheda "Backup"

def backup_su_foglio(sheet, contenuto_precedente):
    """Salva 'contenuto_precedente' (il contenuto di A1 PRIMA di sovrascriverlo) come nuova riga
    nella scheda 'Backup' dello stesso foglio Google, con data e ora. Tiene solo le ultime
    MAX_BACKUP_STORICO versioni. Se qualcosa va storto qui, non deve mai bloccare il salvataggio
    principale: eventuali errori vengono ignorati silenziosamente."""
    try:
        spreadsheet = sheet.spreadsheet
        try:
            foglio_backup = spreadsheet.worksheet("Backup")
        except gspread.exceptions.WorksheetNotFound:
            foglio_backup = spreadsheet.add_worksheet(title="Backup", rows=MAX_BACKUP_STORICO + 5, cols=2)
            foglio_backup.append_row(["Data e Ora", "Contenuto JSON precedente"])

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        foglio_backup.append_row([timestamp, contenuto_precedente])

        righe_totali = len(foglio_backup.get_all_values())
        if righe_totali > MAX_BACKUP_STORICO + 1:  # +1 per la riga di intestazione
            righe_in_eccesso = righe_totali - (MAX_BACKUP_STORICO + 1)
            foglio_backup.delete_rows(2, 1 + righe_in_eccesso)
    except Exception:
        pass

def salvare_dati():
    salvato_sheets = False
    salvato_firebase = False
    errori = []

    try:
        sheet = connetti_foglio()
        if sheet:
            contenuto_precedente = sheet.acell('A1').value
            if contenuto_precedente:
                backup_su_foglio(sheet, contenuto_precedente)

            stringa_json = json.dumps(st.session_state.db, ensure_ascii=False, indent=4)
            sheet.update_acell('A1', stringa_json)
            salvato_sheets = True
    except Exception as e:
        errori.append(f"Google Sheets: {e}")

    if FIREBASE_ATTIVO:
        try:
            db_firebase = connetti_firebase()
            if db_firebase:
                db_firebase.collection(FIREBASE_COLLECTION).document(FIREBASE_DOCUMENTO).set(st.session_state.db)
                salvato_firebase = True
                print(f"[FIREBASE] Salvataggio riuscito su collezione '{FIREBASE_COLLECTION}', documento '{FIREBASE_DOCUMENTO}'.")
            else:
                print("[FIREBASE] connetti_firebase() ha restituito None: controlla i Secrets 'firebase_service_account'.")
        except Exception as e:
            errori.append(f"Firebase: {e}")
            print(f"[FIREBASE] ERRORE durante il salvataggio: {repr(e)}")

    if errori:
        st.session_state["ultimo_errore_salvataggio"] = " | ".join(errori)
    else:
        st.session_state.pop("ultimo_errore_salvataggio", None)

    if not salvato_sheets and not salvato_firebase:
        st.error("❌ ERRORE DI SALVATAGGIO (né Google Sheets né Firebase hanno funzionato): " + " | ".join(errori))
        st.stop()
    elif errori:
        st.warning("⚠️ Salvato solo parzialmente, controlla: " + " | ".join(errori))


st.set_page_config(page_title="MisterApp", layout="centered")

# --- CSS DEFINITIVO E BLOCCATO PER VISUALIZZAZIONE ORIZZONTALE SU MOBILE ---
st.markdown(f"""
    <style>
    .card {{ 
        background-color: var(--secondary-background-color); 
        border-radius: 15px; padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        margin-bottom: 20px; 
        border: 1px solid {COLORE_BLU_ACCENTO};
    }}
    
    /* MENU LATERALE RESPONSIVE ED INGRANDITO - tema Blu/Verde */
    [data-testid="stSidebar"] {{
        border-right: 2px solid {COLORE_BLU_ACCENTO};
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
        border-color: {COLORE_BLU_ACCENTO};
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label p {{
        font-size: 22px !important;
        font-weight: bold !important;
        color: var(--text-color) !important;
    }}

    /* Pulsanti primari (Salva, Aggiungi, ecc.) con sfumatura Blu -> Verde */
    button[kind="primary"], .stButton button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORE_BLU} 0%, {COLORE_BLU_ACCENTO} 100%) !important;
        border: none !important;
        color: white !important;
    }}

    /* Intestazioni di pagina con accento verde */
    h1, h2 {{
        border-left: 5px solid {COLORE_BLU_ACCENTO};
        padding-left: 12px;
    }}
    </style>
""", unsafe_allow_html=True)

def genera_pdf(html_content):
    """Converte una stringa HTML in un PDF (bytes) usando WeasyPrint. Restituisce None se la generazione fallisce."""
    try:
        from weasyprint import HTML
    except ImportError:
        st.error("Manca la libreria 'weasyprint' o le sue dipendenze di sistema. Controlla requirements.txt e packages.txt, poi riavvia l'app.")
        return None
    try:
        documento_completo = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: A4;
        margin: 1.5cm;
    }}
    html, body {{
        background-color: white;
        margin: 0;
        padding: 0;
    }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""
        return HTML(string=documento_completo).write_pdf()
    except Exception as e:
        st.error(f"Errore nella generazione del PDF: {e}")
        return None

def get_logo_html(per_pdf=False):
    for ext in ["png", "jpg", "jpeg"]:
        if os.path.exists(f"stemma.{ext}"):
            with open(f"stemma.{ext}", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                if per_pdf:
                    # xhtml2pdf non supporta bene max-width/object-fit: serve una dimensione fissa esplicita.
                    return f"<img src='data:image/{ext};base64,{encoded}' width='90' height='100' style='width:90px; height:100px;'>"
                return f"<img src='data:image/{ext};base64,{encoded}' style='max-width: 100px; max-height: 120px; object-fit: contain;'>"
    if per_pdf:
        return "<div style='font-size: 40px;'>&#9812;</div>"
    return "<div style='font-size: 50px;'>🛡️</div>"

# --- HELPER NOME/COGNOME ---
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

# --- HELPER ORARI (menu a tendina a step di 30 minuti) ---
def genera_orari(inizio="07:00", fine="23:00", step_minuti=30):
    orari = []
    t = datetime.datetime.strptime(inizio, "%H:%M")
    fine_dt = datetime.datetime.strptime(fine, "%H:%M")
    while t <= fine_dt:
        orari.append(t.strftime("%H:%M"))
        t += datetime.timedelta(minutes=step_minuti)
    return orari

ORARI_DISPONIBILI = genera_orari()

def orario_piu_vicino(valore, lista=ORARI_DISPONIBILI):
    """Restituisce l'orario della lista più vicino a 'valore' (formato HH:MM).
    Utile per agganciare alla lista un vecchio orario libero (es. '15:15') salvato prima di questa funzione."""
    try:
        t_valore = datetime.datetime.strptime(str(valore), "%H:%M")
    except (ValueError, TypeError):
        return lista[0]
    return min(lista, key=lambda o: abs((datetime.datetime.strptime(o, "%H:%M") - t_valore).total_seconds()))

def un_ora_prima(orario_str):
    """Calcola l'orario un'ora prima di 'orario_str' (HH:MM), agganciato alla lista di orari disponibili."""
    try:
        t = datetime.datetime.strptime(str(orario_str), "%H:%M") - datetime.timedelta(hours=1)
        return orario_piu_vicino(t.strftime("%H:%M"))
    except (ValueError, TypeError):
        return ORARI_DISPONIBILI[0]

def _callback_orario_partita_modifica(ev_id):
    chiave_partita = f"mod_op_{ev_id}"
    chiave_convocazione = f"mod_oc_{ev_id}"
    if chiave_partita in st.session_state:
        st.session_state[chiave_convocazione] = un_ora_prima(st.session_state[chiave_partita])

def _callback_orario_partita_nuova():
    if "new_orap" in st.session_state:
        st.session_state["new_orac"] = un_ora_prima(st.session_state["new_orap"])

# Inizializzazione Session State
if "db" not in st.session_state: 
    st.session_state.db = caricare_dati()
    if "anagrafica_ruolo" not in st.session_state.db: st.session_state.db["anagrafica_ruolo"] = {}
    if "anagrafica_nascita" not in st.session_state.db: st.session_state.db["anagrafica_nascita"] = {}
    if "storico_capitano" not in st.session_state.db: st.session_state.db["storico_capitano"] = {}
    if "storico_vicecapitano" not in st.session_state.db: st.session_state.db["storico_vicecapitano"] = {}

if "rosa_editor_version" not in st.session_state: st.session_state.rosa_editor_version = 0
if "edit_evento" not in st.session_state: st.session_state.edit_evento = None

if st.session_state.get("ultimo_errore_salvataggio"):
    st.warning(f"⚠️ Ultimo salvataggio parziale — {st.session_state['ultimo_errore_salvataggio']}")

if st.session_state.get("ultimo_errore_sheets"):
    st.error(f"❌ Google Sheets non raggiungibile — {st.session_state['ultimo_errore_sheets']}")

with st.sidebar:
    st.markdown(f"<div style='text-align:center; padding: 12px 0 14px 0;'><div style='display:inline-block; background:white; border-radius:12px; padding:8px 10px;'>{get_logo_html()}</div></div>", unsafe_allow_html=True)

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
                mod_data = st.date_input("Data", curr_date, format="DD/MM/YYYY", key=f"mod_d_{ev['id']}")
                mod_orario = st.text_input("Orario (es. 17:30)", value=ev.get("orario", ev.get("nota", "")), key=f"mod_or_{ev['id']}")
                luogo_precedente = ev.get("luogo", "")
                idx_luogo_mod = CAMPI_ALLENAMENTO.index(luogo_precedente) if luogo_precedente in CAMPI_ALLENAMENTO else 0
                mod_luogo_all = st.selectbox("Luogo", CAMPI_ALLENAMENTO, index=idx_luogo_mod, key=f"mod_lu_all_{ev['id']}")
                
                col_s, col_a = st.columns(2)
                with col_s:
                    if st.button("💾 Salva", key=f"s_mod_{ev['id']}", type="primary"):
                        ev["data"] = str(mod_data)
                        ev["orario"] = mod_orario
                        ev["luogo"] = mod_luogo_all
                        ev.pop("nota", None)
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
                if "orario" in ev or "luogo" in ev:
                    dettaglio_all = " - ".join(filter(None, [ev.get("orario", ""), ev.get("luogo", "")]))
                else:
                    dettaglio_all = ev.get("nota", "")
                titolo_box = f"🔵 Allenamento del {data_f} ({dettaglio_all})"
                
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
                    col_titolo_pres, col_azzera_pres = st.columns([2, 1])
                    with col_titolo_pres:
                        st.write(f"#### 📋 Registro Presenze")
                    with col_azzera_pres:
                        if st.button("🔄 Azzera Presenze", key=f"azzera_pres_{ev['id']}"):
                            if ev["id"] in st.session_state.db["storico_presenze"]:
                                del st.session_state.db["storico_presenze"][ev["id"]]
                            salvare_dati()
                            st.success("Presenze azzerate!")
                            st.rerun()

                    if ev["id"] in st.session_state.db["storico_presenze"]:
                        st.success("✅ Presenze salvate")
                    else:
                        st.error("❌ Presenze non ancora salvate")
                    
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
    nuova_data = st.date_input("Data", datetime.date.today(), format="DD/MM/YYYY", key="new_data_all")
    nuovo_orario = st.text_input("Orario (es. 17:30)", key="new_orario_all")
    nuovo_luogo_all = st.selectbox("Luogo", CAMPI_ALLENAMENTO, key="new_luogo_all")
    if st.button("Aggiungi Allenamento"):
        nuovo_id = str(int(max([int(e["id"]) for e in st.session_state.db["eventi"]], default=0)) + 1)
        st.session_state.db["eventi"].append({"id": nuovo_id, "data": str(nuova_data), "tipo": "Allenamento", "orario": nuovo_orario, "luogo": nuovo_luogo_all})
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
                        valore_attuale_campo = ev.get("indirizzo", "")
                        idx_campo_casa = CAMPI_CASA.index(valore_attuale_campo) if valore_attuale_campo in CAMPI_CASA else 0
                        mod_indirizzo = st.selectbox("Quale campo di casa?", CAMPI_CASA, index=idx_campo_casa, key=f"mod_campo_casa_{ev['id']}")
                with col2:
                    chiave_op = f"mod_op_{ev['id']}"
                    chiave_oc = f"mod_oc_{ev['id']}"
                    if chiave_op not in st.session_state:
                        st.session_state[chiave_op] = orario_piu_vicino(ev.get("ora_partita", ORARI_DISPONIBILI[0]))
                    if chiave_oc not in st.session_state:
                        st.session_state[chiave_oc] = orario_piu_vicino(ev.get("ora_convocazione") or un_ora_prima(st.session_state[chiave_op]))
                    mod_orap = st.selectbox("Ora Partita", ORARI_DISPONIBILI, key=chiave_op, on_change=_callback_orario_partita_modifica, args=(ev['id'],))
                    mod_orac = st.selectbox("Ora Convocazione", ORARI_DISPONIBILI, key=chiave_oc)
                    
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
                            if ev["id"] in st.session_state.db["presenze"]: del st.session_state.db["presenze"][ev["id"]]
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
                    
                    ind_campo = ev.get("indirizzo") or CAMPI_CASA[0]
                    tipo_partita = ev.get("nota", "Campionato")
                    note_agg = ev.get("note_aggiuntive", "")
                    
                    righe_giocatori = ""
                    righe_whatsapp = ""
                    convocati_list = []
                    non_convocati_list = []
                    riga_num = 1

                    # Larghezza colonna Cognome calcolata sul cognome più lungo in rosa (min 9, max 20),
                    # così il nome intero è sempre visibile e la tabella si adatta da sola se la rosa cambia.
                    larghezza_cognome_wa = 9
                    if st.session_state.db["ragazzi"]:
                        larghezza_cognome_wa = max(9, min(20, max(len(dividi_nome(g)[1]) for g in st.session_state.db["ragazzi"])))
                    
                    for ragazzo in ordina_giocatori(st.session_state.db["ragazzi"]):
                        stato = appello_evento.get(ragazzo, "🟢 Convocato")
                        is_convocato = "Convocato" in stato and "Non" not in stato
                        
                        c_mark = "X" if is_convocato else ""
                        nc_mark = "X" if not is_convocato else ""
                        
                        if is_convocato:
                            convocati_list.append(ragazzo)
                        else:
                            non_convocati_list.append(ragazzo)

                        nome_wa, cognome_wa = dividi_nome(ragazzo)
                        nome_iniziale_wa = f"{nome_wa[0].upper()}." if nome_wa else ""
                        c_wa = "✓" if is_convocato else " "
                        nc_wa = "✓" if not is_convocato else " "
                        righe_whatsapp += f"{cognome_wa[:larghezza_cognome_wa]:<{larghezza_cognome_wa + 1}}{nome_iniziale_wa:<4}{c_wa:^3}{nc_wa:^3}\n"
                            
                        righe_giocatori += f"<tr><td style='border: 1px solid black; padding: 5px;'>{riga_num}</td><td style='border: 1px solid black; padding: 5px; text-align: left;'>{cognome_nome(ragazzo)}</td><td style='border: 1px solid black; padding: 5px; color: green; font-weight: bold;'>{c_mark}</td><td style='border: 1px solid black; padding: 5px; color: red; font-weight: bold;'>{nc_mark}</td></tr>"
                        riga_num += 1
                    
                    righe_formazione = ""
                    if titolari_evento:
                        titolari_validi = ordina_giocatori([t for t in titolari_evento if t in convocati_list])
                        for t in titolari_validi:
                            num = numeri_evento.get(t, '-')
                            nome_t, cognome_t = dividi_nome(t)
                            
                            badge = ""
                            if t == capitano_evento: badge = f" <span style='color: {COLORE_BLU}; font-weight: bold;'>(C)</span>"
                            elif t == vice_evento: badge = f" <span style='color: {COLORE_BLU_ACCENTO}; font-weight: bold;'>(VC)</span>"
                            
                            righe_formazione += f"<tr><td style='border: 1px solid black; padding: 5px; font-weight: bold; width: 10%;'>{num}</td><td style='border: 1px solid black; padding: 5px; text-align: left; width: 45%;'>{cognome_t}</td><td style='border: 1px solid black; padding: 5px; text-align: left; width: 45%;'>{nome_t}{badge}</td></tr>"
                    else:
                        righe_formazione = "<tr><td colspan='3' style='border: 1px solid black; padding: 5px; font-style: italic;'>Nessun titolare selezionato</td></tr>"
                    
                    logo_immagine = get_logo_html()
                    
                    # HTML Convocazioni
                    html_distinta = f"""<div style='background-color: white; color: black; padding: 10px; font-family: Arial, sans-serif; width: 100%;'>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid {COLORE_BLU};'>
<tr>
<td style='width: 30%; border: 1px solid black; vertical-align: middle; padding: 10px;'>{logo_immagine}</td>
<td style='width: 70%; border: 1px solid black; padding: 0;'>
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
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid {COLORE_BLU}; border-top: none;'>
<tr style='font-weight: bold; background-color: {COLORE_BLU_CHIARO};'>
<td style='border: 1px solid black; padding: 5px; width: 10%;'>N°</td>
<td style='border: 1px solid black; padding: 5px; width: 50%;'>Cognome e Nome</td>
<td style='border: 1px solid black; padding: 5px; width: 20%;' title='Convocato'>C</td>
<td style='border: 1px solid black; padding: 5px; width: 20%;' title='Non Convocato'>NC</td>
</tr>
{righe_giocatori}
</table>
</div>"""

                    # HTML Formazione
                    html_formazione = f"""<div style='background-color: white; color: black; padding: 10px; font-family: Arial, sans-serif; width: 100%;'>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid {COLORE_BLU_ACCENTO};'>
<tr>
<td style='width: 30%; border: 1px solid black; vertical-align: middle; padding: 10px;'>{logo_immagine}</td>
<td style='width: 70%; border: 1px solid black; padding: 0;'>
<table style='width: 100%; border-collapse: collapse; text-align: center;'>
<tr><td style='padding: 5px; font-weight: bold; font-size: 16px; background-color: {COLORE_BLU_ACCENTO_CHIARO}; border-bottom: 1px solid black;'>FORMAZIONE UFFICIALE</td></tr>
<tr><td style='padding: 5px; border-bottom: 1px solid black;'>PARTITA: {sq_casa} - {sq_trasf}</td></tr>
<tr><td style='padding: 5px; font-weight: bold; border-bottom: 1px solid black;'>TIPO PARTITA: {tipo_partita}</td></tr>
<tr><td style='padding: 5px;'>DATA: {data_f}</td></tr>
</table>
</td>
</tr>
</table>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid {COLORE_BLU_ACCENTO}; border-top: none;'>
<tr style='font-weight: bold; background-color: {COLORE_BLU_ACCENTO_CHIARO};'>
<td style='border: 1px solid black; padding: 5px; width: 10%;'>N°</td>
<td style='border: 1px solid black; padding: 5px; width: 45%;'>Cognome</td>
<td style='border: 1px solid black; padding: 5px; width: 45%;'>Nome</td>
</tr>
{righe_formazione}
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
                    if note_agg: whatsapp_text += f"📝 *Note:* {note_agg}\n"
                        
                    intestazione_wa = f"{'Cognome':<{larghezza_cognome_wa + 1}}{'Nome':<4}{'C':^3}{'NC':^3}\n"
                    separatore_wa = "-" * (larghezza_cognome_wa + 1 + 4 + 3 + 3) + "\n"
                    whatsapp_text += f"\n*ELENCO GIOCATORI:*\n"
                    whatsapp_text += "```\n" + intestazione_wa + separatore_wa + righe_whatsapp + "```\n"

                    tab1, tab2, tab_formazione, tab3 = st.tabs(["⚙️ Compila Elenco", "📄 Convocazioni Ufficiali", "⚽ Formazione e Dati Partita", "📱 Messaggio WhatsApp"])
                    
                    with tab1:
                        if not st.session_state.db["ragazzi"]:
                            st.warning("Rosa vuota.")
                        else:
                            col_titolo_conv, col_azzera_conv = st.columns([2, 1])
                            with col_titolo_conv:
                                st.write("#### 🏃 Seleziona Convocati")
                            with col_azzera_conv:
                                if st.button("🔄 Azzera Convocazioni", key=f"azzera_conv_{ev['id']}"):
                                    if ev["id"] in st.session_state.db["storico_presenze"]:
                                        del st.session_state.db["storico_presenze"][ev["id"]]
                                    salvare_dati()
                                    st.success("Convocazioni azzerate!")
                                    st.rerun()
                            resoconto_corrente = {}
                            opzioni = ["🟢 Convocato", "🔴 Non Convocato"]

                            if ev["id"] in st.session_state.db["storico_presenze"]:
                                st.success("✅ Convocazioni salvate")
                            else:
                                st.error("❌ Convocazioni non ancora salvate")
                            
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
                        e_coppa = (tipo_partita == "Coppa Brescia")
                        if e_coppa:
                            st.caption("Partita di Coppa: risultato su 2 tempi.")
                            col_t1, col_t2 = st.columns(2)
                            with col_t1:
                                ris_t1 = st.text_input("1° Tempo (es. 1-0)", value=ris_evento.get("t1", ""), key=f"ris_t1_{ev['id']}")
                            with col_t2:
                                ris_t2 = st.text_input("2° Tempo (es. 2-2)", value=ris_evento.get("t2", ""), key=f"ris_t2_{ev['id']}")
                            ris_t3 = ""
                        else:
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

                            # --- Costruzione tabella dati (sostituisce il vecchio layout a colonne) ---
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

                            st.caption("Tocca una cella per modificarla. La tabella si adatta automaticamente allo schermo, anche su smartphone. N° a 0 = numero di maglia non ancora assegnato (nel documento ufficiale comparirà '-').")

                            df_edit = st.data_editor(
                                df_formazione,
                                key=f"data_editor_form_{ev['id']}",
                                hide_index=True,
                                width="stretch",
                                column_order=["N°", "Cognome", "Nome", "Tit.", "Gol"],
                                column_config={
                                    "N°": st.column_config.NumberColumn("N°", min_value=0, max_value=99, step=1, width="small", format="%d"),
                                    "Cognome": st.column_config.TextColumn("Cognome", disabled=True, width="medium"),
                                    "Nome": st.column_config.TextColumn("Nome", disabled=True, width="medium"),
                                    "Tit.": st.column_config.CheckboxColumn("Tit.", width="small"),
                                    "Gol": st.column_config.NumberColumn("Gol", min_value=0, max_value=99, step=1, width="small", format="%d"),
                                },
                            )

                            # Riallineo l'indice del giocatore alle righe restituite dal data_editor
                            df_edit = df_edit.copy()
                            df_edit["Giocatore"] = df_formazione["Giocatore"].values

                            nuovi_titolari = df_edit.loc[df_edit["Tit."] == True, "Giocatore"].tolist()
                            # N.B.: un N° pari a 0 è considerato "non assegnato" e viene escluso,
                            # così nel documento ufficiale compare correttamente "-" invece di "0".
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
                            st.warning("⚠️ Non sono riuscito a generare il PDF. Scarica la versione HTML in alternativa.")
                            st.download_button(
                                label="⬇️ Scarica Convocazioni (.html)",
                                data=html_distinta,
                                file_name=f"Convocazioni_{sq_casa}_{sq_trasf}.html",
                                mime="text/html",
                                key=f"dl_html_conv_fallback_{ev['id']}"
                            )
                        st.caption("📎 WhatsApp non permette di allegare automaticamente un file da un sito esterno: scarica il PDF qui sopra, poi allegalo manualmente nella chat. Nella scheda '📱 Messaggio WhatsApp' trovi un pulsante per aprire subito la chat con il testo già pronto.")

                    with tab3:
                        st.code(whatsapp_text, language="markdown")
                        st.caption("💡 Clicca sull'iconcina dei foglietti in alto a destra in questo riquadro nero per copiare tutto il testo in un colpo solo e incollarlo su WhatsApp!")

                        st.write("---")
                        wa_url = "https://api.whatsapp.com/send?text=" + urllib.parse.quote(whatsapp_text)
                        if hasattr(st, "link_button"):
                            st.link_button("📲 Apri WhatsApp con questo messaggio", wa_url)
                        else:
                            st.markdown(f"[📲 Apri WhatsApp con questo messaggio]({wa_url})")
                        st.info("WhatsApp non consente di allegare automaticamente un PDF da un sito web (limite della piattaforma, non dell'app). Dopo aver aperto la chat: scarica il PDF dalla scheda '📄 Convocazioni Ufficiali' e allegalo manualmente con l'icona della graffetta 📎.")

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
            nuovo_indirizzo = st.selectbox("Quale campo di casa?", CAMPI_CASA, key="new_campo_casa")
    with col2:
        if "new_orap" not in st.session_state:
            st.session_state["new_orap"] = orario_piu_vicino("15:00")
        if "new_orac" not in st.session_state:
            st.session_state["new_orac"] = un_ora_prima(st.session_state["new_orap"])
        nuova_orap = st.selectbox("Ora Partita", ORARI_DISPONIBILI, key="new_orap", on_change=_callback_orario_partita_nuova)
        nuova_orac = st.selectbox("Ora Convocazione", ORARI_DISPONIBILI, key="new_orac")
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
                "indirizzo": nuovo_indirizzo, "nota": nuova_nota, "note_aggiuntive": nuova_nota_agg
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
            html_all = f"<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Allenamenti</h2><p><strong>Allenamenti totali: {totale_allenamenti}</strong></p><table border='1' style='border-collapse: collapse; text-align: center; width:100%;'><tr><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>Giocatore</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🟢 Presenze</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🔴 Assenze</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🟡 Infortuni</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>📈 % Presenza</th></tr>"
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
            html_giocatori = f"<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Giocatori</h2><p><strong>Gare totali: {totale_gare}</strong></p><table border='1' style='border-collapse: collapse; text-align: center; width:100%;'><tr><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>Giocatore</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🟢 Convocato</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🔴 Non Conv.</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>👕 Titolare</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>📈 % Conv.</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>🏅 % Titolare</th><th style='padding:8px; background-color: {COLORE_BLU_CHIARO};'>⚽ Gol Fatti</th></tr>"
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

    def esito_singolo_tempo(ris_str, luogo="Casa"):
        """Restituisce 'V', 'P' o 'S' per un singolo tempo, oppure None se non è stato inserito un risultato."""
        if not str(ris_str).strip():
            return None
        pu, pa, gf, gs = parse_tempo(ris_str, luogo)
        if pu == 0 and pa == 0:
            return None
        if pu > pa: return "V"
        elif pu < pa: return "S"
        else: return "P"

    eventi_partita = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] in ["Partita", "Torneo"]]
    
    tot_partite = 0
    tot_gf = 0
    tot_gs = 0
    vittorie = 0
    pareggi = 0
    sconfitte = 0
    vittorie_t1, pareggi_t1, sconfitte_t1 = 0, 0, 0
    vittorie_t2, pareggi_t2, sconfitte_t2 = 0, 0, 0
    vittorie_t3, pareggi_t3, sconfitte_t3 = 0, 0, 0
    
    righe_partite = ""
    
    for ev in eventi_partita:
        ris_evento = st.session_state.db["storico_risultati"].get(ev["id"], {})
        t1 = ris_evento.get("t1", "")
        t2 = ris_evento.get("t2", "")
        t3 = ris_evento.get("t3", "")
        
        if t1 or t2 or t3:
            tot_partite += 1
            luogo_gara = ev.get("luogo", "Casa")
            e_coppa_stat = (ev.get("nota", "Campionato") == "Coppa Brescia")

            esito_t1 = esito_singolo_tempo(t1, luogo_gara)
            esito_t2 = esito_singolo_tempo(t2, luogo_gara)
            esito_t3 = esito_singolo_tempo(t3, luogo_gara)
            if esito_t1 == "V": vittorie_t1 += 1
            elif esito_t1 == "P": pareggi_t1 += 1
            elif esito_t1 == "S": sconfitte_t1 += 1
            if esito_t2 == "V": vittorie_t2 += 1
            elif esito_t2 == "P": pareggi_t2 += 1
            elif esito_t2 == "S": sconfitte_t2 += 1
            if esito_t3 == "V": vittorie_t3 += 1
            elif esito_t3 == "P": pareggi_t3 += 1
            elif esito_t3 == "S": sconfitte_t3 += 1
            pu1, pa1, gf1, gs1 = parse_tempo(t1, luogo_gara)
            pu2, pa2, gf2, gs2 = parse_tempo(t2, luogo_gara)
            pu3, pa3, gf3, gs3 = parse_tempo(t3, luogo_gara)
            
            p_uso_tot = pu1 + pu2 + pu3
            p_avv_tot = pa1 + pa2 + pa3
            
            gf_partita = gf1 + gf2 + gf3
            gs_partita = gs1 + gs2 + gs3
            
            tot_gf += gf_partita
            tot_gs += gs_partita
            
            if e_coppa_stat:
                # Partita di Coppa: trattata come una partita normale, risultato finale = somma dei gol dei 2 tempi
                esito_tabella = f"{gf_partita} - {gs_partita}"
                if gf_partita > gs_partita:
                    vittorie += 1
                elif gf_partita < gs_partita:
                    sconfitte += 1
                else:
                    pareggi += 1
            else:
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
                
            data_f = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
            
            sq_casa = "USO UNITED" if luogo_gara == "Casa" else ev.get("avversario", "Avversario")
            sq_trasf = ev.get("avversario", "Avversario") if luogo_gara == "Casa" else "USO UNITED"
            stringa_partita = f"{sq_casa}-{sq_trasf}"
            
            righe_partite += f"<tr><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{data_f}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{stringa_partita}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t1 if t1 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t2 if t2 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t3 if t3 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px; font-weight: bold;'>{esito_tabella}</td></tr>"

    riepilogo_html = f"""<table style="width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; color: var(--text-color);">
<tr style="background-color: rgba(128,128,128,0.2); font-weight: bold;">
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Gare Giocate</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Vittorie</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Pareggi</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Sconfitte</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Gol Fatti</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Gol Subiti</td>
</tr>
<tr>
<td style="padding: 15px; font-size: 24px; font-weight: bold; border: 1px solid rgba(128,128,128,0.3);">{tot_partite}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #4CAF50; border: 1px solid rgba(128,128,128,0.3);">{vittorie}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #FF9800; border: 1px solid rgba(128,128,128,0.3);">{pareggi}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #F44336; border: 1px solid rgba(128,128,128,0.3);">{sconfitte}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #4CAF50; border: 1px solid rgba(128,128,128,0.3);">{tot_gf}</td>
<td style="padding: 15px; font-size: 24px; font-weight: bold; color: #F44336; border: 1px solid rgba(128,128,128,0.3);">{tot_gs}</td>
</tr>
</table>"""
    st.markdown(riepilogo_html, unsafe_allow_html=True)

    st.write("---")
    st.subheader("⏱️ Statistiche per Tempo")
    st.caption("Vittorie, pareggi e sconfitte contati singolarmente per ciascun tempo di gioco, su tutte le partite con un risultato inserito. Le partite di Coppa hanno solo 1° e 2° tempo, per questo non contribuiscono alla riga del 3° tempo.")
    tabella_tempi_html = f"""<table style="width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; color: var(--text-color);">
<tr style="background-color: rgba(128,128,128,0.2); font-weight: bold;">
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Tempo</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Vittorie</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Pareggi</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3);">Sconfitte</td>
</tr>
<tr>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); font-weight: bold;">1° Tempo</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #4CAF50; font-weight: bold;">{vittorie_t1}</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #FF9800; font-weight: bold;">{pareggi_t1}</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #F44336; font-weight: bold;">{sconfitte_t1}</td>
</tr>
<tr>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); font-weight: bold;">2° Tempo</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #4CAF50; font-weight: bold;">{vittorie_t2}</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #FF9800; font-weight: bold;">{pareggi_t2}</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #F44336; font-weight: bold;">{sconfitte_t2}</td>
</tr>
<tr>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); font-weight: bold;">3° Tempo</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #4CAF50; font-weight: bold;">{vittorie_t3}</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #FF9800; font-weight: bold;">{pareggi_t3}</td>
<td style="padding: 10px; border: 1px solid rgba(128,128,128,0.3); color: #F44336; font-weight: bold;">{sconfitte_t3}</td>
</tr>
</table>"""
    st.markdown(tabella_tempi_html, unsafe_allow_html=True)
    
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
            html_squadra = f"<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Squadra</h2>{riepilogo_html}<h2>Statistiche per Tempo</h2>{tabella_tempi_html}<h2>Dettaglio Partite</h2>{tabella_html}</body></html>"
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

        # La chiave include una "versione": dopo ogni salvataggio la incrementiamo per
        # forzare un widget pulito e non farci reincollare in tabella modifiche vecchie
        # (es. un'eliminazione già salvata) su righe che nel frattempo si sono spostate.
        df_rosa_edit = st.data_editor(
            df_rosa,
            key=f"data_editor_rosa_{st.session_state.rosa_editor_version}",
            hide_index=True,
            width="stretch",
            num_rows="fixed",
            column_order=["Cognome", "Nome", "Data di Nascita", "🗑️ Elimina"],
            column_config={
                "Cognome": st.column_config.TextColumn("Cognome", width="medium"),
                "Nome": st.column_config.TextColumn("Nome", width="medium"),
                "Data di Nascita": st.column_config.DateColumn("Data di Nascita", format="DD/MM/YYYY", width="small"),
                "🗑️ Elimina": st.column_config.CheckboxColumn("🗑️ Elimina", width="small"),
            },
        )

        if st.button("💾 Salva Modifiche Rosa", key="btn_salva_rosa", type="primary"):
            # --- Validazione preliminare: Nome obbligatorio, nessun duplicato ---
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
                        # Ripulisce anche tutte le tracce nello storico, così un giocatore
                        # cancellato sparisce davvero e non resta "fantasma" nei dati salvati.
                        for _, appello in st.session_state.db["storico_presenze"].items():
                            appello.pop(nome_originale, None)
                        for _, titolari_list in st.session_state.db["storico_titolari"].items():
                            if nome_originale in titolari_list:
                                titolari_list.remove(nome_originale)
                        for _, numeri_dict in st.session_state.db["storico_numeri"].items():
                            if numeri_dict:
                                numeri_dict.pop(nome_originale, None)
                        for _, gol_dict in st.session_state.db["storico_gol"].items():
                            if gol_dict:
                                gol_dict.pop(nome_originale, None)
                        for campo_fascia in ("storico_capitano", "storico_vicecapitano"):
                            for ev_id_f, nome_assegnato in st.session_state.db.get(campo_fascia, {}).items():
                                if nome_assegnato == nome_originale:
                                    st.session_state.db[campo_fascia][ev_id_f] = ""
                        continue

                    nome_pulito = str(row["Nome"]).strip()
                    cognome_pulito = str(row["Cognome"]).strip()
                    nome_nuovo = f"{nome_pulito} {cognome_pulito}".strip()
                    nascita_nuova = row["Data di Nascita"]
                    ruolo_nuovo = row["Ruolo"]

                    if nome_nuovo != nome_originale:
                        # Propaga la rinomina a tutto lo storico, come nel comportamento precedente
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

                # Persistiamo la rosa già in ordine alfabetico per Cognome
                st.session_state.db["ragazzi"] = ordina_giocatori(nuova_lista_ragazzi)
                st.session_state.rosa_editor_version += 1
                salvare_dati()
                st.success("✅ Rosa aggiornata con successo!")
                st.rerun()

        with st.expander("📋 Importa elenco giocatori da testo"):
            st.caption("Incolla un elenco, una riga per giocatore, nel formato: **Cognome Nome GG/MM/AAAA** (va bene anche un cognome composto da più parole, es. 'Prandini Busi Giuliano 19/06/2014'). I giocatori già presenti in rosa (stesso nome e cognome) vengono saltati automaticamente, gli altri dati dell'app (partite, allenamenti) non vengono toccati.")
            testo_elenco = st.text_area("Elenco da incollare", height=200, key="testo_elenco_import", placeholder="Abrami Tommaso 07/11/2014\nBertelli Nicolò 11/10/2014\n...")

            if st.button("📋 Importa Elenco", key="btn_importa_elenco"):
                aggiunti, gia_presenti, righe_non_riconosciute = [], [], []
                for riga in testo_elenco.splitlines():
                    riga = riga.strip()
                    if not riga:
                        continue
                    match_data = re.search(r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\s*$', riga)
                    if not match_data:
                        righe_non_riconosciute.append(riga)
                        continue
                    giorno, mese, anno = match_data.groups()
                    parte_nome = riga[:match_data.start()].strip()
                    parole = parte_nome.split()
                    if len(parole) < 2:
                        righe_non_riconosciute.append(riga)
                        continue
                    nome_estratto = parole[-1]
                    cognome_estratto = " ".join(parole[:-1])
                    try:
                        data_iso = f"{int(anno):04d}-{int(mese):02d}-{int(giorno):02d}"
                        datetime.datetime.strptime(data_iso, "%Y-%m-%d")  # valida che sia una data reale
                    except ValueError:
                        righe_non_riconosciute.append(riga)
                        continue

                    nome_completo_import = f"{nome_estratto} {cognome_estratto}".strip()
                    if nome_completo_import in st.session_state.db["ragazzi"]:
                        gia_presenti.append(cognome_nome(nome_completo_import))
                    else:
                        st.session_state.db["ragazzi"].append(nome_completo_import)
                        st.session_state.db.setdefault("anagrafica_nascita", {})[nome_completo_import] = data_iso
                        aggiunti.append(cognome_nome(nome_completo_import))

                if aggiunti:
                    st.session_state.db["ragazzi"] = ordina_giocatori(st.session_state.db["ragazzi"])
                    salvare_dati()
                    st.success(f"✅ Aggiunti {len(aggiunti)} giocatori: {', '.join(aggiunti)}")
                if gia_presenti:
                    st.info(f"ℹ️ Già presenti, saltati: {', '.join(gia_presenti)}")
                if righe_non_riconosciute:
                    st.warning("⚠️ Righe non riconosciute (controlla il formato):\n" + "\n".join(righe_non_riconosciute))
                if aggiunti:
                    st.rerun()

        with st.expander("💾 Backup e Ripristino"):
            st.write("#### ⬇️ Scarica Backup")
            st.caption("Scarica una copia completa di tutti i dati (rosa, presenze, partite, formazioni) in un file .json sul tuo telefono o computer.")
            st.download_button(
                label="⬇️ Scarica Backup completo (.json)",
                data=json.dumps(st.session_state.db, ensure_ascii=False, indent=4),
                file_name=f"backup_misterapp_{datetime.date.today().strftime('%Y%m%d')}.json",
                mime="application/json",
                key="btn_scarica_backup"
            )

            st.write("---")
            st.write("#### ⬆️ Importa Backup")
            st.caption("⚠️ Attenzione: importare un backup SOSTITUISCE tutti i dati attuali dell'app con quelli del file. Usalo solo se sai cosa stai facendo (es. per ripristinare uno stato precedente).")
            file_caricato = st.file_uploader("Carica un file di backup (.json)", type=["json"], key="upload_backup")

            if file_caricato is not None:
                try:
                    contenuto_caricato = json.loads(file_caricato.read().decode("utf-8"))
                except json.JSONDecodeError:
                    st.error("❌ Il file caricato non è un JSON valido.")
                    contenuto_caricato = None
                except Exception as e:
                    st.error(f"❌ Errore durante la lettura del file: {e}")
                    contenuto_caricato = None

                if contenuto_caricato is not None:
                    if not isinstance(contenuto_caricato, dict) or "ragazzi" not in contenuto_caricato or "eventi" not in contenuto_caricato:
                        st.error("❌ Il file non sembra un backup valido di MisterApp (mancano i campi essenziali 'ragazzi' o 'eventi').")
                    else:
                        n_giocatori = len(contenuto_caricato.get("ragazzi", []))
                        n_eventi = len(contenuto_caricato.get("eventi", []))
                        st.warning(f"⚠️ Questo file contiene **{n_giocatori} giocatori** e **{n_eventi} eventi** (allenamenti/partite). Importandolo, TUTTI i dati attuali dell'app verranno sostituiti con questi. L'operazione non si può annullare, a meno di avere un backup precedente da reimportare.")
                        conferma_import = st.checkbox("Ho capito, voglio procedere con l'importazione", key="conferma_importazione")
                        if conferma_import:
                            if st.button("♻️ Conferma e Importa Backup", key="btn_conferma_importa", type="primary"):
                                for k in CHIAVI_DATI_DEFAULT:
                                    if k not in contenuto_caricato: contenuto_caricato[k] = {}
                                st.session_state.db = contenuto_caricato
                                st.session_state.rosa_editor_version += 1
                                salvare_dati()
                                st.success("✅ Backup importato e salvato con successo!")
                                st.rerun()

        with st.expander("🧹 Pulizia dati orfani (avanzato)"):
            st.caption("Rimuove dallo storico (presenze, formazioni, gol, fasce, anagrafica) qualsiasi nome che non è più nella rosa attuale. Utile per ripulire tracce di giocatori cancellati in passato, prima che la pulizia automatica esistesse.")
            if st.button("🧹 Esegui pulizia dati orfani", key="btn_pulizia_orfani"):
                nomi_attuali = set(st.session_state.db["ragazzi"])
                rimossi = set()

                for appello in st.session_state.db.get("storico_presenze", {}).values():
                    for nome in list(appello.keys()):
                        if nome not in nomi_attuali:
                            rimossi.add(nome)
                            appello.pop(nome, None)

                for titolari_list in st.session_state.db.get("storico_titolari", {}).values():
                    for nome in list(titolari_list):
                        if nome not in nomi_attuali:
                            rimossi.add(nome)
                            titolari_list.remove(nome)

                for numeri_dict in st.session_state.db.get("storico_numeri", {}).values():
                    if numeri_dict:
                        for nome in list(numeri_dict.keys()):
                            if nome not in nomi_attuali:
                                rimossi.add(nome)
                                numeri_dict.pop(nome, None)

                for gol_dict in st.session_state.db.get("storico_gol", {}).values():
                    if gol_dict:
                        for nome in list(gol_dict.keys()):
                            if nome not in nomi_attuali:
                                rimossi.add(nome)
                                gol_dict.pop(nome, None)

                for campo_fascia in ("storico_capitano", "storico_vicecapitano"):
                    for ev_id_f, nome_assegnato in st.session_state.db.get(campo_fascia, {}).items():
                        if nome_assegnato and nome_assegnato not in nomi_attuali:
                            rimossi.add(nome_assegnato)
                            st.session_state.db[campo_fascia][ev_id_f] = ""

                for chiave_anagrafica in ("anagrafica_ruolo", "anagrafica_nascita"):
                    for nome in list(st.session_state.db.get(chiave_anagrafica, {}).keys()):
                        if nome not in nomi_attuali:
                            rimossi.add(nome)
                            st.session_state.db[chiave_anagrafica].pop(nome, None)

                if rimossi:
                    salvare_dati()
                    st.success(f"✅ Rimossi {len(rimossi)} nome/i orfano/i: {', '.join(sorted(cognome_nome(n) for n in rimossi))}")
                    st.rerun()
                else:
                    st.info("ℹ️ Nessun dato orfano trovato, è già tutto pulito.")

    st.subheader("➕ Aggiungi un nuovo giocatore")
    with st.container():
        col_c, col_n, col_d = st.columns([2, 2, 1.5])
        with col_c: nuovo_cognome_ins = st.text_input("Cognome:", key="nuovo_ins_cognome")
        with col_n: nuovo_nome_ins = st.text_input("Nome:", key="nuovo_ins_nome")
        with col_d: nuova_nascita_ins = st.date_input("Data di Nascita", datetime.date(2014, 1, 1))
        
        if st.button("Inserisci in Squadra", type="primary"):
            nome_completo_ins = f"{nuovo_nome_ins.strip()} {nuovo_cognome_ins.strip()}".strip()
            if nuovo_nome_ins.strip() == "":
                st.error("Il campo 'Nome' non può essere vuoto.")
            elif nome_completo_ins in st.session_state.db["ragazzi"]:
                st.error(f"'{cognome_nome(nome_completo_ins)}' è già presente in rosa.")
            else:
                st.session_state.db["ragazzi"].append(nome_completo_ins)
                st.session_state.db.setdefault("anagrafica_nascita", {})[nome_completo_ins] = str(nuova_nascita_ins)
                salvare_dati()
                st.success(f"⚽ {cognome_nome(nome_completo_ins)} aggiunto alla rosa!")
                st.rerun()