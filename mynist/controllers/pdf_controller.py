"""Contrôleur pour l'export PDF décadactylaire (rapport 10 empreintes)."""

from io import BytesIO
from typing import List, Tuple, Dict, Optional

from PIL import Image, ImageDraw, ImageFont

from mynist.models.nist_file import NISTFile
from mynist.utils.image_tools import locate_image_payload, exif_transpose, detect_image_format
from mynist.utils.image_codecs import decode_wsq, decode_jpeg2000


class PDFController:
    """Génère un PDF A4 avec les empreintes et quelques métadonnées."""

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def export_dacty_pdf(self, nist_file: NISTFile, output_path: str) -> Tuple[bool, str]:
        """Exporte un PDF décadactylaire organisé (pouces/main gauche/main droite + simultanés + paumes).

        Args:
            nist_file: fichier NIST déjà parsé.
            output_path: chemin de sortie du PDF.

        Returns:
            (succes, message) ; message vide si succès.
        """
        buckets = self._collect_images(nist_file)
        if not buckets:
            return False, "Aucune image (Type-14/4/10/7/15) n'a été détectée dans ce fichier."

        metadata = self._collect_metadata(nist_file)

        try:
            # Génération via Pillow en A4 (300 DPI par défaut)
            dpi = self.dpi
            page_w = int(8.27 * dpi)  # 210mm
            page_h = int(11.69 * dpi)  # 297mm

            page = Image.new("RGB", (page_w, page_h), "white")
            draw = ImageDraw.Draw(page)
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
            draw.text((80, 40), "Relevé décadactylaire", fill="black", font=font_title)
            draw.text((80, 70), f"TCN : {metadata.get('TCN', 'N/A')}", fill="black", font=font_body)
            draw.text((80, 90), f"ORI : {metadata.get('ORI', 'N/A')}", fill="black", font=font_body)
            draw.text((80, 110), f"Date : {metadata.get('DATE', 'N/A')}", fill="black", font=font_body)
            draw.text((80, 130), f"Sujet : {metadata.get('NAME', 'N/A')}", fill="black", font=font_body)

            # Layout spécifique : colonnes 2x5 pour les doigts (gauche puis droite),
            # suivi d'une rangée simultanés et paumes.
            margin_x, margin_y = 60, 170
            cell_w = int((page_w - 2 * margin_x) / 2)
            cell_h = int((page_h - margin_y - 200) / 5)

            def paste_slot(img_info, col, row):
                x = margin_x + col * cell_w
                y = margin_y + row * cell_h
                pil_img = img_info["image"].convert("RGB")
                max_w = cell_w - 20
                max_h = cell_h - 40
                img_w, img_h = pil_img.size
                scale = min(max_w / img_w, max_h / img_h)
                new_size = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))
                resized = pil_img.resize(new_size)
                paste_x = x + int((max_w - new_size[0]) / 2) + 10
                paste_y = y + 20
                page.paste(resized, (paste_x, paste_y))
                label = img_info["label"]
                draw.text((x + 10, y + max_h + 20), label, fill="black", font=font_body)

            # Doigts main gauche (P I M A O)
            for idx, key in enumerate(["LG_P", "LG_I", "LG_M", "LG_A", "LG_O"]):
                if buckets.get(key):
                    paste_slot(buckets[key][0], 0, idx)
            # Doigts main droite (P I M A O)
            for idx, key in enumerate(["RD_P", "RD_I", "RD_M", "RD_A", "RD_O"]):
                if buckets.get(key):
                    paste_slot(buckets[key][0], 1, idx)

            # Ligne simultanés (colonne gauche/droite)
            base_y = margin_y + 5 * cell_h
            sim_labels = ["SIM_MAIN_GAUCHE", "SIM_POUCES", "SIM_MAIN_DROITE"]
            for i, key in enumerate(sim_labels):
                if key in buckets:
                    img_info = buckets[key][0]
                    pil_img = img_info["image"].convert("RGB")
                    max_w = int((page_w - 2 * margin_x) / 3) - 20
                    max_h = 180
                    img_w, img_h = pil_img.size
                    scale = min(max_w / img_w, max_h / img_h)
                    new_size = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))
                    resized = pil_img.resize(new_size)
                    start_x = margin_x + i * (max_w + 20)
                    paste_x = start_x + int((max_w - new_size[0]) / 2)
                    paste_y = base_y + 20
                    page.paste(resized, (paste_x, paste_y))
                    draw.text((start_x + 5, base_y + max_h + 30), img_info["label"], fill="black", font=font_body)

            # Paumes
            base_y2 = base_y + 230
            for i, key in enumerate(["PAUME_GAUCHE", "PAUME_DROITE"]):
                if key in buckets:
                    img_info = buckets[key][0]
                    pil_img = img_info["image"].convert("RGB")
                    max_w = int((page_w - 2 * margin_x) / 2) - 20
                    max_h = 220
                    img_w, img_h = pil_img.size
                    scale = min(max_w / img_w, max_h / img_h)
                    new_size = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))
                    resized = pil_img.resize(new_size)
                    start_x = margin_x + i * (max_w + 20)
                    paste_x = start_x + int((max_w - new_size[0]) / 2)
                    paste_y = base_y2 + 20
                    page.paste(resized, (paste_x, paste_y))
                    draw.text((start_x + 5, base_y2 + max_h + 30), img_info["label"], fill="black", font=font_body)

            # Extras non mappés : placer en bandeau sous les paumes
            extras = buckets.get("EXTRA", [])
            if extras:
                extra_y = base_y2 + 260
                max_w = int((page_w - 2 * margin_x) / 3) - 20
                max_h = 180
                for i, img_info in enumerate(extras[:3]):
                    pil_img = img_info["image"].convert("RGB")
                    img_w, img_h = pil_img.size
                    scale = min(max_w / img_w, max_h / img_h)
                    new_size = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))
                    resized = pil_img.resize(new_size)
                    start_x = margin_x + i * (max_w + 20)
                    paste_x = start_x + int((max_w - new_size[0]) / 2)
                    paste_y = extra_y + 10
                    page.paste(resized, (paste_x, paste_y))
                    draw.text((start_x + 5, extra_y + max_h + 20), img_info["label"], fill="black", font=font_body)

            page.save(output_path, "PDF", resolution=dpi)
            return True, ""
        except Exception as exc:  # pragma: no cover
            return False, f"Erreur lors de la génération du PDF : {exc}"

    def _collect_metadata(self, nist_file: NISTFile) -> Dict[str, str]:
        """Récupère des métadonnées basiques depuis Type-1/2."""
        meta = {"TCN": "", "ORI": "", "DATE": "", "NAME": ""}
        try:
            type2_records = nist_file.get_records_by_type(2)
            if type2_records:
                _, rec = type2_records[0]
                meta["TCN"] = self._first(rec, ["_009", "_007", "TCN"]) or ""
                meta["ORI"] = self._first(rec, ["_008", "ORI"]) or ""
                meta["DATE"] = self._first(rec, ["_019", "_018"]) or ""
                name_parts = [self._first(rec, ["_030"]) or "", self._first(rec, ["_031"]) or ""]
                meta["NAME"] = " ".join(p for p in name_parts if p).strip()
        except Exception:
            pass
        return meta

    def _collect_images(self, nist_file: NISTFile) -> Dict[str, List[Dict[str, object]]]:
        """Collecte les images et les range dans des buckets (gauche/droite/simultané/paume)."""
        buckets: Dict[str, List[Dict[str, object]]] = {}
        for rtype in (14, 4, 10, 7, 15):
            for idc, record in nist_file.get_records_by_type(rtype):
                pil_img, fmt = self._record_to_image(record)
                if not pil_img:
                    continue
                pos = self._deduce_position(record, rtype, idc)
                label = pos if pos else f"Type-{rtype} IDC {idc}"
                entry = {"image": pil_img, "idc": idc, "type": rtype, "format": fmt, "label": label}
                buckets.setdefault(pos or "EXTRA", []).append(entry)
        return buckets

    def _record_to_image(self, record) -> Tuple[Optional[Image.Image], str]:
        """Convertit un record en PIL Image."""
        data = None
        for attr in ("_999", "_009", "DATA", "data", "image", "Image", "BDB", "value"):
            try:
                val = getattr(record, attr, None)
                if val and isinstance(val, (bytes, bytearray)):
                    data = bytes(val)
                    break
            except Exception:
                continue

        if not data:
            return None, ""

        payload, fmt = locate_image_payload(data)

        if fmt == "WSQ":
            img, _ = decode_wsq(payload)
            if img:
                return img, fmt
            return None, fmt

        if fmt == "JPEG2000":
            img, _ = decode_jpeg2000(payload)
            if img:
                return exif_transpose(img), fmt
            return None, fmt

        try:
            img = Image.open(BytesIO(payload))
            img = exif_transpose(img)
            return img, detect_image_format(payload)
        except Exception:
            return None, fmt

    def _deduce_position(self, record, record_type: int, idc: int) -> str:
        """Déduit une étiquette de position à partir des champs FGP/IMP ou IDC."""
        # Positions côté NIST : 1-10 doigts; 11-14 paumes, 20 pouces simultanés.
        fgp = self._first(record, ["FGP", "_004"])
        try:
            fgp_int = int(fgp) if fgp is not None else None
        except Exception:
            fgp_int = None

        if record_type == 15:
            if fgp_int in (20, 21, 22, 23):
                return "PAUME_GAUCHE"
            if fgp_int in (24, 25, 26, 27):
                return "PAUME_DROITE"
            return "PAUME"

        mapping = {
            1: "RD_P",
            2: "RD_I",
            3: "RD_M",
            4: "RD_A",
            5: "RD_O",
            6: "LG_P",
            7: "LG_I",
            8: "LG_M",
            9: "LG_A",
            10: "LG_O",
            13: "SIM_MAIN_GAUCHE",
            14: "SIM_MAIN_DROITE",
            15: "SIM_POUCES",
        }
        if fgp_int in mapping:
            return mapping[fgp_int]
        # fallback: utiliser l'IDC pour ordonner
        if record_type in (10, 7) and idc is not None:
            # IDC 0 -> gauche, IDC 1 -> droite en fallback rudimentaire
            return "LG_DIVERS" if idc == 0 else "RD_DIVERS"
        return ""

    def _first(self, record, candidates) -> Optional[str]:
        for name in candidates:
            try:
                val = getattr(record, name, None)
                if val not in (None, ""):
                    return str(val)
            except Exception:
                continue
        return None
