# AppLu · percorso guidato di apprendimento locale

Prototipo desktop Windows per svolgere round di raccolta strutturata prima di scrivere le regole definitive degli ordinativi.

## Cosa fa

- Guida Lucrezia attraverso una tipologia alla volta e chiede un solo esemplare per selezione.
- Resta sul tipo corrente finché tutte le variabili e varianti non sono state confermate. Un documento indisponibile sospende il percorso; non si può saltare.
- Consente più esemplari dello stesso tipo, ognuno etichettato con la variante/caso rappresentato.
- Seleziona localmente PDF testuali, DOCX, TXT, MD o CSV.
- Mostra il testo e occorrenze letterali di email, protocollo, importi, date e intervalli orari, con pagina o sezione di origine.
- Propone campi attesi per ciascuna tipologia. Ogni campo può essere marcato come presente e chiaro, ambiguo, non trovato, illeggibile, non previsto o ancora da valutare.
- Permette di collegare un’occorrenza al campo selezionato, correggere il valore, aggiungere campi e tipizzare ogni dubbio. Ogni mappatura conserva fonte, pagina/sezione, contesto, valore revisionato, stato e domanda di chiarimento.
- Salva round in JSONL sul profilo dell’utente Windows e consente di esportarli in JSON.

## Cosa non fa

Non addestra un modello, non modifica da sola le regole, non deduce che un’occorrenza appartenga a un campo, non genera ordinativi e non decide quale documento sia corretto in presenza di duplicati. Le estrazioni sono candidati da verificare. Il passaggio al documento successivo è bloccato finché i campi restano da verificare, ambigui, non rilevati o illeggibili. PDF scansionati (senza testo selezionabile), DOC e immagini non sono supportati in questa fase.

## Privacy e percorso dati

L’analisi e il log restano locali; nessun contenuto viene inviato a servizi esterni. Per rendere il dataset utile alla definizione delle regole, il log dettagliato è attivo per impostazione predefinita e conserva valori candidati, brevi contesti, provenienza e mappature revisionate. Il testo integrale e i file originali non vengono copiati. È disponibile l’opzione per omettere valori, contesti e mappature testuali quando necessario. Il file JSONL può contenere dati personali e va conservato e condiviso con le cautele aziendali previste.

Percorso Windows: `%LOCALAPPDATA%\AppLu\Apprendimento\learning-log.jsonl`.
I progressi intermedi vengono salvati automaticamente in `session-progress.json` nello stesso percorso e riaperti all’avvio. Il file conserva riferimenti ai documenti e le annotazioni di lavoro, non il testo integrale.

## Avvio di sviluppo

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_app.py
```

## Pacchetto portable

Su Windows, senza installazione amministrativa:

```powershell
.\build_windows.ps1
```

Produce `AppLu-Apprendimento-portable.zip`; estrarre la cartella ed avviare `AppLu-Apprendimento.exe`. Il log rimane nel profilo utente scrivibile. Non installa servizi o driver.

GitHub Actions compila anche un artifact Windows su push del branch `codex/local-learning-app` o manualmente da Actions. È un artifact di sviluppo, non un installer firmato.

Le istruzioni complete per Lucrezia sono incluse in [`LEGGIMI_PRIMA.txt`](LEGGIMI_PRIMA.txt) e copiate dentro lo ZIP portable.

