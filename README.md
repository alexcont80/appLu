# Ordinativi docenti · prototipo web

Prototipo dimostrativo statico per la fase iniziale del progetto. La versione attuale presenta il flusso, le fonti dei dati, gli stati di verifica e le decisioni manuali. Non elabora documenti e non produce DOCX o PDF.

## Avvio

Aprire `index.html` in un browser. Per una preview locale:

```sh
python -m http.server 8000
```

poi visitare `http://localhost:8000` dalla cartella `appLu`.

## Limiti intenzionali

- Il selettore cartella dimostra l’interazione nel browser; i nomi selezionati non vengono caricati né letti.
- Il caso visualizzato usa dati fittizi e non contiene dati personali o tariffe reali.
- La scelta BLSD è interattiva: solo “Sì” determina `PAC Formest`; “No” resta da completare.
- La generazione dei documenti è disattivata fino alla consegna dei modelli e delle regole mancanti.
- La futura app Windows dovrà leggere le cartelle locali/rete con le autorizzazioni Windows dell’utente, senza credenziali memorizzate.

## Struttura

- `index.html`: schermata dimostrativa e contenuti informativi.
- `styles.css`: layout responsive.
- `app.js`: stato dimostrativo e interazioni locali.
- `docs/requirements-discovery.md`: riscontro documentale e requisiti ancora aperti.
- `learning_app/`: prima applicazione desktop portable per etichettare documenti, verificare campi e produrre round di apprendimento locali.
- `run_app.py`: avvio dell’app desktop in modalità sviluppo.

## Prossime fasi

1. Usare il banco di apprendimento locale su campioni autorizzati e raccogliere più round strutturati.
2. Analizzare i log per fissare le regole mancanti riportate in `docs/requirements-discovery.md`.
3. Ricevere i due modelli Word degli ordinativi, i PDF dei piani e campioni rappresentativi.
4. Implementare i moduli definitivi per regole, generazione DOCX, revisione e conversione PDF.

Il percorso desktop è guidato e sequenziale: un tipo non si chiude finché campi e varianti non risultano compresi. Per i dettagli vedere [`learning_app/README.md`](learning_app/README.md) e la guida inclusa [`learning_app/LEGGIMI_PRIMA.txt`](learning_app/LEGGIMI_PRIMA.txt).
