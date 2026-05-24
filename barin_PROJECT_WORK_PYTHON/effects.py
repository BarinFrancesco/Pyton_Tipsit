

import cv2
import numpy as np
import os
import time

# trova òa cartella degli asset
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

#funzione che carica l'immagine
def _load_asset(filename):

    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        return cv2.imread(path, cv2.IMREAD_UNCHANGED)  # mantiene canale alpha
    return None

_hat_img     = _load_asset("cappello.png")


# Rettangolo verde sui visi

def draw_face_rectangles(frame, faces):

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


#Funzione che mette limagine sopra al frame

def _overlay_png(frame, png, x, y, target_w, target_h):

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

#funzione che mette il cappello sopra il viso
def apply_hat_overlay(frame, faces):

    result = frame.copy()
    for (x, y, w, h) in faces:
        hat_w = int(w * 1.4)
        hat_h = int(h * 0.7)
        hat_x = x - (hat_w - w) // 2
        hat_y = y - hat_h + 10

        if _hat_img is not None:
            result = _overlay_png(result, _hat_img, hat_x, hat_y, hat_w, hat_h)
        else:
            # Placeholder: cappello a cilindro stilizzato
            cx     = x + w // 2
            top_y  = y - int(h * 0.55)
            # Tesa del cappello
            cv2.rectangle(result,
                          (cx - int(w * 0.65), y - int(h * 0.08)),
                          (cx + int(w * 0.65), y + int(h * 0.04)),
                          (40, 20, 10), -1)
            cv2.rectangle(result,
                          (cx - int(w * 0.65), y - int(h * 0.08)),
                          (cx + int(w * 0.65), y + int(h * 0.04)),
                          (80, 50, 20), 2)
            # Calotta del cappello
            cv2.rectangle(result,
                          (cx - int(w * 0.38), top_y),
                          (cx + int(w * 0.38), y - int(h * 0.06)),
                          (40, 20, 10), -1)
            cv2.rectangle(result,
                          (cx - int(w * 0.38), top_y),
                          (cx + int(w * 0.38), y - int(h * 0.06)),
                          (80, 50, 20), 2)
            # Nastro
            ribbon_y = y - int(h * 0.15)
            cv2.rectangle(result,
                          (cx - int(w * 0.38), ribbon_y),
                          (cx + int(w * 0.38), ribbon_y + int(h * 0.07)),
                          (0, 0, 160), -1)
    return result


#effetto ghost
_ghost_prev = None

def apply_ghost_effect(frame, alpha=0.5):

    global _ghost_prev
    result = frame.copy()
    if _ghost_prev is None:
        _ghost_prev = frame.copy()
        return result

    ghost  = cv2.addWeighted(result, alpha, _ghost_prev, 1.0 - alpha, 0)
    _ghost_prev = ghost.copy()
    return ghost





# funzione per mettere un audio in sottofondo

_SOUND_PATH   = os.path.join(ASSETS_DIR, "sound.mp3")
_audio_thread = None    # thread che riproduce il suono in loop
_audio_stop   = False   # flag per fermare il loop

def _audio_loop():

    global _audio_stop
    try:
        from playsound import playsound
        while not _audio_stop:
            playsound(_SOUND_PATH, block=True)
    except Exception as e:
        print(f"[AUDIO] Errore riproduzione: {e}")
        print("[AUDIO] Installa con:  pip install playsound==1.2.2")

#crea un altro thread che fa il suono per non bloccareil programma
def start_face_swap_sound():

    global _audio_thread, _audio_stop

    if not os.path.exists(_SOUND_PATH):
        print(f"[AUDIO] File non trovato: {_SOUND_PATH}")
        return

    # Se già in esecuzione non fare nulla
    if _audio_thread is not None and _audio_thread.is_alive():
        return

    import threading
    _audio_stop   = False
    _audio_thread = threading.Thread(target=_audio_loop, daemon=True)
    _audio_thread.start()
    print("[AUDIO] Riproduzione avviata.")

#ferma il suono quando chiudo
def stop_face_swap_sound():

    global _audio_stop, _audio_thread
    _audio_stop   = True
    _audio_thread = None
    print("[AUDIO] Riproduzione fermata.")



# filtro joker


_new_face_cache = None
_new_face_loaded = False

# va a prendere l'immagine
def _get_new_face():
    global _new_face_cache, _new_face_loaded
    if _new_face_loaded:
        return _new_face_cache
    path = os.path.join(ASSETS_DIR, "New_Face.jpg")
    if os.path.exists(path):
        _new_face_cache = cv2.imread(path)
    _new_face_loaded = True
    return _new_face_cache

# Posizione dell'ultimo viso rilevato: usata per mantenere la faccia
# anche nei frame in cui il detector fallisce (face detection instabile)
_last_faces = []
_face_miss_counter = 0
_FACE_MISS_TOLERANCE = 8   # frame consecutivi senza viso prima di resettare

#uniamo scala di grigi, filtro ed scritta
def apply_face_swap(frame, faces):

    global _last_faces, _face_miss_counter

    new_face_img = _get_new_face()

    # Tutto in bianco e nero
    gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    #  Stabilizzazione face detection
    if len(faces) > 0:
        _last_faces       = list(faces)
        _face_miss_counter = 0
    else:
        _face_miss_counter += 1
        if _face_miss_counter > _FACE_MISS_TOLERANCE:
            _last_faces = []   # viso perso davvero

    faces_to_use = _last_faces

    # Overlay New_Face
    if new_face_img is None:
        # Avviso direttamente sul frame se manca il file
        cv2.putText(result, "New_Face.jpg non trovata in assets/",
                    (10, result.shape[0] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    else:
        for (x, y, w, h) in faces_to_use:
            fh, fw = result.shape[:2]

            # Allarga leggermente il ROI per coprire bene il viso
            pad_x = int(w * 0.12)
            pad_y = int(h * 0.15)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(fw, x + w + pad_x)
            y2 = min(fh, y + h + pad_y)
            rw, rh = x2 - x1, y2 - y1
            if rw <= 0 or rh <= 0:
                continue

            # Scala la nuova faccia sul ROI
            nf = cv2.resize(new_face_img, (rw, rh), interpolation=cv2.INTER_AREA)

            # Maschera ellittica con bordi morbidi
            mask = np.zeros((rh, rw), dtype=np.uint8)
            cx, cy = rw // 2, rh // 2
            cv2.ellipse(mask, (cx, cy),
                        (int(cx * 0.88), int(cy * 0.92)),
                        0, 0, 360, 255, -1)
            mask = cv2.GaussianBlur(mask, (25, 25), 0)
            m = (mask.astype(np.float32) / 255.0)[:, :, np.newaxis]

            roi     = result[y1:y2, x1:x2].astype(np.float32)
            blended = nf.astype(np.float32) * m + roi * (1.0 - m)
            result[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)

    #  Scritta
    h, w = result.shape[:2]
    testo     = "ADESSO PARLO IO"
    font      = cv2.FONT_HERSHEY_DUPLEX
    scale     = _fit_text_scale(testo, font, w - 40, 3)
    thickness = 4

    (tw, th), baseline = cv2.getTextSize(testo, font, scale, thickness)
    tx = (w - tw) // 2
    ty = h - 28

    # Ombra nera spessa per leggibilità totale
    cv2.putText(result, testo, (tx + 3, ty + 3), font, scale,
                (0, 0, 0), thickness + 4, cv2.LINE_AA)
    #testo
    cv2.putText(result, testo, (tx, ty), font, scale,
                (255, 255, 255), thickness, cv2.LINE_AA)

    return result

#per far si che il testo non "sbordi"
def _fit_text_scale(text, font, max_width, thickness):
    scale = 0.5
    while scale < 6.0:
        (tw, _), _ = cv2.getTextSize(text, font, scale + 0.1, thickness)
        if tw > max_width:
            break
        scale += 0.1
    return round(scale, 1)


# Screenshot

def save_screenshot(frame, directory="."):

    filename = time.strftime("screenshot_%Y%m%d_%H%M%S.jpg")
    filepath = os.path.join(directory, filename)
    cv2.imwrite(filepath, frame)
    return filepath
