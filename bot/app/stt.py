# ############################################################################
# AI_HEADER: MODULE_BOT_STT
# ROLE: Local speech-to-text helper for voice tasks.
# DEPENDENCIES: faster_whisper.
# GRACE_ANCHORS: [BOT_STT]
# ############################################################################

import os
from typing import Optional

import structlog
from faster_whisper import WhisperModel

logger = structlog.get_logger()

_MODEL: Optional[WhisperModel] = None


def _load_model() -> WhisperModel:
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    model_name = os.getenv("WHISPER_MODEL", "base")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    _MODEL = WhisperModel(model_name, device=device, compute_type=compute_type)
    logger.info("bot.stt.model_ready", model=model_name, device=device)
    return _MODEL


def transcribe_audio(path: str) -> str:
    model = _load_model()
    language = os.getenv("WHISPER_LANGUAGE", "ru")
    beam_size_raw = os.getenv("WHISPER_BEAM_SIZE", "5")
    try:
        beam_size = int(beam_size_raw)
    except ValueError:
        beam_size = 5

    segments, _ = model.transcribe(path, language=language, beam_size=beam_size)
    parts = []
    for segment in segments:
        if segment.text:
            parts.append(segment.text.strip())
    return " ".join(parts).strip()
