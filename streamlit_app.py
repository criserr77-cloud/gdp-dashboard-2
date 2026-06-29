import streamlit as st
import datetime
import json
import os
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAZIONE GOOGLE SHEETS ---
ID_FOGLIO_GOOGLE = "1PCmJ9tgv-ohAIuc3CmwP4BOZLg68qSLmkLYwSQ7pSsc" 

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

# --- CSS PER MENU SMARTPHONE E DESIGN ---
st.markdown("""
    <style>
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
        padding: 16px 20px !important;
        margin-bottom: 12px !important;
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.2);
        cursor: pointer;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: var(--text-color) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:active {
        opacity: 0.7;
    }
    </style>
""", unsafe_allow_html=True)

def get_logo_html():
    for ext in ["png", "jpg", "jpeg"]:
        if os.path.exists(f"stemma.{ext}"):
            with open(f"stemma.{ext}", "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                return f"<img src='data:image/{ext};base64,{encoded}' style='max-width: 100px; max-height: 120px; object-fit: contain;'>"
    return "<div style='font-size: 50px;'>🛡️</div>"

# Inizializzazione Session State
if "db" not in st.session_state: 
    st.session_state.db = caricare_dati()
    if "anagrafica_ruolo" not in st.session_state.db: st.session_state.db["anagrafica_ruolo"] = {}
    if "anagrafica_nascita" not in st.session_state.db: st.session_state.db["anagrafica_nascita"] = {}
    if "storico_capitano" not in st.session_state.db: st.session_state.db["storico_capitano"] = {}
    if "storico_vicecapitano" not in st.session_state.db: st.session_state.db["storico_vicecapitano"] = {}

if "edit_mode" not in st.session_state: st.session_state.edit_mode = None
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
                        mod_indirizzo = ""
                with col2:
                    mod_orap = st.text_input("Ora Partita (es. 15:00)", value=ev.get("ora_partita", ""), key=f"mod_op_{ev['id']}")
                    mod_orac = st.text_input("Ora Convocazione (es. 14:00)", value=ev.get("ora_convocazione", ""), key=f"mod_oc_{ev['id']}")
                    
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
                            if ev["id"] in st.session_state.db["storico_minutaggio"]: del st.session_state.db["storico_minutaggio"][ev["id"]]
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
                    minutaggio_evento = st.session_state.db["storico_minutaggio"].get(ev["id"], {})
                    gol_evento = st.session_state.db["storico_gol"].get(ev["id"], {})
                    ris_evento = st.session_state.db["storico_risultati"].get(ev["id"], {})
                    titolari_evento = st.session_state.db["storico_titolari"].get(ev["id"], [])
                    numeri_evento = st.session_state.db["storico_numeri"].get(ev["id"], {})
                    capitano_evento = st.session_state.db.get("storico_capitano", {}).get(ev["id"], "")
                    vice_evento = st.session_state.db.get("storico_vicecapitano", {}).get(ev["id"], "")
                    
                    ind_campo = ev.get("indirizzo", "Campo di Casa") if ev.get("luogo", "Casa") == "Trasferta" else "Campo di Casa"
                    tipo_partita = ev.get("nota", "Campionato")
                    note_agg = ev.get("note_aggiuntive", "")
                    
                    righe_giocatori = ""
                    convocati_list = []
                    riga_num = 1
                    
                    for idx, ragazzo in enumerate(st.session_state.db["ragazzi"]):
                        stato = appello_evento.get(ragazzo, "🟢 Convocato")
                        is_convocato = "Convocato" in stato and "Non" not in stato
                        
                        c_mark = "X" if is_convocato else ""
                        nc_mark = "X" if not is_convocato else ""
                        
                        if is_convocato:
                            convocati_list.append(ragazzo)
                            
                        righe_giocatori += f"<tr><td style='border: 1px solid black; padding: 5px;'>{riga_num}</td><td style='border: 1px solid black; padding: 5px; text-align: left;'>{ragazzo}</td><td style='border: 1px solid black; padding: 5px; color: green; font-weight: bold;'>{c_mark}</td><td style='border: 1px solid black; padding: 5px; color: red; font-weight: bold;'>{nc_mark}</td></tr>"
                        riga_num += 1
                    
                    righe_formazione = ""
                    if titolari_evento:
                        titolari_validi = [t for t in titolari_evento if t in convocati_list]
                        for t in titolari_validi:
                            num = numeri_evento.get(t, '-')
                            parts = t.split(" ", 1)
                            nome_t = parts[0]
                            cognome_t = parts[1] if len(parts) > 1 else ""
                            
                            badge = ""
                            if t == capitano_evento: badge = " <span style='color: blue; font-weight: bold;'>(C)</span>"
                            elif t == vice_evento: badge = " <span style='color: green; font-weight: bold;'>(VC)</span>"
                            
                            righe_formazione += f"<tr><td style='border: 1px solid black; padding: 5px; font-weight: bold; width: 10%;'>{num}</td><td style='border: 1px solid black; padding: 5px; text-align: left; width: 45%;'>{nome_t}</td><td style='border: 1px solid black; padding: 5px; text-align: left; width: 45%;'>{cognome_t}{badge}</td></tr>"
                    else:
                        righe_formazione = "<tr><td colspan='3' style='border: 1px solid black; padding: 5px; font-style: italic;'>Nessun titolare selezionato</td></tr>"
                    
                    logo_immagine = get_logo_html()
                    
                    # HTML Convocazioni
                    html_distinta = f"""<div style='background-color: white; color: black; padding: 10px; font-family: Arial, sans-serif; max-width: 600px; margin: auto;'>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black;'>
<tr>
<td rowspan='6' style='width: 30%; border: 1px solid black; vertical-align: middle; padding: 10px;'>{logo_immagine}</td>
<td style='border: 1px solid black; font-weight: bold; font-size: 16px; padding: 5px; background-color: #f0f0f0;'>CONVOCAZIONI</td>
</tr>
<tr><td style='border: 1px solid black; padding: 5px;'>PARTITA: {sq_casa} - {sq_trasf}</td></tr>
<tr><td style='border: 1px solid black; padding: 5px; font-weight: bold;'>TIPO PARTITA: {tipo_partita}</td></tr>
<tr><td style='border: 1px solid black; padding: 5px;'>DATA: {data_f}</td></tr>
<tr><td style='border: 1px solid black; padding: 5px;'>ORA PARTITA: {ev.get("ora_partita", "___")} - ORA RITROVO: {ev.get("ora_convocazione", "___")}</td></tr>
<tr><td style='border: 1px solid black; font-weight: bold; padding: 5px; background-color: #f9f9f9;'>LUOGO: {ind_campo}</td></tr>
</table>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black; border-top: none;'>
<tr style='font-weight: bold; background-color: #f0f0f0;'>
<td style='border: 1px solid black; padding: 5px; width: 10%;'>N°</td>
<td style='border: 1px solid black; padding: 5px; width: 50%;'>Nome e Cognome</td>
<td style='border: 1px solid black; padding: 5px; width: 20%;' title='Convocato'>C</td>
<td style='border: 1px solid black; padding: 5px; width: 20%;' title='Non Convocato'>NC</td>
</tr>
{righe_giocatori}
</table>
</div>"""

                    # HTML Formazione (senza ora e luogo, con NOME e COGNOME divisi)
                    html_formazione = f"""<div style='background-color: white; color: black; padding: 10px; font-family: Arial, sans-serif; max-width: 600px; margin: auto;'>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black;'>
<tr>
<td rowspan='4' style='width: 30%; border: 1px solid black; vertical-align: middle; padding: 10px;'>{logo_immagine}</td>
<td style='border: 1px solid black; font-weight: bold; font-size: 16px; padding: 5px; background-color: #f0f0f0;'>FORMAZIONE UFFICIALE</td>
</tr>
<tr><td style='border: 1px solid black; padding: 5px;'>PARTITA: {sq_casa} - {sq_trasf}</td></tr>
<tr><td style='border: 1px solid black; padding: 5px; font-weight: bold;'>TIPO PARTITA: {tipo_partita}</td></tr>
<tr><td style='border: 1px solid black; padding: 5px;'>DATA: {data_f}</td></tr>
</table>
<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black; border-top: none;'>
<tr style='font-weight: bold; background-color: #f0f0f0;'>
<td style='border: 1px solid black; padding: 5px; width: 10%;'>N°</td>
<td style='border: 1px solid black; padding: 5px; width: 45%;'>Nome</td>
<td style='border: 1px solid black; padding: 5px; width: 45%;'>Cognome</td>
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
                        
                    whatsapp_text += f"\n*ELENCO CONVOCATI:*\n"
                    if convocati_list:
                        for c in convocati_list:
                            whatsapp_text += f"✅ {c}\n"
                    else:
                        whatsapp_text += "*(Nessun convocato ancora selezionato)*\n"
                    whatsapp_text += "\n*Forza USO UNITED!* 💙💚"

                    tab1, tab_formazione, tab2, tab3 = st.tabs(["⚙️ Compila Elenco", "⚽ Formazione e Dati Partita", "📄 Convocazioni Ufficiali", "📱 Messaggio WhatsApp"])
                    
                    with tab1:
                        if not st.session_state.db["ragazzi"]:
                            st.warning("Rosa vuota.")
                        else:
                            st.write("#### 🏃 Seleziona Convocati")
                            resoconto_corrente = {}
                            opzioni = ["🟢 Convocato", "🔴 Non Convocato"]
                            
                            for ragazzo in st.session_state.db["ragazzi"]:
                                col_nome, col_stato = st.columns([1, 2])
                                with col_nome: st.write(f"**{ragazzo}**")
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
                            
                            nuovi_titolari = []
                            nuovi_numeri = {}
                            resoconto_minuti = {}
                            resoconto_gol = {}
                            
                            # Intestazioni delle colonne Formazione
                            c_n, c_nome, c_cognome, c_tit, c_min, c_g = st.columns([1, 1.5, 1.5, 1, 1, 1])
                            c_n.markdown("**N°**")
                            c_nome.markdown("**Nome**")
                            c_cognome.markdown("**Cognome**")
                            c_tit.markdown("**Tit.**")
                            c_min.markdown("**Min.**")
                            c_g.markdown("**Gol**")
                            
                            for c in convocati_list:
                                parts = c.split(" ", 1)
                                nome_str = parts[0]
                                cogn_str = parts[1] if len(parts) > 1 else ""
                                
                                col_num, col_nome, col_cognome, col_tit, col_min, col_g = st.columns([1, 1.5, 1.5, 1, 1, 1])
                                with col_num:
                                    num_prec = numeri_salvati.get(c, "")
                                    num = st.text_input("N°", value=num_prec, key=f"num_{c}_{ev['id']}", label_visibility="collapsed")
                                    nuovi_numeri[c] = num
                                with col_nome:
                                    st.write(nome_str)
                                with col_cognome:
                                    st.write(cogn_str)
                                with col_tit:
                                    is_tit = st.checkbox("Tit", value=(c in titolari_salvati), key=f"tit_{c}_{ev['id']}", label_visibility="collapsed")
                                    if is_tit: nuovi_titolari.append(c)
                                with col_min:
                                    min_prec = minutaggio_evento.get(c, 0)
                                    minuti = st.number_input("Min", min_value=0, max_value=150, value=min_prec, step=1, label_visibility="collapsed", key=f"m_{c}_{ev['id']}")
                                    resoconto_minuti[c] = minuti
                                with col_g:
                                    gol_prec = gol_evento.get(c, 0)
                                    gol = st.number_input("Gol", min_value=0, max_value=50, value=gol_prec, step=1, label_visibility="collapsed", key=f"g_{c}_{ev['id']}")
                                    resoconto_gol[c] = gol
                            
                            st.write("---")
                            st.write("#### © Assegna Fasce")
                            opzioni_fasce = ["Nessuno"] + convocati_list
                            idx_cap = opzioni_fasce.index(capitano_evento) if capitano_evento in opzioni_fasce else 0
                            idx_vice = opzioni_fasce.index(vice_evento) if vice_evento in opzioni_fasce else 0
                            
                            col_cap, col_vice = st.columns(2)
                            with col_cap:
                                input_capitano = st.selectbox("Capitano (C)", opzioni_fasce, index=idx_cap, key=f"cap_{ev['id']}")
                            with col_vice:
                                input_vice = st.selectbox("Vice-Capitano (VC)", opzioni_fasce, index=idx_vice, key=f"vice_{ev['id']}")
                            
                            st.write("")
                            if st.button("💾 Salva Formazione e Dati", key=f"btn_salva_form_{ev['id']}", type="primary"):
                                st.session_state.db["storico_titolari"][ev["id"]] = nuovi_titolari
                                st.session_state.db["storico_numeri"][ev["id"]] = nuovi_numeri
                                st.session_state.db["storico_risultati"][ev["id"]] = {"t1": ris_t1, "t2": ris_t2, "t3": ris_t3}
                                st.session_state.db["storico_minutaggio"][ev["id"]] = resoconto_minuti
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
                        st.download_button(
                            label="⬇️ Scarica Convocazioni (.html)",
                            data=html_distinta,
                            file_name=f"Convocazioni_{sq_casa}_{sq_trasf}.html",
                            mime="text/html",
                            key=f"dl_html_conv_{ev['id']}"
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
        
        if tabella_all:
            html_all = "<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Allenamenti</h2><table border='1' style='border-collapse: collapse; text-align: center; width:100%;'><tr><th style='padding:8px; background-color: #f0f0f0;'>Giocatore</th><th style='padding:8px; background-color: #f0f0f0;'>🟢 Presenze</th><th style='padding:8px; background-color: #f0f0f0;'>🔴 Assenze</th><th style='padding:8px; background-color: #f0f0f0;'>🟡 Infortuni</th><th style='padding:8px; background-color: #f0f0f0;'>📈 % Presenza</th></tr>"
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
                "🟢 Convocato": convocati,
                "🔴 Non Conv.": non_convocati,
                "👕 Titolare": presenze_titolare,
                "📈 % Conv.": f"{pct_conv:.2f}%",
                "⏱️ Min.": min_tot,
                "⚽ Gol Fatti": gol_tot
            })
        st.table(tabella_gare)
        
        if tabella_gare:
            html_giocatori = "<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Giocatori</h2><table border='1' style='border-collapse: collapse; text-align: center; width:100%;'><tr><th style='padding:8px; background-color: #f0f0f0;'>Giocatore</th><th style='padding:8px; background-color: #f0f0f0;'>🟢 Convocato</th><th style='padding:8px; background-color: #f0f0f0;'>🔴 Non Conv.</th><th style='padding:8px; background-color: #f0f0f0;'>👕 Titolare</th><th style='padding:8px; background-color: #f0f0f0;'>📈 % Conv.</th><th style='padding:8px; background-color: #f0f0f0;'>⏱️ Min.</th><th style='padding:8px; background-color: #f0f0f0;'>⚽ Gol Fatti</th></tr>"
            for row in tabella_gare:
                html_giocatori += f"<tr><td style='padding:8px;'>{row['Giocatore']}</td><td style='padding:8px;'>{row['🟢 Convocato']}</td><td style='padding:8px;'>{row['🔴 Non Conv.']}</td><td style='padding:8px;'>{row['👕 Titolare']}</td><td style='padding:8px;'>{row['📈 % Conv.']}</td><td style='padding:8px;'>{row['⏱️ Min.']}</td><td style='padding:8px;'>{row['⚽ Gol Fatti']}</td></tr>"
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
            html_squadra = f"<html><head><meta charset='UTF-8'></head><body style='font-family: Arial, sans-serif; color: black;'><h2>Statistiche Squadra</h2>{riepilogo_html}<h2>Dettaglio Partite</h2>{tabella_html}</body></html>"
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
        st.warning("La rosa è vuota!")
    else:
        st.markdown("### 📋 Elenco Giocatori")
        
        col_n, col_r, col_d, col_azioni = st.columns([2, 1.5, 1.5, 2])
        col_n.markdown("**Nome e Cognome**")
        col_r.markdown("**Ruolo**")
        col_d.markdown("**Data Nascita**")
        col_azioni.markdown("**Azioni**")
        st.write("---")
        
        for i, ragazzo in enumerate(list(st.session_state.db["ragazzi"])):
            if st.session_state.edit_mode == i:
                st.markdown(f"**✏️ Stai modificando: {ragazzo}**")
                c1, c2, c3 = st.columns([1.5, 1.5, 1.5])
                with c1: 
                    nuovo_nome_mod = st.text_input("Nome", value=ragazzo, key=f"edit_input_{i}")
                
                ruolo_prec = st.session_state.db.get("anagrafica_ruolo", {}).get(ragazzo, "Non definito")
                ruoli_disp = ["Portiere", "Difensore", "Centrocampista", "Attaccante", "Non definito"]
                idx_r = ruoli_disp.index(ruolo_prec) if ruolo_prec in ruoli_disp else 4
                with c2: 
                    nuovo_ruolo_mod = st.selectbox("Ruolo", ruoli_disp, index=idx_r, key=f"edit_r_{i}")
                
                nascita_prec = st.session_state.db.get("anagrafica_nascita", {}).get(ragazzo, "")
                if nascita_prec:
                    try: d_obj = datetime.datetime.strptime(nascita_prec, "%Y-%m-%d").date()
                    except: d_obj = datetime.date(2014, 1, 1)
                else:
                    d_obj = datetime.date(2014, 1, 1)
                with c3: 
                    nuova_nascita_mod = st.date_input("Nascita", d_obj, key=f"edit_d_{i}")
                
                col_s, col_a = st.columns(2)
                with col_s:
                    if st.button("💾 Salva Modifiche", key=f"save_btn_{i}", type="primary"):
                        nuovo_nome_mod = nuovo_nome_mod.strip()
                        nome_finale = ragazzo
                        if nuovo_nome_mod and nuovo_nome_mod != ragazzo and nuovo_nome_mod not in st.session_state.db["ragazzi"]:
                            st.session_state.db["ragazzi"][i] = nuovo_nome_mod
                            nome_finale = nuovo_nome_mod
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
                            
                            if ragazzo in st.session_state.db.get("anagrafica_ruolo", {}):
                                st.session_state.db["anagrafica_ruolo"].pop(ragazzo)
                            if ragazzo in st.session_state.db.get("anagrafica_nascita", {}):
                                st.session_state.db["anagrafica_nascita"].pop(ragazzo)
                        
                        st.session_state.db.setdefault("anagrafica_ruolo", {})[nome_finale] = nuovo_ruolo_mod
                        st.session_state.db.setdefault("anagrafica_nascita", {})[nome_finale] = str(nuova_nascita_mod)
                        
                        st.session_state.edit_mode = None
                        salvare_dati()
                        st.rerun()
                with col_a:
                    if st.button("❌ Annulla", key=f"cancel_btn_{i}"):
                        st.session_state.edit_mode = None
                        st.rerun()
                st.write("---")
            else:
                ruolo_val = st.session_state.db.get("anagrafica_ruolo", {}).get(ragazzo, "Non definito")
                nascita_val = st.session_state.db.get("anagrafica_nascita", {}).get(ragazzo, "-")
                if nascita_val != "-":
                    try:
                        nascita_val = datetime.datetime.strptime(nascita_val, "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        pass
                
                c_n, c_r, c_d, c_mod, c_del = st.columns([2, 1.5, 1.5, 1, 1])
                c_n.write(f"**{ragazzo}**")
                c_r.write(ruolo_val)
                c_d.write(nascita_val)
                with c_mod:
                    if st.button("✏️ Modifica", key=f"edit_btn_{i}"):
                        st.session_state.edit_mode = i
                        st.rerun()
                with c_del:
                    if st.button("🗑️ Elimina", key=f"del_btn_{i}"):
                        st.session_state.db["ragazzi"].remove(ragazzo)
                        if ragazzo in st.session_state.db.get("anagrafica_ruolo", {}): del st.session_state.db["anagrafica_ruolo"][ragazzo]
                        if ragazzo in st.session_state.db.get("anagrafica_nascita", {}): del st.session_state.db["anagrafica_nascita"][ragazzo]
                        salvare_dati()
                        st.rerun()
                st.write("---")
                    
    st.subheader("➕ Aggiungi un nuovo giocatore")
    col_n, col_r, col_d = st.columns(3)
    with col_n: nuovo_nome_ins = st.text_input("Nome e Cognome:", key="nuovo_ins_input")
    with col_r: nuovo_ruolo_ins = st.selectbox("Ruolo", ["Portiere", "Difensore", "Centrocampista", "Attaccante", "Non definito"])
    with col_d: nuova_nascita_ins = st.date_input("Data di Nascita", datetime.date(2014, 1, 1))
    
    if st.button("Inserisci in Squadra"):
        if nuovo_nome_ins.strip() != "" and nuovo_nome_ins.strip() not in st.session_state.db["ragazzi"]:
            st.session_state.db["ragazzi"].append(nuovo_nome_ins.strip())
            st.session_state.db.setdefault("anagrafica_ruolo", {})[nuovo_nome_ins.strip()] = nuovo_ruolo_ins
            st.session_state.db.setdefault("anagrafica_nascita", {})[nuovo_nome_ins.strip()] = str(nuova_nascita_ins)
            salvare_dati()
            st.success(f"⚽ {nuovo_nome_ins.strip()} aggiunto alla rosa!")
            st.rerun()