"""
main.py - Loop principale dell'applicazione webcam.
Gestisce l'acquisizione video, i tasti della tastiera e l'orchestrazione
di filtri, effetti e HUD.
"""

import cv2
import time
import filters
import effects
import ui

# ─── Configurazione ────────────────────────────────────────────────────────────
CAMERA_INDEX = 0          # Indice della webcam (0 = webcam di default)
WINDOW_NAME  = "Webcam Filtri"

# Mappa tasto → (nome filtro, funzione)
FILTER_MAP = {
    ord('1'): ("Originale",    filters.apply_original),
    ord('2'): ("Scala di grigi", filters.apply_grayscale),
    ord('3'): ("Negativo",     filters.apply_negative),
    ord('4'): ("Sepia",        filters.apply_sepia),
    ord('5'): ("Heatmap",      filters.apply_heatmap),
    ord('6'): ("Cartoon",      filters.apply_cartoon),
    ord('7'): ("Pixelate",     filters.apply_pixelate),
    ord('8'): ("Vignetta",     filters.apply_vignette),
}

# ─── Stato applicazione ────────────────────────────────────────────────────────
current_filter_name = "Originale"
current_filter_fn   = filters.apply_original
face_rect_active    = False   # Tasto F: rettangoli verdi sui visi
blur_bg_active      = False   # Tasto B: blur sfondo (richiede face detection)
face_swap_active    = False   # Tasto N: sostituisce il viso con New_Face.jpg
mirror_active       = False   # Tasto M: flip specchio
recording           = False   # Tasto R: registrazione video
video_writer        = None

# Variabili per calcolo FPS
fps         = 0.0
frame_count = 0
fps_timer   = time.time()

# Haar cascade per face detection
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def init_video_writer(frame):
    """Crea un VideoWriter per registrare il feed con filtri applicati."""
    h, w = frame.shape[:2]
    filename = time.strftime("rec_%Y%m%d_%H%M%S.mp4")
    fourcc   = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(filename, fourcc, 20.0, (w, h)), filename


def main():
    global current_filter_name, current_filter_fn
    global face_rect_active, blur_bg_active, face_swap_active
    global mirror_active
    global recording, video_writer
    global fps, frame_count, fps_timer

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Errore: impossibile aprire la webcam.")
        return

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    print("Webcam avviata. Premi Q per uscire.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Errore: frame non ricevuto.")
            break

        # ── Calcolo FPS ──────────────────────────────────────────────────────
        frame_count += 1
        elapsed = time.time() - fps_timer
        if elapsed >= 1.0:
            fps        = frame_count / elapsed
            frame_count = 0
            fps_timer  = time.time()

        # ── Flip specchio ────────────────────────────────────────────────────
        if mirror_active:
            frame = cv2.flip(frame, 1)

        # ── Face detection (usata da più effetti) ────────────────────────────
        gray_for_det = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces        = face_cascade.detectMultiScale(
            gray_for_det, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

        # ── Blur sfondo ──────────────────────────────────────────────────────
        if blur_bg_active:
            frame = effects.apply_background_blur(frame, faces)

        # ── Face swap (New_Face.jpg) ──────────────────────────────────────────
        if face_swap_active:
            frame = effects.apply_face_swap(frame, faces)

        # ── Rettangoli verdi sui visi (sopra tutto, ben visibile) ─────────────
        if face_rect_active:
            frame = effects.draw_face_rectangles(frame, faces)

        # ── Filtro colore attivo ──────────────────────────────────────────────
        frame = current_filter_fn(frame)

        # ── HUD sovrimpresso ─────────────────────────────────────────────────
        hud_info = {
            "filter":    current_filter_name,
            "faces":     len(faces),
            "fps":       fps,
            "recording": recording,
            "mirror":    mirror_active,
            "blur_bg":   blur_bg_active,
            "face_rect": face_rect_active,
            "face_swap": face_swap_active,
        }
        frame = ui.draw_hud(frame, hud_info)
        #frame = ui.draw_filter_bar(frame, list(FILTER_MAP.values()), current_filter_name)

        # ── Pannello comandi laterale sinistro ────────────────────────────────
        active_effects = {
            "face_rect": face_rect_active,
            "blur_bg":   blur_bg_active,
            "face_swap": face_swap_active,
            "mirror":    mirror_active,
            "recording": recording,
        }
        frame = ui.draw_command_panel(frame, active_effects)

        # ── Registrazione ─────────────────────────────────────────────────────
        if recording and video_writer is not None:
            video_writer.write(frame)

        cv2.imshow(WINDOW_NAME, frame)

        # ── Gestione tasti ────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == ord('Q'):
            break

        elif key in FILTER_MAP:
            current_filter_name, current_filter_fn = FILTER_MAP[key]

        elif key == ord('f') or key == ord('F'):
            face_rect_active = not face_rect_active
            print(f"Rettangoli viso: {'ON' if face_rect_active else 'OFF'}")

        elif key == ord('b') or key == ord('B'):
            blur_bg_active = not blur_bg_active
            print(f"Blur sfondo: {'ON' if blur_bg_active else 'OFF'}")

        elif key == ord('n') or key == ord('N'):
            face_swap_active = not face_swap_active
            print(f"Face swap: {'ON' if face_swap_active else 'OFF'}")

        elif key == ord('m') or key == ord('M'):
            mirror_active = not mirror_active

        elif key == ord('s') or key == ord('S'):
            filename = effects.save_screenshot(frame)
            print(f"Screenshot salvato: {filename}")

        elif key == ord('r') or key == ord('R'):
            if not recording:
                video_writer, rec_name = init_video_writer(frame)
                recording = True
                print(f"Registrazione avviata: {rec_name}")
            else:
                recording = False
                if video_writer:
                    video_writer.release()
                    video_writer = None
                print("Registrazione fermata.")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if recording and video_writer:
        video_writer.release()
    cap.release()
    cv2.destroyAllWindows()
    print("Applicazione chiusa correttamente.")


if __name__ == "__main__":
    main()
