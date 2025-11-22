"""Décodage des formats d'images biométriques spécialisés (WSQ, JPEG2000).

Ce module centralise le décodage des formats d'images utilisés dans les fichiers NIST
pour les empreintes digitales et autres données biométriques.

- WSQ : package Python `wsq` (cross-platform) avec fallback NBIS `dwsq` (plus robuste)
- JPEG2000 : utilise `imagecodecs`
"""

import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image

# Chargement du plugin WSQ pour Pillow
WSQ_AVAILABLE = False
try:
    from wsq import WsqImagePlugin  # noqa: F401 - registers the plugin
    WSQ_AVAILABLE = True
except ImportError:
    pass

# Flag indiquant si imagecodecs est disponible
IMAGECODECS_AVAILABLE = False
try:
    import imagecodecs
    IMAGECODECS_AVAILABLE = True
except ImportError:
    imagecodecs = None


def _is_macos_arm64() -> bool:
    """Vérifie si on tourne sur macOS ARM64 (Apple Silicon)."""
    import platform
    import sys
    return sys.platform == 'darwin' and platform.machine() == 'arm64'


def _decode_wsq_python(data: bytes) -> Tuple[Optional[Image.Image], str]:
    """Décode WSQ via le package Python wsq."""
    if not WSQ_AVAILABLE:
        return None, "Package wsq non disponible"

    # Le package wsq Python a un bug connu qui cause un segfault sur macOS ARM64
    # Voir: https://github.com/mgeier/wsq/issues - crash dans wsq_decode_mem
    if _is_macos_arm64():
        return None, "Package wsq désactivé sur macOS ARM64 (bug segfault connu)"

    try:
        img = Image.open(BytesIO(data))
        img.load()
        return img, ""
    except Exception as e:
        return None, f"wsq Python: {str(e)}"


def _find_dwsq() -> Optional[str]:
    """Trouve l'exécutable dwsq (bundled ou système)."""
    import sys

    # 1. Chercher dans le bundle PyInstaller
    if getattr(sys, 'frozen', False):
        # Application packagée
        bundle_dir = Path(sys._MEIPASS)  # type: ignore

        if sys.platform == 'win32':
            dwsq_name = 'dwsq.exe'
        else:
            dwsq_name = 'dwsq'

        # Chemins possibles selon le type de packaging
        possible_paths = [
            bundle_dir / 'nbis' / 'bin' / dwsq_name,  # onefolder standard
        ]

        # Pour macOS .app bundle, les ressources peuvent être dans Contents/Resources
        if sys.platform == 'darwin':
            # Si _MEIPASS est dans Contents/Frameworks ou Contents/MacOS
            contents_dir = bundle_dir.parent
            if contents_dir.name in ('Frameworks', 'MacOS'):
                resources_dir = contents_dir.parent / 'Resources'
                possible_paths.append(resources_dir / 'nbis' / 'bin' / dwsq_name)
            # Aussi essayer directement dans _MEIPASS (onefolder classique)
            possible_paths.append(bundle_dir / 'nbis' / 'bin' / dwsq_name)

        for path in possible_paths:
            if path.exists():
                return str(path)

    # 2. Chercher à côté du script (dev mode)
    script_dir = Path(__file__).parent.parent.parent
    if sys.platform == 'win32':
        local = script_dir / 'nbis' / 'bin' / 'dwsq.exe'
    else:
        local = script_dir / 'nbis' / 'bin' / 'dwsq'
    if local.exists():
        return str(local)

    # 3. Chercher dans le PATH système
    return shutil.which("dwsq")


def _decode_wsq_nbis(data: bytes) -> Tuple[Optional[Image.Image], str]:
    """Décode WSQ via l'outil NBIS dwsq (plus robuste pour certains fichiers)."""
    dwsq_path = _find_dwsq()
    if not dwsq_path:
        return None, "NBIS dwsq non disponible"

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
                return None, f"dwsq: {stderr or 'erreur inconnue'}"

            raw_file = wsq_file.with_suffix(".raw")
            ncm_file = wsq_file.with_suffix(".ncm")

            if not raw_file.exists() or not ncm_file.exists():
                return None, "Fichiers de sortie dwsq introuvables"

            meta = {}
            for line in ncm_file.read_text().splitlines():
                if " " in line:
                    k, v = line.split(None, 1)
                    meta[k] = v

            width = int(meta.get("PIX_WIDTH", 0))
            height = int(meta.get("PIX_HEIGHT", 0))
            depth = int(meta.get("PIX_DEPTH", 8))

            if not width or not height:
                return None, "Métadonnées WSQ invalides"

            raw_bytes = raw_file.read_bytes()
            mode = "L" if depth <= 8 else "RGB"
            img = Image.frombytes(mode, (width, height), raw_bytes)
            return img, ""

    except Exception as e:
        return None, f"dwsq: {str(e)}"


def decode_wsq(data: bytes) -> Tuple[Optional[Image.Image], str]:
    """Décode une image WSQ (Wavelet Scalar Quantization).

    WSQ est le format de compression standard pour les empreintes digitales,
    utilisé par le FBI et les forces de l'ordre internationales.

    Stratégie : essaie d'abord NBIS dwsq (plus robuste, évite les segfaults),
    puis fallback sur le package Python wsq.

    Args:
        data: Données binaires WSQ

    Returns:
        Tuple (image PIL, message d'erreur).
        Si succès: (Image, "")
        Si échec: (None, description de l'erreur)
    """
    errors = []

    # 1. Essayer NBIS dwsq d'abord (plus robuste, évite les segfaults du package Python)
    img, err = _decode_wsq_nbis(data)
    if img:
        return img, ""
    if err and "non disponible" not in err:
        errors.append(err)

    # 2. Fallback sur le package Python wsq
    img, err = _decode_wsq_python(data)
    if img:
        return img, ""
    if err and "non disponible" not in err:
        errors.append(err)

    # Aucun décodeur n'a fonctionné
    if not WSQ_AVAILABLE and not _find_dwsq():
        return None, "Aucun décodeur WSQ disponible. Installez wsq (pip install wsq) ou NBIS."

    return None, f"Échec décodage WSQ: {'; '.join(errors)}"


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
