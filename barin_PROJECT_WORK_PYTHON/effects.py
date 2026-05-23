"""
effects.py - Effetti che utilizzano la face detection e operazioni di sistema.

Ogni funzione che trasforma il frame:
  - Riceve il frame come primo parametro
  - Restituisce il frame modificato
  - Non modifica l'originale
  - Ha un commento che spiega brevemente cosa fa
"""

import cv2
import numpy as np
import os
import time

# ─── Asset overlay (PNG con canale alpha) ─────────────────────────────────────
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def _load_asset(filename):
    """Carica un PNG con canale alpha dalla cartella assets. Ritorna None se non trovato."""
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        return cv2.imread(path, cv2.IMREAD_UNCHANGED)  # mantiene canale alpha
    return None

_hat_img     = _load_asset("cappello.png")
_glasses_img = _load_asset("occhiali.png")

# ─── New_Face: caricata dalla root del progetto ────────────────────────────────
_NEW_FACE_PATH = os.path.join(os.path.dirname(__file__), "New_Face.jpg")

def _load_new_face():
    """
    Carica New_Face.jpg dalla cartella del progetto.
    Ritorna l'immagine BGR oppure None se il file non esiste.
    """
    if os.path.exists(_NEW_FACE_PATH):
        img = cv2.imread(_NEW_FACE_PATH)
        if img is not None:
            return img
    return None



# ─── Rettangolo verde sui visi ────────────────────────────────────────────────

def draw_face_rectangles(frame, faces):
    """
    Disegna un rettangolo verde attorno a ogni viso rilevato.
    Aggiunge anche un piccolo punto centrale e la numerazione del viso.
    """
    result = frame.copy()
    for i, (x, y, w, h) in enumerate(faces):
        # Rettangolo verde principale
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 220, 50), 2)

        # Angoli decorativi (stile "targeting")
        corner = 18
        thick  = 3
        color  = (0, 255, 80)
        # In alto a sinistra
        cv2.line(result, (x, y),             (x + corner, y),         color, thick)
        cv2.line(result, (x, y),             (x, y + corner),         color, thick)
        # In alto a destra
        cv2.line(result, (x + w, y),         (x + w - corner, y),     color, thick)
        cv2.line(result, (x + w, y),         (x + w, y + corner),     color, thick)
        # In basso a sinistra
        cv2.line(result, (x, y + h),         (x + corner, y + h),     color, thick)
        cv2.line(result, (x, y + h),         (x, y + h - corner),     color, thick)
        # In basso a destra
        cv2.line(result, (x + w, y + h),     (x + w - corner, y + h), color, thick)
        cv2.line(result, (x + w, y + h),     (x + w, y + h - corner), color, thick)

        # Etichetta "FACE N" sopra il rettangolo
        label = f"FACE {i + 1}"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(result, (x, y - lh - 8), (x + lw + 6, y), (0, 180, 40), -1)
        cv2.putText(result, label, (x + 3, y - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # Punto centrale
        cx, cy = x + w // 2, y + h // 2
        cv2.circle(result, (cx, cy), 3, (0, 255, 80), -1)

    return result


# ─── Blur sfondo ──────────────────────────────────────────────────────────────

def apply_background_blur(frame, faces, blur_strength=51):
    """
    Sfoca l'intero frame tranne la regione del viso rilevata.
    Se non ci sono visi, sfoca tutto il frame.
    blur_strength deve essere un numero dispari.
    """
    result = frame.copy()
    blurred = cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)

    if len(faces) == 0:
        return blurred  # nessun viso: sfoca tutto

    # Maschera nera; le regioni dei visi saranno bianche
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    for (x, y, w, h) in faces:
        # Leggermente allargata per includere capelli/mento
        pad_x = int(w * 0.15)
        pad_y = int(h * 0.2)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(frame.shape[1], x + w + pad_x)
        y2 = min(frame.shape[0], y + h + pad_y)
        cv2.ellipse(mask, ((x1 + x2) // 2, (y1 + y2) // 2),
                    ((x2 - x1) // 2, (y2 - y1) // 2),
                    0, 0, 360, 255, -1)

    # Sfuma i bordi della maschera per una transizione naturale
    mask = cv2.GaussianBlur(mask, (31, 31), 0)

    # Compositing: viso nitido + sfondo sfocato
    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
    result = (frame.astype(np.float32) * mask_3ch +
              blurred.astype(np.float32) * (1.0 - mask_3ch)).astype(np.uint8)
    return result


# ─── Overlay PNG con alpha ─────────────────────────────────────────────────────

def _overlay_png(frame, png, x, y, target_w, target_h):
    """
    Sovrappone un PNG con canale alpha (BGRA) sul frame BGR.
    L'immagine viene scalata a (target_w, target_h) e posizionata in (x, y).
    """
    if png is None:
        return frame

    result = frame.copy()
    png_resized = cv2.resize(png, (target_w, target_h), interpolation=cv2.INTER_AREA)

    # Coordinate clippate ai bordi del frame
    fh, fw = result.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(fw, x + target_w), min(fh, y + target_h)
    if x2 <= x1 or y2 <= y1:
        return result

    # Regione corrispondente nel PNG ritagliato
    px1, py1 = x1 - x, y1 - y
    px2, py2 = px1 + (x2 - x1), py1 + (y2 - y1)

    roi   = result[y1:y2, x1:x2].astype(np.float32)
    patch = png_resized[py1:py2, px1:px2]

    bgr   = patch[:, :, :3].astype(np.float32)
    alpha = (patch[:, :, 3] / 255.0)[:, :, np.newaxis]

    blended = bgr * alpha + roi * (1.0 - alpha)
    result[y1:y2, x1:x2] = blended.astype(np.uint8)
    return result


def apply_hat_overlay(frame, faces):
    """Sovrappone il cappello PNG sopra ogni viso rilevato."""
    result = frame.copy()
    for (x, y, w, h) in faces:
        hat_w = int(w * 1.4)
        hat_h = int(h * 0.7)
        hat_x = x - (hat_w - w) // 2
        hat_y = y - hat_h + 10
        result = _overlay_png(result, _hat_img, hat_x, hat_y, hat_w, hat_h)
    return result


def apply_glasses_overlay(frame, faces):
    """
    Sovrappone gli occhiali PNG all'altezza degli occhi di ogni viso.
    Approssima la posizione degli occhi come il terzo superiore del viso.
    """
    result = frame.copy()
    for (x, y, w, h) in faces:
        g_w  = int(w * 0.9)
        g_h  = int(h * 0.25)
        g_x  = x + (w - g_w) // 2
        g_y  = y + int(h * 0.25)
        result = _overlay_png(result, _glasses_img, g_x, g_y, g_w, g_h)
    return result


# ─── Rilevamento movimento ────────────────────────────────────────────────────

_prev_frame_gray = None

def apply_motion_detection(frame, threshold=30):
    """
    Confronta il frame corrente con il precedente usando cv2.absdiff.
    Evidenzia in rosso le zone con cambiamenti superiori alla soglia.
    """
    global _prev_frame_gray
    result = frame.copy()
    gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray   = cv2.GaussianBlur(gray, (11, 11), 0)

    if _prev_frame_gray is None:
        _prev_frame_gray = gray
        return result

    diff = cv2.absdiff(_prev_frame_gray, gray)
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Colora le zone in movimento in rosso semitrasparente
    motion_mask = thresh > 0
    overlay = result.copy()
    overlay[motion_mask] = [0, 0, 200]
    result = cv2.addWeighted(result, 0.7, overlay, 0.3, 0)

    _prev_frame_gray = gray
    return result


# ─── Ghost effect ─────────────────────────────────────────────────────────────

_ghost_prev = None

def apply_ghost_effect(frame, alpha=0.5):
    """
    Sovrappone il frame corrente con una versione pesata del frame precedente
    per creare un effetto scia/fantasma.
    """
    global _ghost_prev
    result = frame.copy()
    if _ghost_prev is None:
        _ghost_prev = frame.copy()
        return result

    ghost  = cv2.addWeighted(result, alpha, _ghost_prev, 1.0 - alpha, 0)
    _ghost_prev = ghost.copy()
    return ghost



# ─── Face Swap con New_Face.jpg ───────────────────────────────────────────────

def apply_face_swap(frame, faces):
    """
    Sostituisce ogni viso rilevato con New_Face.jpg.
    La nuova faccia viene scalata esattamente sul rettangolo del viso,
    poi blended con una maschera ellittica sfumata per bordi naturali.
    Se New_Face.jpg non esiste, ritorna il frame invariato con un avviso.
    """
    new_face_img = _load_new_face()

    result = frame.copy()

    if new_face_img is None:
        # Avvisa l'utente direttamente sul frame
        msg = "New_Face.jpg non trovata nella cartella del progetto"
        cv2.putText(result, msg, (10, result.shape[0] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        return result

    if len(faces) == 0:
        return result

    for (x, y, w, h) in faces:
        # Ritaglio sicuro entro i bordi del frame
        fh, fw = result.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(fw, x + w)
        y2 = min(fh, y + h)
        rw, rh = x2 - x1, y2 - y1
        if rw <= 0 or rh <= 0:
            continue

        # Scala New_Face sulla dimensione esatta del viso rilevato
        new_face_resized = cv2.resize(new_face_img, (rw, rh), interpolation=cv2.INTER_AREA)

        # Maschera ellittica sfumata: bordi morbidi per un look naturale
        mask = np.zeros((rh, rw), dtype=np.uint8)
        cx, cy = rw // 2, rh // 2
        cv2.ellipse(mask, (cx, cy), (int(cx * 0.92), int(cy * 0.95)),
                    0, 0, 360, 255, -1)
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        mask_f = mask.astype(np.float32) / 255.0

        # Compositing sul ROI del frame
        roi     = result[y1:y2, x1:x2].astype(np.float32)
        new_f   = new_face_resized.astype(np.float32)
        m       = mask_f[:, :, np.newaxis]
        blended = new_f * m + roi * (1.0 - m)
        result[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)

    return result


# ─── Screenshot ───────────────────────────────────────────────────────────────

def save_screenshot(frame, directory="."):
    """
    Salva il frame corrente come JPEG con nome che include data e ora,
    così i file non si sovrascrivono mai.
    """
    filename = time.strftime("screenshot_%Y%m%d_%H%M%S.jpg")
    filepath = os.path.join(directory, filename)
    cv2.imwrite(filepath, frame)
    return filepath
