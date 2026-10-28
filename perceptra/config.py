"""Local paths and resource configuration; no directories are created on import."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"
NLTK_DATA_DIR = VENV_DIR / "nltk_data"
NLTK_RESOURCES = {
    "punkt_tab": "tokenizers/punkt_tab/english/",
    "averaged_perceptron_tagger_eng": "taggers/averaged_perceptron_tagger_eng/",
    "stopwords": "corpora/stopwords",
}


def data_dir(override: str | Path | None = None) -> Path:
    value = Path(override or os.environ.get("PERCEPTRA_DATA_DIR", "data"))
    return value if value.is_absolute() else PROJECT_ROOT / value


def configure_nltk() -> None:
    """Restrict NLTK to the project virtual environment's resource directory."""
    import nltk

    nltk.data.path[:] = [str(NLTK_DATA_DIR)]


def check_nltk_resources() -> None:
    import nltk

    configure_nltk()
    missing = []
    for name, resource_path in NLTK_RESOURCES.items():
        try:
            nltk.data.find(resource_path)
        except LookupError:
            missing.append(name)
    if missing:
        raise LookupError(
            f"Missing NLTK resources in {NLTK_DATA_DIR}: {', '.join(missing)}. "
            "Run .venv\\Scripts\\python.exe scripts/prepare_demo_data.py --prepare-nltk. "
            "Inference never downloads resources automatically."
        )
