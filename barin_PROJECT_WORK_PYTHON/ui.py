"""
ui.py - Interfaccia utente sovraimpressa sul frame webcam.

Gestisce HUD (informazioni in tempo reale) e barra filtri navigabile.
Ogni funzione riceve e restituisce il frame modificato.
"""

import cv2
import numpy as np


# ─── Costanti di stile ────────────────────────────────────────────────────────
FONT        = cv2.FONT_HERSHEY_SIMPLEX
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0,   0,   0)
COLOR_GREEN = (0,   220, 80)
COLOR_RED   = (0,   0,   220)
COLOR_BLUE  = (220, 160, 0)
COLOR_YELLOW= (0,   220, 220)


def _draw_text_with_shadow(frame, text, pos, font_scale=0.55, color=COLOR_WHITE,
                           thickness=1, shadow_offset=1):
    """
    Disegna testo con ombra nera per garantire leggibilità su qualsiasi sfondo.
    """
    x, y = pos
    # Ombra
    cv2.putText(frame, text, (x + shadow_offset, y + shadow_offset),
                FONT, font_scale, COLOR_BLACK, thickness + 1, cv2.LINE_AA)
    # Testo principale
    cv2.putText(frame, text, (x, y),
                FONT, font_scale, color, thickness, cv2.LINE_AA)


def draw_hud(frame, info: dict):
    """
    Sovraimpressa nell'angolo in alto a sinistra del frame.
    Mostra: filtro attivo, numero facce, FPS, stato registrazione, mirror, blur.

    info = {
        'filter':    str   - nome filtro attivo
        'faces':     int   - numero di facce rilevate
        'fps':       float - FPS correnti
        'recording': bool  - True se si sta registrando
        'mirror':    bool  - True se flip specchio attivo
        'blur_bg':   bool  - True se blur sfondo attivo
    }
    """
    result = frame.copy()
    h, w   = result.shape[:2]

    # Rettangolo semitrasparente come sfondo HUD
    overlay = result.copy()
    cv2.rectangle(overlay, (8, 8), (290, 130), (20, 20, 20), -1)
    result = cv2.addWeighted(result, 0.55, overlay, 0.45, 0)

    # Riga 1 — Filtro attivo
    _draw_text_with_shadow(result,
        f"Filtro: {info.get('filter', '?')}",
        (16, 34), font_scale=0.6, color=COLOR_GREEN)

    # Riga 2 — Facce rilevate
    n_faces = info.get('faces', 0)
    face_color = COLOR_YELLOW if n_faces > 0 else COLOR_WHITE
    _draw_text_with_shadow(result,
        f"Facce: {n_faces}",
        (16, 60), font_scale=0.55, color=face_color)

    # Riga 3 — FPS
    fps_val = info.get('fps', 0.0)
    fps_color = COLOR_GREEN if fps_val >= 25 else (COLOR_YELLOW if fps_val >= 15 else COLOR_RED)
    _draw_text_with_shadow(result,
        f"FPS: {fps_val:.1f}",
        (16, 84), font_scale=0.55, color=fps_color)

    # Riga 4 — Stato effetti attivi
    stati = []
    if info.get('mirror'):    stati.append("MIRROR")
    if info.get('blur_bg'):   stati.append("BLUR-BG")
    if info.get('face_rect'): stati.append("FACE-BOX")
    if info.get('face_swap'): stati.append("FACE-SWAP")
    if info.get('hat'):       stati.append("HAT")
    if info.get('glasses'):   stati.append("GLASSES")
    if info.get('motion'):    stati.append("MOTION")
    if info.get('ghost'):     stati.append("GHOST")
    if stati:
        # Se troppi stati, li spezza su due righe
        riga1 = " | ".join(stati[:4])
        riga2 = " | ".join(stati[4:])
        _draw_text_with_shadow(result, riga1,
            (16, 108), font_scale=0.38, color=COLOR_BLUE)
        if riga2:
            _draw_text_with_shadow(result, riga2,
                (16, 124), font_scale=0.38, color=COLOR_BLUE)

    # Indicatore REC (angolo in alto a destra)
    if info.get('recording'):
        rec_x = w - 90
        cv2.circle(result, (rec_x, 24), 8, COLOR_RED, -1)
        _draw_text_with_shadow(result, "REC", (rec_x + 14, 30),
                               font_scale=0.55, color=COLOR_RED)

    return result


def draw_filter_bar(frame, filter_list, active_name):
    """
    Barra filtri in basso al frame: mostra tutti i filtri disponibili,
    evidenziando quello attivo con sfondo colorato.

    filter_list: lista di tuple (nome, funzione) - come FILTER_MAP.values()
    active_name: nome del filtro correntemente attivo
    """
    result  = frame.copy()
    h, w    = result.shape[:2]

    bar_h   = 32
    bar_y   = h - bar_h

    # Sfondo barra semitrasparente
    overlay = result.copy()
    cv2.rectangle(overlay, (0, bar_y), (w, h), (20, 20, 20), -1)
    result = cv2.addWeighted(result, 0.45, overlay, 0.55, 0)

    # Calcola larghezza di ogni slot
    n       = len(filter_list)
    slot_w  = w // n if n > 0 else w

    for i, (name, _) in enumerate(filter_list):
        x1 = i * slot_w
        x2 = x1 + slot_w - 2
        is_active = (name == active_name)

        # Sfondo slot attivo
        if is_active:
            cv2.rectangle(result, (x1, bar_y + 1), (x2, h - 1), (50, 180, 80), -1)

        # Numero tasto (1-indexed)
        label = f"{i+1}:{name}"
        # Tronca se troppo lungo
        if len(label) > 10:
            label = label[:9] + "."

        text_color = COLOR_BLACK if is_active else COLOR_WHITE
        scale = 0.38
        tx = x1 + 4
        ty = bar_y + 21
        cv2.putText(result, label, (tx, ty), FONT, scale, text_color, 1, cv2.LINE_AA)

    return result


def draw_label_above_face(frame, faces, label="Utente"):
    """
    Scrive un'etichetta sopra ogni viso rilevato.
    Utile come effetto aggiuntivo o per debug.
    """
    result = frame.copy()
    for (x, y, w, h) in faces:
        _draw_text_with_shadow(result, label,
                               (x, max(y - 10, 20)),
                               font_scale=0.6, color=COLOR_YELLOW, thickness=1)
    return result


def draw_command_panel(frame, active_effects: dict):
    """
    Pannello comandi fisso a sinistra, appena sotto la barra di stato (HUD).
    Elenca tutti i comandi disponibili divisi in sezioni:
      - Filtri colore (tasti 1-8)
      - Effetti faccia (tasti F, B, N)
      - Controlli generali (M, S, R, Q)
    Gli effetti attivi vengono evidenziati in verde.

    active_effects: dict con chiavi 'face_rect', 'blur_bg', 'face_swap', 'mirror', 'recording'
    """
    result = frame.copy()

    # ── Struttura del pannello ────────────────────────────────────────────────
    # Ogni voce è (tasto, descrizione, chiave_stato_o_None)
    # Se chiave_stato è None → non ha uno stato on/off (es. screenshot)
    sections = [
        ("── FILTRI COLORE ──", None, [
            ("[1]", "Originale",      None),
            ("[2]", "Scala di grigi", None),
            ("[3]", "Negativo",       None),
            ("[4]", "Sepia",          None),
            ("[5]", "Heatmap",        None),
            ("[6]", "Cartoon",        None),
            ("[7]", "Pixelate",       None),
            ("[8]", "Vignettatura",   None),
        ]),
        ("── EFFETTI FACCIA ──", None, [
            ("[F]", "Box viso",       "face_rect"),
            ("[B]", "Blur sfondo",    "blur_bg"),
            ("[N]", "Face swap",      "face_swap"),
            ("[H]", "Cappello",       "hat"),
            ("[G]", "Occhiali",       "glasses"),
        ]),
        ("── EFFETTI SPECIALI ──", None, [
            ("[O]", "Movimento",      "motion"),
            ("[T]", "Ghost/scia",     "ghost"),
        ]),
        ("── CONTROLLI ──", None, [
            ("[M]", "Mirror",         "mirror"),
            ("[S]", "Screenshot",     None),
            ("[R]", "Registra",       "recording"),
            ("[Q]", "Esci",           None),
        ]),
    ]

    # ── Dimensioni e posizione ────────────────────────────────────────────────
    LINE_H   = 19          # altezza di ogni riga in pixel
    PAD_X    = 10          # padding interno orizzontale
    PAD_Y    = 8           # padding interno verticale
    BOX_W    = 190         # larghezza del pannello
    START_X  = 8           # distanza dal bordo sinistro
    START_Y  = 138         # sotto l'HUD (che finisce ~130px)

    # Conta le righe totali: titolo sezione + voci
    total_rows = sum(1 + len(voci) for _, _, voci in sections) + len(sections) - 1
    BOX_H = total_rows * LINE_H + PAD_Y * 2 + 4

    # ── Sfondo semitrasparente ────────────────────────────────────────────────
    overlay = result.copy()
    cv2.rectangle(overlay,
                  (START_X, START_Y),
                  (START_X + BOX_W, START_Y + BOX_H),
                  (15, 15, 15), -1)
    result = cv2.addWeighted(result, 0.4, overlay, 0.6, 0)

    # Bordo sottile
    cv2.rectangle(result,
                  (START_X, START_Y),
                  (START_X + BOX_W, START_Y + BOX_H),
                  (80, 80, 80), 1)

    # ── Disegna le voci ───────────────────────────────────────────────────────
    cursor_y = START_Y + PAD_Y + LINE_H

    for s_idx, (titolo, _, voci) in enumerate(sections):
        # Separatore tra sezioni (non prima della prima)
        if s_idx > 0:
            cursor_y += 6

        # Titolo sezione
        cv2.putText(result, titolo,
                    (START_X + PAD_X, cursor_y),
                    FONT, 0.36, (160, 160, 160), 1, cv2.LINE_AA)
        cursor_y += LINE_H

        for (tasto, descrizione, stato_key) in voci:
            is_active = stato_key is not None and active_effects.get(stato_key, False)

            # Sfondo verde per le voci attive
            if is_active:
                cv2.rectangle(result,
                              (START_X + 2, cursor_y - LINE_H + 4),
                              (START_X + BOX_W - 2, cursor_y + 3),
                              (30, 100, 40), -1)

            # Tasto (es. "[F]") in giallo/verde
            key_color  = COLOR_GREEN if is_active else COLOR_YELLOW
            text_color = COLOR_BLACK if is_active else COLOR_WHITE

            cv2.putText(result, tasto,
                        (START_X + PAD_X, cursor_y),
                        FONT, 0.40, key_color, 1, cv2.LINE_AA)

            # Descrizione
            cv2.putText(result, descrizione,
                        (START_X + PAD_X + 34, cursor_y),
                        FONT, 0.40, text_color, 1, cv2.LINE_AA)

            # Indicatore ON a destra per effetti attivi
            if is_active:
                cv2.putText(result, "ON",
                            (START_X + BOX_W - 30, cursor_y),
                            FONT, 0.36, COLOR_GREEN, 1, cv2.LINE_AA)

            cursor_y += LINE_H

    return result


def draw_controls_overlay(frame):
    """
    Mantenuta per compatibilità. Usa draw_command_panel per il pannello completo.
    """
    return frame
