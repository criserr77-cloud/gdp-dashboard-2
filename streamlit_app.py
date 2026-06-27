import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAZIONE GOOGLE SHEETS ---
ID_FOGLIO_GOOGLE = "1PCmJ9tgv-ohAIuc3CmwP4BOZLg68qSLmkLYwSQ7pSsc" 

def connetti_foglio():
    try:
       scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_FOGLIO_GOOGLE).sheet1
        # Debug visivo: ti dice a quale foglio si è collegato
        st.sidebar.write(f"Connesso a: '{sheet.title}'") 
        return sheet
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return None

def caricare_dati():
    sheet = connetti_foglio()
    if sheet:
        contenuto = sheet.cell(1, 1).value
        if contenuto:
            dati = json.loads(contenuto)
            # Controllo chiavi esistenti
            for k in ["storico_presenze", "storico_minutaggio", "storico_titolari", "storico_moduli", "storico_numeri", "storico_gol", "storico_risultati"]:
                if k not in dati: dati[k] = {}
            return dati
    
    # Ritorno dati di default se foglio vuoto o errore
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
        try:
            stringa_json = json.dumps(st.session_state.db, ensure_ascii=False)
            # update è più affidabile di update_cell
            sheet.update('A1', [[stringa_json]])
            st.toast("✅ Dati salvati sul foglio!", icon="✅")
        except Exception as e:
            st.error(f"Errore scrittura: {e}")
    else:
        st.error("Connessione foglio non disponibile.")

# Inizializzazione dati
if "db" not in st.session_state:
    st.session_state.db = caricare_dati()
    import streamlit as st
import datetime
import json
import os
import base64

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="MisterApp - Settore Giovanile", layout="centered")

# --- CSS PER LOOK MOBILE E MENU RESPONSIVE (DARK/LIGHT MODE) ---
st.markdown("""
    <style>
    /* Colori nativi del tema di Streamlit per adattarsi perfettamente alla Dark Mode */
    .card { 
        background-color: var(--secondary-background-color); 
        color: var(--text-color);
        border-radius: 15px; 
        padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        margin-bottom: 20px; 
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 12px 15px !important;
        margin-bottom: 10px !important;
        background-color: var(--secondary-background-color);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FILE DI SALVATAGGIO (DATABASE LOCALE) ---
DB_FILE = "misterapp_db.json"

def caricare_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            dati = json.load(f)
            if "storico_minutaggio" not in dati: dati["storico_minutaggio"] = {}
            if "storico_titolari" not in dati: dati["storico_titolari"] = {}
            if "storico_moduli" not in dati: dati["storico_moduli"] = {}
            if "storico_numeri" not in dati: dati["storico_numeri"] = {}
            if "storico_gol" not in dati: dati["storico_gol"] = {}
            if "storico_risultati" not in dati: dati["storico_risultati"] = {}
            return dati
    else:
        return {
            "ragazzi": ["Luca R.", "Matteo V.", "Alessandro M.", "Filippo T.", "Gabriele L.", "Tommaso N."],
            "eventi": [
                {"id": "1", "data": "2026-06-23", "tipo": "Allenamento", "nota": "Campo Principale - ore 17:30"},
                {"id": "2", "data": "2026-06-27", "tipo": "Partita", "avversario": "Real City", "luogo": "Trasferta", "ora_partita": "15:00", "ora_convocazione": "14:00", "indirizzo": "Via Stadio 5, Torino", "nota": "Campionato"}
            ],
            "storico_presenze": {},
            "storico_minutaggio": {},
            "storico_titolari": {},
            "storico_moduli": {},
            "storico_numeri": {},
            "storico_gol": {},
            "storico_risultati": {}
        }

def salvare_dati():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, indent=4, ensure_ascii=False)

def get_logo_html():
    for ext in ["png", "jpg", "jpeg"]:
        if os.path.exists(f"stemma.{ext}"):
            with open(f"stemma.{ext}", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                return f"<img src='data:image/{ext};base64,{encoded}' style='max-width: 100px; max-height: 120px; object-fit: contain;'>"
    return "<div style='font-size: 50px;'>🛡️</div><div style='color: red; font-weight: bold; font-size: 14px;'>USO</div><div style='color: green; font-weight: bold; font-size: 14px;'>UNITED</div>"

# Inizializziamo lo stato di Streamlit
if "db" not in st.session_state:
    st.session_state.db = caricare_dati()
    if "storico_minutaggio" not in st.session_state.db: st.session_state.db["storico_minutaggio"] = {}
    if "storico_titolari" not in st.session_state.db: st.session_state.db["storico_titolari"] = {}
    if "storico_moduli" not in st.session_state.db: st.session_state.db["storico_moduli"] = {}
    if "storico_numeri" not in st.session_state.db: st.session_state.db["storico_numeri"] = {}
    if "storico_gol" not in st.session_state.db: st.session_state.db["storico_gol"] = {}
    if "storico_risultati" not in st.session_state.db: st.session_state.db["storico_risultati"] = {}

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "edit_evento" not in st.session_state:
    st.session_state.edit_evento = None

# --- MENU LATERALE ---
menu = st.sidebar.radio("Navigazione", [
    "🔵 Calendario Allenamenti",
    "🟢 Calendario e Convocazioni", 
    "📊 Statistiche Allenamenti",
    "🏆 Statistiche Giocatori",
    "📈 Statistiche Squadra",
    "🏃 Gestione Rosa"
])

st.sidebar.write("---")
st.sidebar.info("MisterApp Cloud - Attiva")

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
                mod_nota = st.text_input("Note/Orario", value=ev.get("nota", ""), key=f"mod_n_{ev['id']}")
                
                col_s, col_a = st.columns(2)
                with col_s:
                    if st.button("💾 Salva", key=f"s_mod_{ev['id']}", type="primary"):
                        ev["data"] = str(mod_data)
                        ev["nota"] = mod_nota
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
                titolo_box = f"🔵 Allenamento del {data_f} ({ev.get('nota', '')})"
                
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
                            if ev["id"] in st.session_state.db["storico_minutaggio"]: del st.session_state.db["storico_minutaggio"][ev["id"]]
                            salvare_dati()
                            st.rerun()
                    
                    st.write("---")
                    st.write(f"#### 📋 Registro Presenze")
                    
                    if not st.session_state.db["ragazzi"]:
                        st.warning("Rosa vuota.")
                    else:
                        appello_evento = st.session_state.db["storico_presenze"].get(ev["id"], {})
                        resoconto_corrente = {}
                        opzioni = ["🟢 Presente", "🔴 Assente", "🟡 Infortunato"]
                        
                        for ragazzo in st.session_state.db["ragazzi"]:
                            col_nome, col_stato = st.columns([1, 2])
                            with col_nome: st.write(f"**{ragazzo}**")
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
    nuova_nota = st.text_input("Orario e Luogo (es. '17:30 Campo B')", key="new_nota_all")
    if st.button("Aggiungi Allenamento"):
        nuovo_id = str(int(max([int(e["id"]) for e in st.session_state.db["eventi"]], default=0)) + 1)
        st.session_state.db["eventi"].append({"id": nuovo_id, "data": str(nuova_data), "tipo": "Allenamento", "nota": nuova_nota})
        salvare_dati()
        st.rerun()

# ==========================================
# SCHERMATA 2: PARTITE E DISTINTA UFFICIALE
# ==========================================
elif menu == "🟢 Calendario e Convocazioni":
    st.header("🟢 Calendario e Convocazioni")
    
    st.subheader("Le tue Gare:")
    eventi_partita = [ev for ev in st.session_state.db["eventi"] if ev["tipo"] in ["Partita", "Torneo"]]
    
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
                        mod_indirizzo = ""
                with col2:
                    mod_orap = st.text_input("Ora Partita (es. 15:00)", value=ev.get("ora_partita", ""), key=f"mod_op_{ev['id']}")
                    mod_orac = st.text_input("Ora Convocazione (es. 14:00)", value=ev.get("ora_convocazione", ""), key=f"mod_oc_{ev['id']}")
                    mod_nota = st.text_input("Note (es. Campionato)", value=ev.get("nota", ""), key=f"mod_np_{ev['id']}")
                
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
                
                titolo_box = f"🟢 {sq_casa}-{sq_trasf} del {data_f}"
                
                with st.expander(titolo_box):
                    col_mod, col_del = st.columns([1, 1])
                    with col_mod:
                        if st.button("✏️ Modifica Gara", key=f"ed_evp_{ev['id']}"):
                            st.session_state.edit_evento = ev["id"]
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Elimina Gara", key=f"del_evp_{ev['id']}"):
                            st.session_state.db["eventi"] = [e for e in st.session_state.db["eventi"] if e["id"] != ev["id"]]
                            if ev["id"] in st.session_state.db["storico_presenze"]: del st.session_state.db["storico_presenze"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_minutaggio"]: del st.session_state.db["storico_minutaggio"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_titolari"]: del st.session_state.db["storico_titolari"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_moduli"]: del st.session_state.db["storico_moduli"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_numeri"]: del st.session_state.db["storico_numeri"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_gol"]: del st.session_state.db["storico_gol"][ev["id"]]
                            if ev["id"] in st.session_state.db["storico_risultati"]: del st.session_state.db["storico_risultati"][ev["id"]]
                            salvare_dati()
                            st.rerun()
                    
                    st.write("---")
                    
                    appello_evento = st.session_state.db["storico_presenze"].get(ev["id"], {})
                    minutaggio_evento = st.session_state.db["storico_minutaggio"].get(ev["id"], {})
                    gol_evento = st.session_state.db["storico_gol"].get(ev["id"], {})
                    ris_evento = st.session_state.db["storico_risultati"].get(ev["id"], {})
                    titolari_evento = st.session_state.db["storico_titolari"].get(ev["id"], [])
                    modulo_evento = st.session_state.db["storico_moduli"].get(ev["id"], "")
                    numeri_evento = st.session_state.db["storico_numeri"].get(ev["id"], {})
                    
                    ind_campo = ev.get("indirizzo", "Campo di Casa") if ev.get("luogo", "Casa") == "Trasferta" else "Campo di Casa"
                    
                    righe_giocatori = ""
                    convocati_list = []
                    
                    for idx, ragazzo in enumerate(st.session_state.db["ragazzi"]):
                        stato = appello_evento.get(ragazzo, "🟢 Convocato")
                        is_convocato = "Convocato" in stato and "Non" not in stato
                        is_titolare = is_convocato and (ragazzo in titolari_evento)
                        is_panchina = is_convocato and not is_titolare
                        
                        t_mark = "X" if is_titolare else ""
                        p_mark = "X" if is_panchina else ""
                        nc_mark = "X" if not is_convocato else ""
                        
                        numero_maglia = numeri_evento.get(ragazzo, "")
                        numero_display = numero_maglia if numero_maglia else "-"
                        
                        if is_convocato:
                            convocati_list.append(ragazzo)
                            
                        righe_giocatori += f"<tr><td style='border: 1px solid black; padding: 5px;'>{numero_display}</td><td style='border: 1px solid black; padding: 5px; text-align: left;'>{ragazzo}</td><td style='border: 1px solid black; padding: 5px; color: green; font-weight: bold;'>{t_mark}</td><td style='border: 1px solid black; padding: 5px; color: orange; font-weight: bold;'>{p_mark}</td><td style='border: 1px solid black; padding: 5px; color: red; font-weight: bold;'>{nc_mark}</td></tr>"
                    
                    sezione_formazione = ""
                    if modulo_evento or titolari_evento:
                        titolari_validi = [t for t in titolari_evento if t in convocati_list]
                        lista_titolari_html = "<br>".join([f"[{numeri_evento.get(t, '-')}] {t}" for t in titolari_validi]) if titolari_validi else "Nessun titolare selezionato"
                        modulo_txt = modulo_evento if modulo_evento else "Da definire"
                        
                        sezione_formazione = f"""
                        <table style='width: 100%; border-collapse: collapse; text-align: left; border: 2px solid black; border-top: none; background-color: #f9f9f9;'>
                        <tr>
                            <td style='border: 1px solid black; padding: 10px; font-weight: bold; width: 40%; vertical-align: top;'>
                                MODULO TATTICO:<br>
                                <span style='font-size: 24px; color: #1E88E5;'>{modulo_txt}</span>
                            </td>
                            <td style='border: 1px solid black; padding: 10px; vertical-align: top;'>
                                <span style='font-weight: bold;'>FORMAZIONE INIZIALE:</span><br>
                                {lista_titolari_html}
                            </td>
                        </tr>
                        </table>
                        """
                    
                    logo_immagine = get_logo_html()
                    
                    html_distinta = f"""<div style='background-color: white; color: black; padding: 10px; font-family: Arial, sans-serif; max-width: 600px; margin: auto;'>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black;'>
<tr>
<td rowspan='6' style='width: 30%; border: 1px solid black; vertical-align: middle; padding: 10px;'>{logo_immagine}</td>
<td style='border: 1px solid black; color: #4CAF50; font-weight: bold; font-size: 20px; padding: 5px;'>USO UNITED 2014</td>
</tr>
<tr><td style='border: 1px solid black; font-weight: bold; font-size: 16px; padding: 5px;'>MODULO DI GARA UFFICIALE</td></tr>
<tr><td style='border: 1px solid black; padding: 5px;'>PARTITA: {sq_casa}-{sq_trasf}</td></tr>
<tr><td style='border: 1px solid black; padding: 5px;'>DATA: {data_f}</td></tr>
<tr><td style='border: 1px solid black; padding: 5px;'>ORA PARTITA: {ev.get("ora_partita", "___")}</td></tr>
<tr><td style='border: 1px solid black; font-weight: bold; padding: 5px;'>LUOGO: {ind_campo}</td></tr>
</table>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black; border-top: none;'>
<tr style='font-weight: bold; background-color: #f0f0f0;'>
<td style='border: 1px solid black; padding: 5px; width: 10%;'>N°</td>
<td style='border: 1px solid black; padding: 5px; width: 45%;'>Nome e Cognome</td>
<td style='border: 1px solid black; padding: 5px; width: 15%;' title='Titolare'>T</td>
<td style='border: 1px solid black; padding: 5px; width: 15%;' title='Panchina'>P</td>
<td style='border: 1px solid black; padding: 5px; width: 15%;' title='Non Convocato'>NC</td>
</tr>
{righe_giocatori}
</table>
{sezione_formazione}
</div>"""
                    
                    whatsapp_text = f"Ciao a tutti,\n\n"
                    whatsapp_text += f"⚽ *CONVOCAZIONI* ⚽\n"
                    whatsapp_text += f"⚽ *{sq_casa}-{sq_trasf}*\n"
                    whatsapp_text += f"📅 *Data:* {data_f}\n"
                    whatsapp_text += f"⏰ *Ora Partita:* {ev.get('ora_partita', '___')}\n"
                    whatsapp_text += f"📍 *Ora Ritrovo:* {ev.get('ora_convocazione', '___')}\n"
                    whatsapp_text += f"🏟️ *Luogo:* {ind_campo}\n"
                    
                    nota_p = ev.get("nota", "").strip()
                    if nota_p:
                        whatsapp_text += f"📝 *Note:* {nota_p}\n"
                        
                    whatsapp_text += f"\n*ELENCO CONVOCATI:*\n"
                    if convocati_list:
                        for c in convocati_list:
                            whatsapp_text += f"✅ {c}\n"
                    else:
                        whatsapp_text += "*(Nessun convocato ancora selezionato)*\n"
                    whatsapp_text += "\n*Forza USO UNITED!* 💚💙"

                    tab1, tab_formazione, tab2, tab3 = st.tabs(["⚙️ Compila Elenco", "⚽ Formazione", "📄 Modulo Ufficiale", "📱 Messaggio WhatsApp"])
                    
                    with tab1:
                        if not st.session_state.db["ragazzi"]:
                            st.warning("Rosa vuota.")
                        else:
                            # Sezione Risultato Tempi
                            st.write("#### 🏆 Risultato Gara")
                            col_t1, col_t2, col_t3 = st.columns(3)
                            with col_t1:
                                ris_t1 = st.text_input("1° Tempo (es. 1-0)", value=ris_evento.get("t1", ""), key=f"ris_t1_{ev['id']}")
                            with col_t2:
                                ris_t2 = st.text_input("2° Tempo (es. 2-2)", value=ris_evento.get("t2", ""), key=f"ris_t2_{ev['id']}")
                            with col_t3:
                                ris_t3 = st.text_input("3° Tempo (es. 0-1)", value=ris_evento.get("t3", ""), key=f"ris_t3_{ev['id']}")
                                
                            st.write("---")
                            st.write("#### 🏃 Convocati, Minuti e Gol")

                            resoconto_corrente = {}
                            resoconto_minuti = {}
                            resoconto_gol = {}
                            opzioni = ["🟢 Convocato", "🔴 Non Convocato"]
                            
                            for ragazzo in st.session_state.db["ragazzi"]:
                                col_nome, col_stato, col_minuti, col_gol = st.columns([1, 1.2, 0.8, 0.8])
                                with col_nome: st.write(f"**{ragazzo}**")
                                with col_stato:
                                    stato_precedente = appello_evento.get(ragazzo, opzioni[0])
                                    indice_default = opzioni.index(stato_precedente) if stato_precedente in opzioni else 0
                                    stato = st.radio(f"Stato_{ragazzo}_{ev['id']}", opzioni, index=indice_default, horizontal=True, label_visibility="collapsed", key=f"p_{ragazzo}_{ev['id']}")
                                    resoconto_corrente[ragazzo] = stato
                                    
                                with col_minuti:
                                    if "Convocato" in stato and "Non" not in stato:
                                        min_prec = minutaggio_evento.get(ragazzo, 0)
                                        minuti = st.number_input("Min", min_value=0, max_value=150, value=min_prec, step=1, label_visibility="collapsed", key=f"m_{ragazzo}_{ev['id']}", help="Minuti giocati")
                                        resoconto_minuti[ragazzo] = minuti
                                    else:
                                        resoconto_minuti[ragazzo] = 0
                                        st.write("") 

                                with col_gol:
                                    if "Convocato" in stato and "Non" not in stato:
                                        gol_prec = gol_evento.get(ragazzo, 0)
                                        gol = st.number_input("Gol", min_value=0, max_value=50, value=gol_prec, step=1, label_visibility="collapsed", key=f"g_{ragazzo}_{ev['id']}", help="Gol fatti")
                                        resoconto_gol[ragazzo] = gol
                                    else:
                                        resoconto_gol[ragazzo] = 0
                                        st.write("") 
                            
                            st.write("")
                            if st.button("💾 Salva Dati Gara", key=f"btn_salvap_{ev['id']}", type="primary"):
                                st.session_state.db["storico_presenze"][ev["id"]] = resoconto_corrente
                                st.session_state.db["storico_minutaggio"][ev["id"]] = resoconto_minuti
                                st.session_state.db["storico_gol"][ev["id"]] = resoconto_gol
                                st.session_state.db["storico_risultati"][ev["id"]] = {"t1": ris_t1, "t2": ris_t2, "t3": ris_t3}
                                salvare_dati()
                                st.success("Dati archiviati con successo!")
                                st.rerun()

                    with tab_formazione:
                        st.write("#### ⚽ Modulo, Titolari e Numeri di Maglia")
                        if not convocati_list:
                            st.warning("⚠️ Prima devi selezionare i convocati nella scheda 'Compila Elenco'.")
                        else:
                            modulo_salvato = st.session_state.db["storico_moduli"].get(ev["id"], "")
                            nuovo_modulo = st.text_input("Inserisci il numero del modulo (es. 4-4-2, 3-3-2):", value=modulo_salvato, key=f"input_modulo_{ev['id']}")
                            
                            st.write("---")
                            st.write("**Seleziona i titolari e assegna il Numero di Maglia per la distinta:**")
                            
                            titolari_salvati = st.session_state.db["storico_titolari"].get(ev["id"], [])
                            numeri_salvati = st.session_state.db["storico_numeri"].get(ev["id"], {})
                            
                            nuovi_titolari = []
                            nuovi_numeri = {}
                            
                            for c in convocati_list:
                                col_tit, col_num = st.columns([3, 1])
                                with col_tit:
                                    is_tit = st.checkbox(f"Titolare: {c}", value=(c in titolari_salvati), key=f"tit_{c}_{ev['id']}")
                                    if is_tit:
                                        nuovi_titolari.append(c)
                                with col_num:
                                    num_prec = numeri_salvati.get(c, "")
                                    num = st.text_input("N° Maglia", value=num_prec, key=f"num_{c}_{ev['id']}", label_visibility="collapsed", placeholder="N°")
                                    nuovi_numeri[c] = num
                            
                            st.write("")
                            if st.button("💾 Salva Formazione e Numeri", key=f"btn_salva_form_{ev['id']}", type="primary"):
                                st.session_state.db["storico_titolari"][ev["id"]] = nuovi_titolari
                                st.session_state.db["storico_moduli"][ev["id"]] = nuovo_modulo
                                st.session_state.db["storico_numeri"][ev["id"]] = nuovi_numeri
                                salvare_dati()
                                st.success("Formazione, Modulo e Numeri di maglia salvati! Visualizzali nella scheda 'Modulo Ufficiale'.")
                                st.rerun()

                    with tab2:
                        st.markdown(html_distinta, unsafe_allow_html=True)
                        st.write("")
                        st.download_button(
                            label="⬇️ Scarica File del Modulo (.html)",
                            data=html_distinta,
                            file_name=f"Distinta_{sq_casa}_{sq_trasf}.html",
                            mime="text/html",
                            key=f"dl_html_{ev['id']}"
                        )

                    with tab3:
                        st.code(whatsapp_text, language="markdown")
                        st.caption("💡 Clicca sull'iconcina dei foglietti in alto a destra in questo riquadro nero per copiare tutto il testo in un colpo solo e incollarlo su WhatsApp!")

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
            nuovo_indirizzo = ""
    with col2:
        nuova_orap = st.text_input("Ora Partita (es. 15:00)", key="new_orap")
        nuova_orac = st.text_input("Ora Convocazione (es. 14:00)", key="new_orac")
        nuova_nota = st.text_input("Note (es. Campionato)", key="new_notap")
        
    if st.button("Aggiungi Partita a Calendario"):
        if nuovo_avversario.strip() == "":
            st.error("Inserisci il nome dell'avversario!")
        else:
            nuovo_id = str(int(max([int(e["id"]) for e in st.session_state.db["eventi"]], default=0)) + 1)
            st.session_state.db["eventi"].append({
                "id": nuovo_id, "data": str(nuova_data), "tipo": "Partita", 
                "avversario": nuovo_avversario, "luogo": nuovo_luogo, 
                "ora_partita": nuova_orap, "ora_convocazione": nuova_orac, 
                "indirizzo": nuovo_indirizzo, "nota": nuova_nota
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
        for ragazzo in st.session_state.db["ragazzi"]:
            presenti, assenti, infortunati = 0, 0, 0
            for ev_id, appello in storico.items():
                if ev_id in id_allenamenti:
                    stato = appello.get(ragazzo, "")
                    if "Presente" in stato: presenti += 1
                    elif "Assente" in stato: assenti += 1
                    elif "Infortunato" in stato: infortunati += 1
            
            pct = (presenti / totale_allenamenti) * 100 if totale_allenamenti > 0 else 0.00
            tabella_all.append({
                "Giocatore": ragazzo,
                "🟢 Presenze": presenti,
                "🔴 Assenze": assenti,
                "🟡 Infortuni": infortunati,
                "📈 % Presenza": f"{pct:.2f}%"
            })
        st.table(tabella_all)

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
        for ragazzo in st.session_state.db["ragazzi"]:
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
            min_tot = 0
            gol_tot = 0
            for ev_id in id_gare:
                min_tot += st.session_state.db["storico_minutaggio"].get(str(ev_id), {}).get(ragazzo, 0)
                gol_tot += st.session_state.db["storico_gol"].get(str(ev_id), {}).get(ragazzo, 0)

            tabella_gare.append({
                "Giocatore": ragazzo,
                "🟢 Convocati": convocati,
                "👕 Titolare": presenze_titolare,
                "🔴 Non Conv.": non_convocati,
                "📈 % Conv.": f"{pct_conv:.2f}%",
                "⏱️ Min.": min_tot,
                "⚽ Gol Fatti": gol_tot
            })
        st.table(tabella_gare)

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
                    gf = g_casa   # Gol USO UNITED
                    gs = g_trasf  # Gol Avversario
                else:
                    gf = g_trasf  # Gol USO UNITED
                    gs = g_casa   # Gol Avversario
                
                if gf > gs: return 1, 0, gf, gs    # USO vince il tempo
                elif gf == gs: return 1, 1, gf, gs # Pareggio nel tempo (1 punto a testa)
                else: return 0, 1, gf, gs          # Avversario vince il tempo
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
                
            data_f = datetime.datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
            
            sq_casa = "USO UNITED" if luogo_gara == "Casa" else ev.get("avversario", "Avversario")
            sq_trasf = ev.get("avversario", "Avversario") if luogo_gara == "Casa" else "USO UNITED"
            stringa_partita = f"{sq_casa}-{sq_trasf}"
            
            righe_partite += f"<tr><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{data_f}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{stringa_partita}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t1 if t1 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t2 if t2 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px;'>{t3 if t3 else '-'}</td><td style='border: 1px solid rgba(128,128,128,0.3); padding: 8px; font-weight: bold;'>{esito_tabella}</td></tr>"

    riepilogo_html = f"""
    <table style="width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px; color: var(--text-color);">
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
    </table>
    """
    st.markdown(riepilogo_html, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📝 Dettaglio Risultati Partite")
    if not righe_partite:
        st.info("Nessun risultato inserito nelle partite in calendario.")
    else:
        tabella_html = f"""
        <table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; color: var(--text-color);">
            <tr style="background-color: rgba(128,128,128,0.2); font-weight: bold;">
                <td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">Data</td>
                <td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">Partita</td>
                <td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">1° T</td>
                <td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">2° T</td>
                <td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3);">3° T</td>
                <td style="padding: 8px; border: 1px solid rgba(128,128,128,0.3); color: #4CAF50;">Punti Tempi</td>
            </tr>
            {righe_partite}
        </table>
        """
        st.markdown(tabella_html, unsafe_allow_html=True)

# ==========================================
# SCHERMATA 6: GESTIONE ROSA
# ==========================================
elif menu == "🏃 Gestione Rosa":
    st.header("🏃 Anagrafica e Gestione Rosa")
    
    st.subheader("I tuoi giocatori attuali:")
    if not st.session_state.db["ragazzi"]: 
        st.warning("La rosa è vuota!")
    else:
        for i, ragazzo in enumerate(list(st.session_state.db["ragazzi"])):
            if st.session_state.edit_mode == i:
                col_input, col_salva, col_annulla = st.columns([2, 1, 1])
                with col_input:
                    nuovo_nome_mod = st.text_input("Nuovo nome", value=ragazzo, key=f"edit_input_{i}", label_visibility="collapsed")
                with col_salva:
                    if st.button("💾 Salva", key=f"save_btn_{i}", type="primary"):
                        nuovo_nome_mod = nuovo_nome_mod.strip()
                        if nuovo_nome_mod and nuovo_nome_mod != ragazzo and nuovo_nome_mod not in st.session_state.db["ragazzi"]:
                            st.session_state.db["ragazzi"][i] = nuovo_nome_mod
                            for ev_id, appello in st.session_state.db["storico_presenze"].items():
                                if ragazzo in appello: appello[nuovo_nome_mod] = appello.pop(ragazzo)
                            for ev_id, min_dict in st.session_state.db["storico_minutaggio"].items():
                                if ragazzo in min_dict: min_dict[nuovo_nome_mod] = min_dict.pop(ragazzo)
                            for ev_id, titolari_list in st.session_state.db["storico_titolari"].items():
                                if ragazzo in titolari_list: 
                                    titolari_list.remove(ragazzo)
                                    titolari_list.append(nuovo_nome_mod)
                            for ev_id, numeri_dict in st.session_state.db["storico_numeri"].items():
                                if ragazzo in numeri_dict: numeri_dict[nuovo_nome_mod] = numeri_dict.pop(ragazzo)
                            for ev_id, gol_dict in st.session_state.db["storico_gol"].items():
                                if ragazzo in gol_dict: gol_dict[nuovo_nome_mod] = gol_dict.pop(ragazzo)
                        st.session_state.edit_mode = None
                        salvare_dati()
                        st.rerun()
                with col_annulla:
                    if st.button("❌ Annulla", key=f"cancel_btn_{i}"):
                        st.session_state.edit_mode = None
                        st.rerun()
            else:
                col_nome, col_modifica, col_cancella = st.columns([2.5, 1, 1])
                with col_nome: 
                    min_tot_anagrafica = sum(st.session_state.db["storico_minutaggio"].get(ev_id, {}).get(ragazzo, 0) for ev_id in st.session_state.db["storico_minutaggio"])
                    st.write(f"• **{ragazzo}** *(⏱️ {min_tot_anagrafica}' totali)*")
                with col_modifica:
                    if st.button("✏️ Modifica", key=f"edit_btn_{i}"):
                        st.session_state.edit_mode = i
                        st.rerun()
                with col_cancella:
                    if st.button("🗑️ Elimina", key=f"del_btn_{i}"):
                        st.session_state.db["ragazzi"].remove(ragazzo)
                        salvare_dati()
                        st.rerun()
                    
    st.write("---")
    st.subheader("➕ Aggiungi un nuovo giocatore")
    nuovo_nome_ins = st.text_input("Nome e Cognome del ragazzo:", key="nuovo_ins_input")
    if st.button("Inserisci in Squadra"):
        if nuovo_nome_ins.strip() != "" and nuovo_nome_ins.strip() not in st.session_state.db["ragazzi"]:
            st.session_state.db["ragazzi"].append(nuovo_nome_ins.strip())
            salvare_dati()
            st.success(f"⚽ {nuovo_nome_ins.strip()} aggiunto alla rosa!")
            st.rerun()