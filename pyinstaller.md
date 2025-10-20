# Guida all'uso di PyInstaller per ClamAV-GUI

## Introduzione

Questo documento fornisce una guida completa per l'utilizzo dello script `pyinstaller.py`, che automatizza il processo di creazione di eseguibili standalone per l'applicazione ClamAV-GUI utilizzando PyInstaller.

Lo script è progettato per semplificare il processo di compilazione, gestendo automaticamente:

- Lettura della versione da `clamav_gui/utils/version.py`
- Aggiornamento dinamico dei file di versione (`version_info.txt` e `version_info.py`)
- Configurazione ottimizzata di PyInstaller per l'applicazione
- Gestione delle dipendenze e hidden imports

## Prerequisiti

Prima di utilizzare lo script, assicurati di avere:

1. **Python 3.7+** installato
2. **Ambiente virtuale** attivato (raccomandato)
3. **PyInstaller** installato: `pip install pyinstaller`
4. **Dipendenze del progetto** installate: `pip install -r requirements.txt`

## Utilizzo Base

### Compilazione Semplice

Per creare un eseguibile singolo con le impostazioni predefinite:

```bash
python pyinstaller.py
```

Questo comando:

- Legge la versione corrente da `clamav_gui/utils/version.py`
- Aggiorna automaticamente i file di versione
- Crea un eseguibile singolo nella cartella `dist/`

### Compilazione con Pulizia

Per pulire le directory di build prima della compilazione:

```bash
python pyinstaller.py --clean
```

## Opzioni della Riga di Comando

### Modalità di Output

#### `--onefile` (predefinito)

Crea un singolo file eseguibile contenente tutto il necessario.

```bash
python pyinstaller.py --onefile
```

#### `--dir`

Crea una directory contenente l'eseguibile e tutte le sue dipendenze.

```bash
python pyinstaller.py --dir
```

### Pulizia e Build

#### `--clean`

Rimuove le directory `build/` e `dist/` prima della compilazione.

```bash
python pyinstaller.py --clean
```

### Debug e Logging

#### `--debug`

Abilita il logging dettagliato per diagnosticare problemi.

```bash
python pyinstaller.py --debug
```

#### `--debug-build`

Crea una build di debug con traceback e asserzioni attivate.

```bash
python pyinstaller.py --debug-build
```

### Ottimizzazione e Performance

#### `--no-upx`

Disabilita la compressione UPX per file eseguibili più grandi ma più veloci da avviare.

```bash
python pyinstaller.py --no-upx
```

### Opzioni Windows-Specifiche

#### `--show-console`

Mantiene visibile la finestra della console durante l'esecuzione (solo Windows).

```bash
python pyinstaller.py --show-console
```

## Esempi d'Uso Avanzati

### Build Completa con Debug

```bash
python pyinstaller.py --clean --debug --debug-build
```

Questo comando:

- Pulisce le directory di build
- Abilita logging debug
- Crea una build di debug con traceback

### Build per Distribuzione

```bash
python pyinstaller.py --onefile --clean --no-upx
```

Questo comando crea un eseguibile singolo ottimizzato per la distribuzione, senza compressione UPX per una maggiore compatibilità.

### Build Multi-Directory con Debug

```bash
python pyinstaller.py --dir --clean --debug --show-console
```

Utile per il debugging su Windows, mantiene la console visibile.

## Come Funziona lo Script

### 1. Lettura della Versione

Lo script legge automaticamente la versione da `clamav_gui/utils/version.py`:

```python
def get_version():
    """Get the current version from version.py"""
    # Legge clamav_gui/utils/version.py dinamicamente
```

### 2. Aggiornamento dei File di Versione

Prima della compilazione, aggiorna automaticamente:

- `version_info.txt`: Informazioni di versione per Windows
- `version_info.py`: Modulo Python con struttura VSVersionInfo (senza intestazioni problematiche)

**Nota**: Il file `version_info.py` viene generato senza shebang o commenti per evitare errori di sintassi durante la deserializzazione da parte di PyInstaller.

### 3. Configurazione PyInstaller

Lo script configura automaticamente PyInstaller con:

- **Hidden imports** per PySide6, scipy, scikit-learn
- **Esclusioni** per moduli di test problematici
- **Inclusione dati** per assets e lingue
- **Icona** per Windows (se disponibile)
- **Version info** per metadati del file

### 4. Compilazione

Esegue PyInstaller con timeout di 30 minuti e logging completo.

## Output e Directory

### Directory di Output

- `dist/`: Contiene l'eseguibile finale
- `build/`: Directory di lavoro di PyInstaller (viene pulita automaticamente)
- `logs/`: File di log della compilazione

### File Eseguibile

Il nome dell'eseguibile varia in base alle opzioni:

- `--onefile`: `dist/ClamAV-GUI.exe` (Windows) o `dist/ClamAV-GUI` (Linux/Mac)
- `--dir`: `dist/ClamAV-GUI/ClamAV-GUI.exe` (Windows) o `dist/ClamAV-GUI/ClamAV-GUI` (Linux/Mac)

## Risoluzione dei Problemi

### Errori Comuni

#### 1. "PyInstaller not found"

```bash
# Installa PyInstaller
pip install pyinstaller
```

#### 2. "Could not read version from version.py"

Verifica che `clamav_gui/utils/version.py` esista e contenga una funzione `get_version()`.

#### 3. "Compilation timed out"

La compilazione richiede molto tempo. PyInstaller ottimizza automaticamente l'uso dei core disponibili. Se necessario, puoi ridurre il carico dividendo la compilazione in più passaggi o chiudendo altre applicazioni che consumano risorse.

#### 4. "ValueError: Failed to deserialize VSVersionInfo from text-based representation!"

Questo errore si verificava quando il file `version_info.py` conteneva intestazioni (come shebang o commenti) che impedivano a PyInstaller di analizzare correttamente il contenuto.

**Stato**: ✅ **RISOLTO** - Lo script ora:

- Rimuove automaticamente tutti i file `.spec` esistenti prima della compilazione
- Rigenera il file `version_info.py` senza intestazioni problematiche
- Utilizza percorsi relativi per evitare conflitti di percorsi assoluti

### Debug

Per diagnosticare problemi complessi:

```bash
python pyinstaller.py --debug --debug-build --show-console
```

Questo fornisce:

- Logging dettagliato
- Finestra console visibile (Windows)
- Build con informazioni di debug

### Log Files

I log sono salvati in `logs/pyinstaller_compiler.log` e includono:

- Comandi PyInstaller eseguiti
- Output completo di stdout/stderr
- Errori e warning dettagliati

## Personalizzazione

### Modifica delle Impostazioni Predefinite

Lo script utilizza costanti definite all'inizio del file. Per personalizzazioni permanenti, modifica:

```python
# In pyinstaller.py
PROJECT_NAME = "ClamAV-GUI"
IS_WINDOWS = platform.system() == "Windows"
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"
```

### Aggiunta di Nuovi Hidden Imports

Per aggiungere nuovi hidden imports, modifica la sezione nella funzione `build_pyinstaller()`:

```python
# Aggiungi qui nuovi hidden imports
cmd.extend([
    "--hidden-import", "nuovo_modulo",
    "--hidden-import", "altro_modulo.sottmodulo"
])
```

## Best Practices

1. **Usa sempre `--clean`** per build pulite e riproducibili
2. **Attiva l'ambiente virtuale** prima dell'uso
3. **Verifica i requisiti** siano installati
4. **Usa `--debug`** per troubleshooting
5. **Controlla i log** in caso di errori
6. **Testa l'eseguibile** dopo la compilazione

## Supporto

Per problemi o domande:

1. Controlla i log in `logs/pyinstaller_compiler.log`
2. Usa l'opzione `--debug` per informazioni aggiuntive
3. Verifica che tutte le dipendenze siano installate correttamente

---

## Miglioramenti Recenti

### Versione 1.2.0

- ✅ **Correzione generazione file versione**: Risolto il problema di deserializzazione del file `version_info.py`
- ✅ **Rimozione dipendenze problematiche**: Aggiornati gli hidden imports per versioni più recenti delle librerie
- ✅ **Migliore gestione errori**: Messaggi di errore più chiari e informativi
- ✅ **Documentazione completa**: Guida dettagliata per sviluppatori e utenti

### Problemi Risolti

- Il file `version_info.py` viene ora generato senza intestazioni problematiche
- Rimosso supporto per opzioni non esistenti (`--jobs`) dalla documentazione
- Migliorata la compatibilità con le versioni più recenti di PyInstaller

## Changelog

### [1.2.0] - 2025-10-18

#### Corretto

- Generazione del file `version_info.py` senza shebang o commenti problematici
- Gestione corretta della sintassi per PyInstaller

#### Migliorato

- Documentazione completa e aggiornata
- Rimozione riferimenti a opzioni inesistenti
- Messaggi di errore più chiari

---

*Questa guida è stata generata automaticamente e riflette la configurazione attuale dello script `pyinstaller.py`.*
