#!/bin/bash

# ============================================================
# run.sh — Script di avvio per Filtri Webcam in Real Time
# Uso: bash run.sh
# ============================================================

set -e

# ---- Colori per output ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  🎥  Filtri Webcam in Real Time  ${NC}"
echo -e "${GREEN}============================================${NC}"

# ---- Directory del progetto ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---- Controlla che Python sia installato ----
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo -e "${RED}[ERRORE] Python non trovato. Installalo da https://python.org/downloads${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo -e "${GREEN}[OK]${NC} $PYTHON_VERSION trovato."

# ---- Attiva il virtual environment se esiste ----
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}[OK]${NC} Virtual environment trovato, lo attivo..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo -e "${YELLOW}[AVVISO]${NC} Nessun virtual environment trovato in ./venv"
    echo "  Puoi crearne uno con:"
    echo "    python3 -m venv venv && source venv/bin/activate"
    echo "  Continuo usando Python di sistema..."
fi

# ---- Controlla e installa le dipendenze ----
echo ""
echo "Verifica dipendenze da requirements.txt..."

if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo -e "${RED}[ERRORE] requirements.txt non trovato!${NC}"
    exit 1
fi

$PYTHON -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet --exists-action i
echo -e "${GREEN}[OK]${NC} Dipendenze installate/aggiornate."

# ---- Crea cartelle necessarie se non esistono ----
mkdir -p "$SCRIPT_DIR/screenshots"
mkdir -p "$SCRIPT_DIR/recordings"
echo -e "${GREEN}[OK]${NC} Cartelle screenshots/ e recordings/ pronte."

# ---- Controlla che la webcam sia disponibile (solo su Linux) ----
if [ -e /dev/video0 ]; then
    echo -e "${GREEN}[OK]${NC} Webcam rilevata su /dev/video0."
fi

# ---- Avvia l'applicazione ----
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Avvio applicazione...${NC}"
echo -e "${GREEN}  Premi Q per uscire dalla finestra webcam.${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

$PYTHON "$SCRIPT_DIR/main.py"

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}[ERRORE] L'applicazione è uscita con codice $EXIT_CODE.${NC}"
    exit $EXIT_CODE
fi

echo ""
echo -e "${GREEN}Applicazione chiusa correttamente. Arrivederci!${NC}"
