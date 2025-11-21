"""Décodage des formats d'images biométriques spécialisés (WSQ, JPEG2000).

Ce module centralise le décodage des formats d'images utilisés dans les fichiers NIST
pour les empreintes digitales et autres données biométriques.

- WSQ : utilise l'outil externe NBIS `dwsq` (plus stable que la lib Python)
- JPEG2000 : utilise `imagecodecs`
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image

# Flag indiquant si imagecodecs est disponible
IMAGECODECS_AVAILABLE = False

try:
    import imagecodecs
    IMAGECODECS_AVAILABLE = True
except ImportError:
    imagecodecs = None


def decode_wsq(data: bytes) -> Tuple[Optional[Image.Image], str]:
    """Décode une image WSQ (Wavelet Scalar Quantization).

    WSQ est le format de compression standard pour les empreintes digitales,
    utilisé par le FBI et les forces de l'ordre internationales.

    Utilise l'outil NBIS `dwsq` via subprocess pour éviter les crashs
    de la bibliothèque Python wsq sur certaines plateformes.

    Args:
        data: Données binaires WSQ

    Returns:
        Tuple (image PIL, message d'erreur).
        Si succès: (Image, "")
        Si échec: (None, description de l'erreur)
    """
    dwsq_path = shutil.which("dwsq")
    if not dwsq_path:
        return None, (
            "Outil NBIS 'dwsq' non trouvé dans le PATH.\n"
            "Installez NBIS depuis: https://www.nist.gov/itl/iad/image-group/products-and-services/image-group-open-source-server-nigos"
        )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            wsq_file = tmp_dir / "image.wsq"
            wsq_file.write_bytes(data)

            result = subprocess.run(
                [dwsq_path, "raw", str(wsq_file), "-raw_out"],
                capture_output=True,
                check=False,
            )

            if result.returncode != 0:
                stderr = result.stderr.decode(errors="ignore").strip()
                return None, f"dwsq a échoué: {stderr or 'erreur inconnue'}"

            raw_file = wsq_file.with_suffix(".raw")
            ncm_file = wsq_file.with_suffix(".ncm")

            if not raw_file.exists() or not ncm_file.exists():
                return None, "Fichiers de sortie dwsq introuvables"

            # Parse metadata
            meta = {}
            for line in ncm_file.read_text().splitlines():
                if " " in line:
                    k, v = line.split(None, 1)
                    meta[k] = v

            width = int(meta.get("PIX_WIDTH", 0))
            height = int(meta.get("PIX_HEIGHT", 0))
            depth = int(meta.get("PIX_DEPTH", 8))

            if not width or not height:
                return None, "Métadonnées WSQ invalides (dimensions manquantes)"

            raw_bytes = raw_file.read_bytes()
            mode = "L" if depth <= 8 else "RGB"
            img = Image.frombytes(mode, (width, height), raw_bytes)
            return img, ""

    except Exception as e:
        return None, f"Erreur de décodage WSQ: {str(e)}"


def decode_jpeg2000(data: bytes) -> Tuple[Optional[Image.Image], str]:
    """Décode une image JPEG2000.

    JPEG2000 est parfois utilisé dans les fichiers NIST comme alternative
    à WSQ pour les images biométriques.

    Args:
        data: Données binaires JPEG2000

    Returns:
        Tuple (image PIL, message d'erreur).
        Si succès: (Image, "")
        Si échec: (None, description de l'erreur)
    """
    if not IMAGECODECS_AVAILABLE:
        return None, "imagecodecs non installé. Installez avec: pip install imagecodecs"

    try:
        arr = imagecodecs.jpeg2k_decode(data)
        return Image.fromarray(arr), ""
    except Exception as e:
        return None, f"Erreur de décodage JPEG2000: {str(e)}"


def is_codec_available() -> bool:
    """Vérifie si les codecs sont disponibles.

    Returns:
        True si imagecodecs est installé et fonctionnel.
    """
    return IMAGECODECS_AVAILABLE
