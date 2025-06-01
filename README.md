# PyCryptoDesk 📊💰

Benvenuto in PyCryptoDesk! 👋 Una semplice applicazione desktop GUI 💻 sviluppata in Python per monitorare criptovalute, visualizzare dati di mercato, grafici storici 📈 e gestire una watchlist personalizzata.

## Descrizione 📝

PyCryptoDesk offre un'interfaccia utente intuitiva basata su schede per accedere a diverse funzionalità legate al mondo delle criptovalute. Utilizza l'API di CoinGecko 🦎 come fonte dati principale. L'applicazione è progettata per essere reattiva ⚡ e personalizzabile tramite un file di configurazione.

## ⚠️ Nota dell'Autore 👨‍💻

Questo progetto è stato creato come esercizio di apprendimento 💡 da ma che sono sviluppatore Python ancora inesperto. L'obiettivo principale era quello di fare pratica con vari aspetti della programmazione Python, tra cui lo sviluppo di interfacce grafiche con Tkinter, l'interazione con API esterne, il multithreading, la gestione di file di configurazione e la visualizzazione di dati.

Sebbene sia stato fatto uno sforzo per creare un'applicazione funzionale, potrebbe contenere bug 🐞 o aree di miglioramento. Ogni feedback costruttivo è benvenuto! 🙏

## ⚠️ Disclaimer Importante 🚫

**Questa applicazione è stata sviluppata esclusivamente a scopo didattico 🎓 e come esercizio di programmazione. Le informazioni visualizzate sono recuperate da API di terze parti (CoinGecko) e potrebbero non essere sempre accurate o aggiornate in tempo reale.**

**PyCryptoDesk NON fornisce in alcun modo consigli finanziari 💸, di investimento o di trading. Qualsiasi decisione finanziaria presa basandosi (anche parzialmente) sulle informazioni o sulle funzionalità di questa applicazione è di esclusiva responsabilità dell'utente. L'autore non si assume alcuna responsabilità per eventuali perdite o danni derivanti dall'uso di questa applicazione.**

**Si prega di consultare un consulente finanziario qualificato 👨‍💼 prima di prendere qualsiasi decisione di investimento.**

## ✨ Funzionalità Implementate

* **Prezzo Singolo 💲:** Visualizza il prezzo attuale, la variazione 24h e il volume per una specifica criptovaluta in una valuta a scelta.
* **Watchlist Interattiva 📋:** Mostra i dati di mercato per una lista personalizzabile di criptovalute. È possibile aggiungere e rimuovere asset dalla watchlist direttamente dall'interfaccia, e le modifiche vengono salvate.
* **Convertitore Valute 💱:** Converte un importo da una criptovaluta a un'altra valuta (fiat o crypto) usando i tassi attuali.
* **Classifica Market Cap 🏆:** Mostra le prime N criptovalute ordinate per capitalizzazione di mercato, con dettagli come prezzo, variazioni e volumi.
* **Download Dati Storici 💾:** Permette di scaricare i dati storici (prezzo, market cap, volume) per una criptovaluta in formato CSV o JSON.
* **Grafico Prezzi Storici 📈:** Visualizza un grafico dell'andamento del prezzo di una criptovaluta su un periodo selezionato.
* **Configurazione Persistente ⚙️:** Utilizza un file `config.json` per salvare la watchlist e i valori di default per i campi di input delle varie schede, rendendo l'app personalizzabile.
* **Interfaccia Utente Reattiva ⚡:** Le chiamate API vengono gestite in thread separati per non bloccare la GUI.
* **Input Migliorato 👍:** Utilizzo di `ComboBox` per una facile selezione delle valute e `messagebox` per un feedback chiaro su errori e successi.

## 🛠️ Stack Tecnologico / Librerie Utilizzate

* **Python 3** 🐍
* **Tkinter (con ttk)** per l'interfaccia grafica (GUI) 🖼️
* **Requests** per effettuare chiamate alle API HTTP 🌐
* **Pandas** per la manipolazione dei dati, specialmente per le serie storiche usate nei grafici 🐼
* **Matplotlib** per la creazione e visualizzazione dei grafici 📊
* **API di CoinGecko** come fonte dati principale 🦎🔗

## 🚀 Setup e Installazione

1.  **Clona il Repository 📥:**
    ```bash
    git clone [https://github.com/TUO_NOME_UTENTE_GITHUB/PyCryptoDesk.git](https://github.com/TUO_NOME_UTENTE_GITHUB/PyCryptoDesk.git) 
    # (Sostituisci con il tuo URL una volta caricato)
    cd PyCryptoDesk
    ```

2.  **Crea e Attiva un Ambiente Virtuale 🌳📦:**
    ```bash
    python -m venv venv
    # Su Windows:
    venv\Scripts\activate
    # Su macOS/Linux:
    source venv/bin/activate
    ```

3.  **Installa le Dipendenze 🧩🔧:**
    Assicurati di avere il file `requirements.txt` (creato con `pip freeze > requirements.txt` nel tuo ambiente attivo).
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configurazione

Al primo avvio, se il file `config.json` non è presente nella cartella principale del progetto, verrà creato automaticamente con valori di default. Puoi personalizzare questo file per modificare:
* La tua watchlist (`watchlist_ids`).
* Le valute di default e altri valori preimpostati per le varie schede.

Le modifiche alla watchlist fatte tramite l'interfaccia grafica verranno salvate automaticamente in `config.json`.

## ▶️ Come Eseguire l'Applicazione

Una volta completato il setup e con l'ambiente virtuale attivo, esegui:

```bash
python gui_app.py
