# 🎥 Filtri Webcam in Real Time

Un'applicazione desktop Python che accede alla webcam in tempo reale e permette di applicare filtri visivi, effetti e overlay interattivi tramite tastiera.

---

## 📋 Descrizione

L'app acquisisce il feed della webcam e ti permette di applicare filtri colore (scala di grigi, negativo, sepia, cartoon, heatmap, pixelate, vignettatura), rilevare volti in tempo reale tramite Haar cascade, sovrapporre overlay PNG (cappello, occhiali, maschera) e salvare screenshot con un tasto. Il tutto è controllabile da tastiera mentre la finestra è aperta.

---

## ⚙️ Requisiti

### Sistema operativo
- Linux (consigliato), macOS, Windows
- Testato su Raspberry Pi OS (Debian 12, Bookworm) con webcam USB

### Hardware
- Webcam (integrata o USB)
- RAM minima consigliata: 512 MB (1 GB+ per Raspberry Pi)

### Software
- Python **3.9** o superiore
- pip aggiornato
- (Raspberry Pi) `libcamera` o driver V4L2 abilitati

---

## 🚀 Installazione

### 1. Clona il repository

```bash
git clone https://github.com/tuo-utente/filtri-webcam.git
cd filtri-webcam
```

### 2. (Consigliato) Crea un ambiente virtuale

```bash
python3 -m venv venv
source venv/bin/activate      # Linux / macOS / Raspberry Pi
# oppure su Windows:
# venv\Scripts\activate
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

> ⚠️ Su Raspberry Pi, se OpenCV non si installa tramite pip, usa il pacchetto di sistema:
> ```bash
> sudo apt-get install python3-opencv
> ```

---

## ▶️ Come avviare

### Metodo rapido (script shell)

```bash
bash run.sh
```

### Metodo manuale

```bash
python3 main.py
```

---

## ⌨️ Tasti disponibili

| Tasto | Azione |
|-------|--------|
| `Q` | Esci dall'applicazione |
| `S` | Salva screenshot (con filtri applicati) in `screenshots/` |
| `1` | Filtro: Scala di grigi |
| `2` | Filtro: Negativo |
| `3` | Filtro: Sepia |
| `4` | Filtro: Cartoon |
| `5` | Filtro: Heatmap (termico) |
| `6` | Filtro: Pixelate |
| `7` | Filtro: Vignettatura |
| `0` | Nessun filtro (originale) |
| `F` | Flip specchio (selfie mode) |
| `B` | Sfondo sfocato (face detection) |
| `H` | Overlay cappello |
| `G` | Overlay occhiali |
| `M` | Overlay maschera/barba |
| `E` | Ghost effect (scia) |
| `D` | Rilevamento movimento |
| `R` | Avvia/Ferma registrazione video (indicatore rosso) |
| `A` | Modalità automatica (scorre i filtri ogni N secondi) |
| `TAB` | Naviga la barra filtri a schermo |

---

## 📁 Struttura del progetto

```
progetto/
│
├── main.py          # Loop principale, gestione tasti, orchestrazione
├── filters.py       # Funzioni per i filtri colore
├── effects.py       # Effetti con face detection e overlay
├── ui.py            # HUD, testo a schermo, barra filtri
├── run.sh           # Script di avvio
├── requirements.txt # Dipendenze Python
├── README.md        # Questo file
│
└── assets/
    ├── cappello.png
    ├── occhiali.png
    └── maschera.png
```

---

## 📸 Screenshot

Gli screenshot vengono salvati automaticamente nella cartella `screenshots/` con il formato:

```
screenshot_YYYYMMDD_HHMMSS.jpg
```

---

## 🎬 Registrazione video

La registrazione produce file `.mp4` nella cartella `recordings/` con il formato:

```
rec_YYYYMMDD_HHMMSS.mp4
```

Un indicatore rosso lampeggiante appare in alto a destra durante la registrazione.

---

## 🍓 Note specifiche per Raspberry Pi

- Usa una webcam USB compatibile V4L2 (es. Logitech C270, C920).
- Se OpenCV non si trova via pip, installa con `sudo apt-get install python3-opencv`.
- Su Raspberry Pi 4 con 1 GB di RAM, chiudi le altre applicazioni per evitare lag.
- Se la webcam non viene rilevata, verifica con:
  ```bash
  ls /dev/video*
  ```
  e modifica l'indice del device in `main.py` (default `0`).
- Risoluzione consigliata su Pi: 640×480 per prestazioni fluide.
- Per avviare automaticamente all'accensione, aggiungi `bash /percorso/run.sh` a `/etc/rc.local`.

---

## 📦 Dipendenze principali

| Libreria | Versione | Uso |
|----------|----------|-----|
| `opencv-python` | 4.x | Cattura webcam, filtri, face detection |
| `numpy` | 1.x | Manipolazione array e maschere |

Tutte le versioni esatte sono in `requirements.txt`.

---

## 📄 Licenza

Progetto didattico — uso libero a scopo educativo.
