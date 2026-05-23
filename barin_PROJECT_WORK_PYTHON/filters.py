"""
filters.py - Filtri colore applicabili al frame webcam.

Ogni funzione:
  - Riceve il frame BGR come primo parametro
  - Restituisce il frame modificato (BGR)
  - Non modifica l'originale (lavora su copia)
  - Ha un commento che spiega brevemente cosa fa
"""

import cv2
import numpy as np


def apply_original(frame):
    """Restituisce il frame senza alcuna modifica."""
    return frame.copy()


def apply_grayscale(frame):
    """Converte in scala di grigi e riconverte in BGR per uniformità."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def apply_negative(frame):
    """Inverte tutti i valori dei pixel (255 - valore originale)."""
    return cv2.bitwise_not(frame.copy())


def apply_sepia(frame):
    """
    Applica l'effetto seppia classico tramite una matrice di trasformazione
    che sposta i canali BGR verso tonalità calde marroni/giallastre.
    """
    img = frame.copy().astype(np.float64)
    # Matrice seppia (righe = BGR output, colonne = BGR input)
    kernel = np.array([
        [0.272, 0.534, 0.131],   # B output
        [0.349, 0.686, 0.168],   # G output
        [0.393, 0.769, 0.189],   # R output
    ])
    sepia = cv2.transform(img, kernel)
    sepia = np.clip(sepia, 0, 255).astype(np.uint8)
    return sepia


def apply_heatmap(frame):
    """
    Converte in scala di grigi e applica la colormap JET di OpenCV,
    simulando un effetto termico con colori dal blu (freddo) al rosso (caldo).
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.applyColorMap(gray, cv2.COLORMAP_JET)


def apply_cartoon(frame):
    """
    Effetto fumetto: bilateral filter ripetuto per appiattire i colori,
    poi bordi Canny sovrapposti in nero per simulare il tratto del disegno.
    """
    img = frame.copy()

    # Appiattimento colori con bilateral filter (ripetuto per effetto più forte)
    for _ in range(5):
        img = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

    # Estrazione bordi
    gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    # Sovrappone i bordi neri all'immagine appiattita
    cartoon = cv2.bitwise_and(img, cv2.bitwise_not(edges))
    return cartoon


def apply_pixelate(frame, pixel_size=16):
    """
    Effetto pixel art: rimpicciolisce il frame e lo riingrandisce con
    interpolazione NEAREST per ottenere blocchi di pixel visibili.
    """
    h, w = frame.shape[:2]
    small = cv2.resize(frame, (w // pixel_size, h // pixel_size),
                       interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def apply_vignette(frame):
    """
    Vignettatura: scurisce progressivamente i bordi del frame usando
    una maschera gaussiana circolare costruita con NumPy.
    """
    img = frame.copy()
    h, w = img.shape[:2]

    # Maschera gaussiana su X e su Y, poi prodotto esterno
    sigma_x = w / 2
    sigma_y = h / 2
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    gauss_x = np.exp(-x**2 / (2 * (sigma_x / w)**2 + 0.4))
    gauss_y = np.exp(-y**2 / (2 * (sigma_y / h)**2 + 0.4))
    mask = np.outer(gauss_y, gauss_x)
    mask = (mask / mask.max())  # normalizza [0, 1]

    # Applica la maschera a ogni canale
    for c in range(3):
        img[:, :, c] = (img[:, :, c] * mask).astype(np.uint8)
    return img


def apply_solarize(frame, threshold=128):
    """
    Solarizzazione: inverte i pixel il cui valore supera la soglia,
    creando un effetto surreale simile all'omonimo effetto fotografico.
    """
    img = frame.copy()
    mask = img >= threshold
    img[mask] = 255 - img[mask]
    return img
