# 🥥 Wallet to Cashew Migrator

**Wallet to Cashew Migrator** è un'applicazione web costruita con Python e Streamlit per facilitare la migrazione dei dati finanziari dall'app "Wallet by BudgetBakers" alla nuova app "Cashew".

Questa app non si limita a convertire un CSV: genera un file di backup **database SQLite nativo** per Cashew, preservando categorie, icone, colori e soprattutto **collegando automaticamente i trasferimenti** tra conti.

## ✨ Funzionalità

*   **Migrazione Completa:** Trasforma il CSV di Wallet in un database Cashew `.sqlite` pronto all'uso.
*   **Rilevamento Trasferimenti:** Identifica automaticamente le transazioni di uscita e entrata corrispondenti (stesso importo, stessa data) e le collega logicamente nel database.
*   **Mappatura Intelligente (AI):** Usa algoritmi di "fuzzy matching" per suggerire automaticamente la corrispondenza tra le vecchie categorie di Wallet e la nuova struttura di Cashew.
*   **Editor Categorie:** Interfaccia grafica per disegnare la nuova struttura (Categorie Madre e Sottocategorie), assegnare colori e icone.
*   **Supporto Dark Mode:** L'interfaccia si adatta al tema del sistema operativo.
*   **Privacy:** Tutto il processo avviene localmente (o nel container), nessun dato viene inviato a server esterni.

## 🚀 Installazione e Avvio

### Prerequisiti
*   Python 3.8 o superiore
*   pip

### 1. Clona o Scarica il progetto
```bash
git clone https://github.com/tuo-username/wallet-to-cashew.git
cd wallet-to-cashew
```

### 2. Installa le dipendenze
È consigliato usare un virtual environment.
```bash
# Crea virtual env (opzionale)
python3 -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate

# Installa pacchetti
pip install -r requirements.txt
```

### 3. Avvia l'applicazione
```bash
streamlit run app.py
```
L'app si aprirà automaticamente nel tuo browser all'indirizzo `http://localhost:8501`.

## 📖 Guida all'Uso

Segui i passaggi guidati (Wizard) nell'applicazione:

1.  **Caricamento:**
    *   Esporta i tuoi dati da Wallet in formato CSV.
    *   Scegli se vuoi generare un **Database Cashew** (consigliato per una migrazione pulita) o un semplice CSV.
    *   Carica il file `wallet-export.csv`.

2.  **Categorie:**
    *   Definisci le categorie che vuoi avere su Cashew.
    *   Puoi creare categorie principali e sottocategorie, e assegnare colori e icone.

3.  **Mappatura:**
    *   Clicca su **"✨ Esegui Auto-Mappatura IA"**.
    *   Il sistema cercherà di indovinare dove vanno le tue vecchie spese.
    *   Controlla e correggi manualmente le associazioni se necessario.

4.  **Esportazione:**
    *   Scarica il file `cashew_backup.sqlite`.
    *   Invia il file al tuo telefono.
    *   Apri Cashew -> **Impostazioni** -> **Backup e Ripristino** -> **Ripristina Backup** e seleziona il file.

## 📂 Struttura del Progetto

*   `app.py`: Punto di ingresso dell'applicazione Streamlit.
*   `ui/`: Contiene i moduli per le diverse schermate del wizard.
*   `logic.py`: Contiene la logica di business (parsing CSV, matching trasferimenti, AI mapping).
*   `database.py`: Gestisce la creazione del database SQLite compatibile con Cashew.
*   `models.py`: Definizioni dei dati con Pydantic.

## 🛠️ Note Tecniche

*   **Database:** Il file generato è un database SQLite 3 che rispetta rigorosamente lo schema di Cashew (tabelle `transactions`, `wallets`, `categories`, etc.).
*   **Encoding:** Il parser gestisce automaticamente la codifica `cp1252` tipica degli export Excel/CSV problematici.

---
Fatto con ❤️ per semplificare la tua gestione finanziaria.
