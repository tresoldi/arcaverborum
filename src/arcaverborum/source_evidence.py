"""Source-specific distinctions between lexical text and recording placeholders."""


def is_recording_placeholder(source: str, form: str, value: str = "") -> bool:
    """Voices' play button denotes audio, not spelling or a pronunciation."""
    return source == "mixezoqueanvoices" and str(form or value).strip() == "►"
