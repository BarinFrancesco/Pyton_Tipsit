

import cv2
import numpy as np


# costanti di stile
FONT        = cv2.FONT_HERSHEY_SIMPLEX
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0,   0,   0)
COLOR_GREEN = (0,   220, 80)
COLOR_RED   = (0,   0,   220)
COLOR_BLUE  = (220, 160, 0)
COLOR_YELLOW= (0,   220, 220)

#disegna testo
def _draw_text_with_shadow(frame, text, pos, font_scale=0.55, color=COLOR_WHITE,
                           thickness=1, shadow_offset=1):

    x, y = pos
    # Ombra
    cv2.putText(frame, text, (x + shadow_offset, y + shadow_offset),
                FONT, font_scale, COLOR_BLACK, thickness + 1, cv2.LINE_AA)
    # Testo principale
    cv2.putText(frame, text, (x, y),
                FONT, font_scale, color, thickness, cv2.LINE_AA)

# pannello di stato
def draw_hud(frame, info: dict):

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




#mostra scritta sopra alla faccia
def draw_label_above_face(frame, faces, label="Utente"):

    result = frame.copy()
    for (x, y, w, h) in faces:
        _draw_text_with_shadow(result, label,
                               (x, max(y - 10, 20)),
                               font_scale=0.6, color=COLOR_YELLOW, thickness=1)
    return result

# lista filtri e effetti
def draw_command_panel(frame, active_effects: dict):

    result = frame.copy()
    fh, fw = result.shape[:2]

    sections = [
        ("FILTRI COLORE", [
            ("[1]", "Originale",      None),
            ("[2]", "Scala di grigi", None),
            ("[3]", "Negativo",       None),
            ("[4]", "Sepia",          None),
            ("[5]", "Heatmap",        None),
            ("[6]", "Cartoon",        None),
            ("[7]", "Pixelate",       None),
            ("[8]", "Vignettatura",   None),
        ]),
        ("EFFETTI FACCIA", [
            ("[F]", "Box viso",    "face_rect"),
            ("[B]", "Blur sfondo", "blur_bg"),
            ("[N]", "Face swap",   "face_swap"),
            ("[H]", "Cappello",    "hat"),
        ]),
        ("EFFETTI SPECIALI", [
            ("[T]", "Ghost/scia", "ghost"),
        ]),
        ("CONTROLLI", [
            ("[M]", "Mirror",    "mirror"),
            ("[S]", "Screenshot", None),
            ("[R]", "Registra",  "recording"),
            ("[Q]", "Esci",      None),
        ]),
    ]

    # Totale righe da disegnare: 1 titolo + voci per sezione + gap tra sezioni
    total_rows = sum(1 + len(voci) for _, voci in sections) + len(sections) - 1

    START_X = 8
    START_Y = 138          # sotto HUD
    BOX_W   = 192
    PAD_X   = 8
    FILTER_BAR_H = 34      # spazio riservato alla barra filtri in basso

    # Spazio verticale disponibile
    available_h = fh - START_Y - FILTER_BAR_H - 6

    # Calcola LINE_H e font_scale in modo che tutto ci stia
    # Partiamo dal valore ideale e scaliamo verso il basso se necessario
    LINE_H     = max(14, min(19, available_h // (total_rows + 2)))
    font_scale = max(0.28, min(0.40, LINE_H / 48.0))
    title_scale = max(0.26, font_scale - 0.04)

    BOX_H = total_rows * LINE_H + LINE_H + 8   # +8 padding verticale

    # Sfondo semitrasparente
    overlay = result.copy()
    cv2.rectangle(overlay,
                  (START_X, START_Y),
                  (START_X + BOX_W, START_Y + BOX_H),
                  (15, 15, 15), -1)
    result = cv2.addWeighted(result, 0.35, overlay, 0.65, 0)
    cv2.rectangle(result,
                  (START_X, START_Y),
                  (START_X + BOX_W, START_Y + BOX_H),
                  (70, 70, 70), 1)

    cursor_y = START_Y + LINE_H

    for s_idx, (titolo, voci) in enumerate(sections):
        if s_idx > 0:
            cursor_y += max(4, LINE_H // 4)   # gap tra sezioni

        # ── Titolo sezione ────────────────────────────────────────────────────
        cv2.putText(result, f"-- {titolo} --",
                    (START_X + PAD_X, cursor_y),
                    FONT, title_scale, (150, 150, 150), 1, cv2.LINE_AA)
        cursor_y += LINE_H

        for (tasto, descrizione, stato_key) in voci:
            # Interrompi se usciamo dal pannello (sicurezza)
            if cursor_y > START_Y + BOX_H:
                break

            is_active = stato_key is not None and active_effects.get(stato_key, False)

            # Sfondo verde per voce attiva
            if is_active:
                cv2.rectangle(result,
                              (START_X + 2, cursor_y - LINE_H + 3),
                              (START_X + BOX_W - 2, cursor_y + 2),
                              (25, 95, 40), -1)

            key_col  = COLOR_GREEN  if is_active else COLOR_YELLOW
            text_col = COLOR_BLACK  if is_active else COLOR_WHITE

            # Tasto
            cv2.putText(result, tasto,
                        (START_X + PAD_X, cursor_y),
                        FONT, font_scale, key_col, 1, cv2.LINE_AA)
            # Descrizione
            cv2.putText(result, descrizione,
                        (START_X + PAD_X + 32, cursor_y),
                        FONT, font_scale, text_col, 1, cv2.LINE_AA)
            # ON badge
            if is_active:
                cv2.putText(result, "ON",
                            (START_X + BOX_W - 28, cursor_y),
                            FONT, font_scale - 0.04, (80, 255, 120), 1, cv2.LINE_AA)

            cursor_y += LINE_H

    return result


def draw_controls_overlay(frame):

    return frame
