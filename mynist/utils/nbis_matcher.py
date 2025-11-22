"""Intégration minimale de NBIS (mindtct + bozorth3) pour l'auto-match empreintes.

Ce module appelle les binaires NBIS via subprocess. Il suppose que `mindtct` et
`bozorth3` sont soit dans le PATH, soit dans un dossier `nbis/` à la racine du
projet (embarquable dans PyInstaller).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image


def _platform_exe(name: str) -> str:
    return f"{name}.exe" if os.name == "nt" else name


def _find_tool(name: str) -> Optional[Path]:
    """Cherche l'exécutable dans PATH, dans ./nbis/ (dev) ou dans les datas PyInstaller."""
    exe = _platform_exe(name)

    path = shutil.which(exe)
    if path:
        return Path(path)

    candidates = []

    # Dev : racine du projet
    base = Path(__file__).resolve().parents[2]
    candidates.extend([base / "nbis" / exe, base / "nbis" / "bin" / exe])

    # PyInstaller : dossier d'extraction (_MEIPASS)
    meipass = Path(getattr(sys, "_MEIPASS", "")) if hasattr(sys, "_MEIPASS") else None
    if meipass and meipass.exists():
        candidates.extend([meipass / "nbis" / exe, meipass / "nbis" / "bin" / exe])

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@dataclass
class NBISMatchPair:
    left: Tuple[float, float]
    right: Tuple[float, float]


@dataclass
class NBISMatchResult:
    ok: bool
    message: str = ""
    score: Optional[int] = None
    pairs: List[NBISMatchPair] = field(default_factory=list)
    minutiae_left: List[Tuple[float, float]] = field(default_factory=list)
    minutiae_right: List[Tuple[float, float]] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _run_mindtct(img: Image.Image, out_base: Path, dpi: Optional[float] = None):
    """Exécute mindtct sur une image PIL enregistrée en PNG."""
    mindtct_path = _find_tool("mindtct")
    if not mindtct_path:
        return None, [], "mindtct introuvable (PATH ou dossier nbis/)."

    # mindtct attend un fichier, on enregistre en PNG 8 bits
    png_path = out_base.with_suffix(".png")
    img.convert("L").save(png_path)

    cmd = [str(mindtct_path), str(png_path), str(out_base)]
    # Si DPI fourni, on tente de le passer (option -r), ignoré sinon
    if dpi:
        cmd.insert(1, "-r")
        cmd.insert(2, str(int(dpi)))

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or proc.stdout or "").strip()
        return None, [], f"mindtct a échoué ({proc.returncode}): {stderr}"

    xyt_path = out_base.with_suffix(".xyt")
    if not xyt_path.exists():
        return None, [], "Sortie .xyt introuvable après mindtct."

    minutiae = []
    try:
        for line in xyt_path.read_text().splitlines():
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            x, y = float(parts[0]), float(parts[1])
            minutiae.append((x, y))
    except Exception:
        pass

    return xyt_path, minutiae, ""


def _run_bozorth3(xyt_left: Path, xyt_right: Path):
    """Exécute bozorth3 et retourne le score (int) ou un message d'erreur."""
    bozorth_path = _find_tool("bozorth3")
    if not bozorth_path:
        return None, "bozorth3 introuvable (PATH ou dossier nbis/).", {}

    cmd = [str(bozorth_path), str(xyt_left), str(xyt_right)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = (proc.stderr or proc.stdout or "").strip()
        return None, f"bozorth3 a échoué ({proc.returncode}): {stderr}", {}

    stdout = (proc.stdout or "").strip()
    score = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            score = int(float(line.split()[0]))
            break
        except Exception:
            continue

    if score is None:
        return None, f"Score introuvable dans la sortie bozorth3: {stdout}", {}

    return score, "", {"stdout": stdout}


def nbis_auto_match(
    left_img: Image.Image,
    right_img: Image.Image,
    dpi_left: Optional[float] = None,
    dpi_right: Optional[float] = None,
) -> NBISMatchResult:
    """Pipeline complet : mindtct gauche/droite puis bozorth3."""
    # Vérifier les outils
    if not _find_tool("mindtct") or not _find_tool("bozorth3"):
        return NBISMatchResult(ok=False, message="NBIS introuvable : placez mindtct/bozorth3 dans le PATH ou le dossier nbis/.")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        lxyt, lmin, err = _run_mindtct(left_img, tmp / "left", dpi_left)
        if err:
            return NBISMatchResult(ok=False, message=err)
        rxyt, rmin, err = _run_mindtct(right_img, tmp / "right", dpi_right)
        if err:
            return NBISMatchResult(ok=False, message=err)
        if lxyt is None or rxyt is None:
            return NBISMatchResult(ok=False, message="Minuties non générées par mindtct.")

        score, err, stats = _run_bozorth3(lxyt, rxyt)
        if err:
            return NBISMatchResult(ok=False, message=err, minutiae_left=lmin, minutiae_right=rmin, stats=stats)

        return NBISMatchResult(
            ok=True,
            score=score,
            minutiae_left=lmin,
            minutiae_right=rmin,
            stats={"score_raw": score, **stats},
        )
