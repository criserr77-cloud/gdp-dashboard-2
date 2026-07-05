import React, { useState } from 'react';
import { Calendar, Clock, MapPin, Users, Info } from 'lucide-react';

const matchTimes: string[] = [];
for (let h = 9; h <= 18; h++) {
  matchTimes.push(`${h.toString().padStart(2, '0')}:00`);
  if (h !== 18) {
    matchTimes.push(`${h.toString().padStart(2, '0')}:30`);
  }
}

const calculateMeetingTime = (time: string) => {
  if (!time) return "";
  const [h, m] = time.split(':').map(Number);
  const meetingH = h - 1;
  return `${meetingH.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
};

const homeLocations = [
  "Campo Prealpino Santa Giulia Via del brolo 7",
  "Campo Coltrini Comunale",
  "Parco Urbano Bovezzo"
];

export default function App() {
  const [matchTime, setMatchTime] = useState<string>("09:00");
  const [opponent, setOpponent] = useState<string>("");
  const [matchType, setMatchType] = useState<"casa" | "trasferta">("casa");
  const [location, setLocation] = useState<string>(homeLocations[0]);

  const meetingTime = calculateMeetingTime(matchTime);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100">
        
        <div className="bg-blue-600 p-6 text-white text-center">
          <h1 className="text-2xl font-semibold tracking-tight">Programma Partita</h1>
          <p className="text-blue-100 mt-1 text-sm">Imposta i dettagli e gli orari del match</p>
        </div>

        <div className="p-6 space-y-6">
          
          {/* Tipo Partita */}
          <div className="flex bg-slate-100 p-1 rounded-lg">
            <button
              onClick={() => {
                setMatchType("casa");
                if (!homeLocations.includes(location)) {
                  setLocation(homeLocations[0]);
                }
              }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                matchType === "casa" 
                  ? "bg-white text-blue-600 shadow-sm" 
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              In Casa
            </button>
            <button
              onClick={() => {
                setMatchType("trasferta");
                if (homeLocations.includes(location)) {
                  setLocation("");
                }
              }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                matchType === "trasferta" 
                  ? "bg-white text-blue-600 shadow-sm" 
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              In Trasferta
            </button>
          </div>

          {/* Avversario */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
              <Users className="w-4 h-4 text-slate-400" />
              Squadra Avversaria
            </label>
            <input 
              type="text" 
              value={opponent}
              onChange={(e) => setOpponent(e.target.value)}
              placeholder="Es. Real Madrid"
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-900"
            />
          </div>

          {/* Luogo */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-slate-400" />
              Luogo della Partita
            </label>
            {matchType === "casa" ? (
              <div className="relative">
                <select
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full appearance-none px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-slate-900"
                >
                  {homeLocations.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                  <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>
            ) : (
              <input 
                type="text" 
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Es. Stadio Olimpico"
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-slate-900"
              />
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            {/* Ora Partita */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <Clock className="w-4 h-4 text-slate-400" />
                Ora Partita
              </label>
              <div className="relative">
                <select
                  value={matchTime}
                  onChange={(e) => setMatchTime(e.target.value)}
                  className="w-full appearance-none px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-slate-900 font-medium"
                >
                  {matchTimes.map((time) => (
                    <option key={time} value={time}>
                      {time}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                  <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>
            </div>

            {/* Ora Ritrovo */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                Ora Ritrovo
              </label>
              <div className="w-full px-4 py-2 border border-slate-100 bg-slate-50 rounded-lg text-slate-500 font-medium flex items-center h-[42px] cursor-not-allowed">
                {meetingTime}
              </div>
            </div>
          </div>
          
          <div className="bg-blue-50 rounded-lg p-3 flex items-start gap-3 mt-2 border border-blue-100">
             <Info className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
             <p className="text-sm text-blue-800">
               L'orario di ritrovo viene calcolato automaticamente <strong>un'ora prima</strong> dell'inizio della partita.
             </p>
          </div>

        </div>

        <div className="p-6 bg-slate-50 border-t border-slate-100">
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors shadow-sm">
            Salva Partita
          </button>
        </div>

      </div>
    </div>
  );
}st.session_state.db["storico_titolari"][ev["id"]] = nuovi_titolari
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
            opzioni_casa = ["Campo Prealpino Santa Giulia Via del brolo 7", "Campo Coltrini Comunale", "Parco Urbano Bovezzo"]
            nuovo_indirizzo = st.selectbox("Indirizzo del campo", opzioni_casa, key="new_indirizzo")
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