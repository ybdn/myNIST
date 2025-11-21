"""Tests pour le module de décodage d'images biométriques (WSQ, JPEG2000)."""

import pytest

from mynist.utils.image_codecs import (
    decode_wsq,
    decode_jpeg2000,
    is_codec_available,
    IMAGECODECS_AVAILABLE,
)


class TestCodecAvailability:
    """Tests pour la disponibilité des codecs."""

    def test_is_codec_available_returns_bool(self):
        """is_codec_available retourne un booléen."""
        result = is_codec_available()
        assert isinstance(result, bool)

    def test_imagecodecs_flag_matches_function(self):
        """Le flag IMAGECODECS_AVAILABLE correspond à is_codec_available()."""
        assert IMAGECODECS_AVAILABLE == is_codec_available()


class TestDecodeWSQ:
    """Tests pour le décodage WSQ."""

    def test_decode_wsq_invalid_data_returns_error(self):
        """Des données invalides retournent une erreur."""
        img, err = decode_wsq(b"not valid wsq data")
        if IMAGECODECS_AVAILABLE:
            # Si imagecodecs est installé, on attend une erreur de décodage
            assert img is None
            assert err != ""
        else:
            # Si imagecodecs n'est pas installé, message spécifique
            assert img is None
            assert "imagecodecs" in err.lower()

    def test_decode_wsq_empty_data_returns_error(self):
        """Des données vides retournent une erreur."""
        img, err = decode_wsq(b"")
        assert img is None
        assert err != ""

    def test_decode_wsq_returns_tuple(self):
        """decode_wsq retourne toujours un tuple (image, erreur)."""
        result = decode_wsq(b"test")
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestDecodeJPEG2000:
    """Tests pour le décodage JPEG2000."""

    def test_decode_jpeg2000_invalid_data_returns_error(self):
        """Des données invalides retournent une erreur."""
        img, err = decode_jpeg2000(b"not valid jp2 data")
        if IMAGECODECS_AVAILABLE:
            # Si imagecodecs est installé, on attend une erreur de décodage
            assert img is None
            assert err != ""
        else:
            # Si imagecodecs n'est pas installé, message spécifique
            assert img is None
            assert "imagecodecs" in err.lower()

    def test_decode_jpeg2000_empty_data_returns_error(self):
        """Des données vides retournent une erreur."""
        img, err = decode_jpeg2000(b"")
        assert img is None
        assert err != ""

    def test_decode_jpeg2000_returns_tuple(self):
        """decode_jpeg2000 retourne toujours un tuple (image, erreur)."""
        result = decode_jpeg2000(b"test")
        assert isinstance(result, tuple)
        assert len(result) == 2


@pytest.mark.skipif(not IMAGECODECS_AVAILABLE, reason="imagecodecs non installé")
class TestWithImagecodecs:
    """Tests nécessitant imagecodecs installé."""

    def test_decode_wsq_signature_detection(self):
        """WSQ avec signature valide mais données tronquées retourne erreur."""
        # Signature WSQ valide mais données incomplètes
        wsq_header = b"\xff\xa0\xff\xa8\x00\x02"
        img, err = decode_wsq(wsq_header)
        assert img is None
        assert err != ""

    def test_decode_jpeg2000_signature_detection(self):
        """JPEG2000 avec signature valide mais données tronquées retourne erreur."""
        # Signature JP2 valide mais données incomplètes
        jp2_header = b"\x00\x00\x00\x0cjP  \r\n\x87\n"
        img, err = decode_jpeg2000(jp2_header)
        assert img is None
        assert err != ""
