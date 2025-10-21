# Guida alla Compilazione - ClamAV GUI

Questa guida spiega come utilizzare gli script di compilazione per creare un eseguibile Windows (.exe) del ClamAV GUI.

## Script Disponibili

### 1. `compile_app.py` (Script Python principale)

Script di compilazione avanzato con opzioni configurabili.

### 2. `compila.bat` (Script Batch per Windows)

Versione semplificata per utenti Windows, con menu interattivo.

## Utilizzo

### Utilizzo del Batch (Raccomandato per Windows)

1. Apri il Prompt dei Comandi o PowerShell nella directory del progetto
2. Esegui:

   ```batch
   compila.bat
   ```

3. Segui le istruzioni a schermo per scegliere le opzioni di compilazione

### Utilizzo dello Script Python

```bash
# Compilazione normale (raccomandata)
python compile_app.py

# Compilazione con debug (console visibile)
python compile_app.py --debug

# Pulisce tutto e ricompila
python compile_app.py --clean

# Senza compressione UPX
python compile_app.py --no-upx

# Crea directory invece di singolo file
python compile_app.py --onedir
```

## Opzioni di Compilazione

### Modalità Normale (Default)

- ✅ Eseguibile singolo (`--onefile`)
- ✅ Compressione UPX attivata
- ✅ Icona applicazione inclusa
- ✅ Informazioni versione corrette
- ✅ Console nascosta in esecuzione

### Modalità Debug

- 🔍 Console visibile durante l'esecuzione
- 🐛 Utile per debug e sviluppo
- 📝 Mostra messaggi di log dettagliati

### Pulizia (--clean)

- 🧹 Rimuove directory `build/`, `dist/`, e output precedente
- 🔄 Ricompila tutto da zero

### Senza UPX (--no-upx)

- 📦 Eseguibile più grande ma compatibile con tutti i sistemi
- ⚡ Leggermente più veloce da avviare

### Directory (--onedir)

- 📁 Crea una cartella con eseguibile + dipendenze separate
- 🔧 Più facile da debuggare
- 📏 Più grande dello spazio occupato

## Output della Compilazione

Dopo una compilazione riuscita, verrà creata la directory:

```txt
dist/ClamAV-GUI/
├── ClamAV-GUI.exe      # Eseguibile principale
├── README.txt          # Istruzioni per l'uso
└── [altri file necessari]
```

## Requisiti di Sistema

### Per la Compilazione

- **Python 3.8+** con pip
- **PyInstaller 6.0+**
- **pywin32** (per funzionalità Windows)
- **pefile** (per analisi eseguibili)

### Per l'Eseguibile Finale

- **Windows 10/11 (64-bit)**
- **ClamAV** (opzionale, ma raccomandato)

## Installazione Automatica Dipendenze

Il compilatore installerà automaticamente le dipendenze necessarie se non presenti:

```bash
pip install pyinstaller pywin32 pefile
```

## Risoluzione Problemi

### Errore: "Python non trovato"

- Assicurati che Python sia installato
- Verifica che `python` sia nel PATH di sistema

### Errore: "Modulo non trovato"

- Installa le dipendenze: `pip install -r requirements.txt`
- Poi reinstalla quelle per la compilazione

### Eseguibile non si avvia

- Verifica che tutti i dati siano inclusi correttamente
- Prova la modalità `--onedir` per debuggare
- Controlla i log dell'applicazione

### Antivirus blocca l'eseguibile

- È normale - aggiungi l'eseguibile alle eccezioni dell'antivirus
- Il file è sicuro, creato dal tuo sistema

## Personalizzazione

Puoi modificare il file `compile_app.py` per personalizzare:

### Versione

Modifica `APP_VERSION`

### Descrizione

Modifica `APP_DESCRIPTION`

### Icona

Modifica `find_icon()` per percorsi diversi

### Dipendenze

Aggiungi/rimuovi elementi in `hiddenimports`

## Supporto

Per problemi o domande:

- **Email**: [Nsfr750](mailto:nsfr750@yandex.com)
- **Repository**: [https://github.com/Nsfr750/clamav-gui](https://github.com/Nsfr750/clamav-gui)

---

© Copyright 2025 Nsfr750 - All rights reserved
