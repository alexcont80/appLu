# Analisi iniziale dei requisiti

## Materiale individuato in Gmail

È stato esaminato il messaggio inoltrato “Proposta incarico Corso ARCS 26120 Corso di formazione manageriale per direttori Edizione 16” (16 settembre 2026), originato da Isabella Selleri, con tre allegati Word:

- `Accettazione incarico.docx`
- `Dichiarazione conflitto d'interessi docente.docx`
- `Dichiarazione docente esterno.docx`

Il messaggio contiene un esempio di proposta di docenza e specifica una tariffa oraria e il rimborso spese documentato. I dati del caso reale e gli importi non sono stati inseriti nel prototipo web.

## Cosa aggiunge la modulistica

1. **Accettazione incarico** distingue personale dipendente ARCS e professionisti esterni. Prevede attività gratuita, attività retribuita in orario di servizio o fuori orario per il personale ARCS, e compenso orario o forfettario per gli esterni. La richiesta di rimborso spese è separata e richiede giustificativi secondo i termini indicati nel modulo.
2. **Dichiarazione docente esterno** raccoglie la modalità di retribuzione dichiarata dal docente (dipendente pubblico, libero professionista o collaborazione occasionale, con ulteriori casi) e le coordinate di accredito.
3. **Dichiarazione conflitto d’interessi** è un modulo dichiarativo da compilare e sottoscrivere; non individua il conto di imputazione o il centro di costo dell’ordinativo.

Questi allegati sono moduli collegati all’incarico, ma **non** sono i due modelli Word dell’ordinativo richiesti per la generazione.

## Punto da chiarire prima di calcolare

La classificazione interno/esterno tramite dominio email sceglie il modello, ma da sola non determina la tariffa per un dipendente ARCS: l’accettazione distingue anche l’orario di servizio e fuori servizio. La tariffa applicabile dovrà provenire da una fonte certa e coerente (lettera o altra regola formalizzata). Il programma non deve dedurla dal solo dominio.

La modulistica esterna raccoglie inoltre la modalità fiscale/retributiva dichiarata e il rimborso spese è distinto dal compenso. Non è stato esteso il calcolo dell’ordinativo a questi casi, perché la specifica fornita definisce solo compenso orario/forfettario e non la compilazione di rimborsi o oneri fiscali.

## Materiali ancora necessari

- I due modelli Word dell’ordinativo, con indicazione dei campi da compilare.
- Lettere di incarico anonimizzate rappresentative di forfait, tariffa oraria, docente interno ed esterno.
- Programma Edizione e regola precisa per associare l’intervento al docente.
- CV anonimizzati, regola di classificazione dei titoli e codici contabili.
- Piani formativi aziendale/regionale e regola esatta di confronto dei titoli.
- Percorsi aziendali, convenzioni dei nomi file, gestione duplicati e nomi di output/alert.
- Regole su forfait giornaliero, dipendenti in orario/fuori orario, rimborsi, oneri e priorità quando il corso compare in più fonti.

## Perimetro del prototipo

Il prototipo web è una demo di interfaccia con dati fittizi. Non include connessione Gmail, upload/lettura di documenti, OCR, regole inferenziali, generazione Word, conversione PDF o conservazione di file. L’elaborazione effettiva è destinata alla successiva app Windows portable, dopo la chiusura dei punti sopra.
