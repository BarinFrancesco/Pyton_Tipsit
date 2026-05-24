

import cv2
import numpy as np

#restituisce il frame senza niente
def apply_original(frame):
    return frame.copy()

#applica scala di grigi
def apply_grayscale(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

#applica negativo
def apply_negative(frame):

    return cv2.bitwise_not(frame.copy())

#applica effetto seppia
def apply_sepia(frame):

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

#applica effetto temperatura, usa la scala di grici con un'altra colormap
def apply_heatmap(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.applyColorMap(gray, cv2.COLORMAP_JET)

#effetto cartoon
def apply_cartoon(frame):
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

#effetto pixelato
def apply_pixelate(frame, pixel_size=16):

    h, w = frame.shape[:2]
    small = cv2.resize(frame, (w // pixel_size, h // pixel_size),
                       interpolation=cv2.INTER_LINEAR)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

#applica vignetta
def apply_vignette(frame):

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
