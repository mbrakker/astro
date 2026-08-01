"""The single filesystem service for bundled tarot image assets."""

import json
import logging
from pathlib import Path
from xml.etree import ElementTree

from tarot.contracts import TarotImage, TarotImageRequest

MODULE = __name__
ROLE = "service"
DEFAULT_ASSET_ROOT = Path(__file__).parents[3] / "assets"
LOGGER = logging.getLogger(MODULE)


def _log(event: str, **context: object) -> None:
    """Emit a safe structured filesystem event."""
    payload = {"event": event, "module": MODULE, "role": ROLE, **context}
    LOGGER.info(json.dumps(payload, ensure_ascii=False, default=str))


def resolve_card_image(
    request: TarotImageRequest,
    asset_root: Path = DEFAULT_ASSET_ROOT,
) -> TarotImage:
    """Resolve and validate a bundled upright or reversed SVG card asset."""
    _log("resolve_card_image_entry", run_id="local", task_id="tarot", span_id="image")
    request.validate()
    if not request.card.image_path:
        raise ValueError(f"Card {request.card.id} has no image path")
    filename = Path(request.card.image_path).name
    if request.reversed:
        filename = f"{Path(filename).stem}_reversed{Path(filename).suffix}"
    directory = asset_root.expanduser().resolve() / "cards"
    path = directory / "reverse" / filename if request.reversed else directory / filename
    _log(
        "resolve_card_image_request",
        run_id="local",
        task_id="tarot",
        span_id="image",
        card_id=request.card.id,
        reversed=request.reversed,
        path=path,
    )
    if not path.is_file():
        raise FileNotFoundError(f"Tarot image not found: {path}")
    try:
        root = ElementTree.parse(path).getroot()
        width = int(root.attrib["width"])
        height = int(root.attrib["height"])
    except (ElementTree.ParseError, KeyError, ValueError) as error:
        raise ValueError(f"Invalid SVG asset: {path}") from error
    result = TarotImage(request.card.id, str(path), "image/svg+xml", width, height, request.reversed)
    result.validate()
    _log(
        "resolve_card_image_exit",
        run_id="local",
        task_id="tarot",
        span_id="image",
        output={"card_id": result.card_id, "width": width, "height": height},
    )
    return result
