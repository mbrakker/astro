# Tarot

Standalone extraction of Astro Bot's tarot domain. It includes the complete
78-card SQL database, all 78 upright and 78 reversed card illustrations,
three spread-table backgrounds, versioned Python contracts, card lookup,
one-card draws, and reproducible three-card past/present/future spreads.

## Install and use

```bash
python -m pip install -e ./tarot
python - <<'PY'
from tarot import TarotDrawRequest, draw_spread

spread = draw_spread(TarotDrawRequest(spread_type="three", seed="weekly-2026-31"))
for card in spread.cards:
    print(card.position, card.name, card.reversed, card.interpretation)

from tarot import TarotImageRequest, resolve_card_image
image = resolve_card_image(TarotImageRequest(spread.cards[0], spread.cards[0].reversed))
print(image.path)
PY
```

The default database is `data/tarot.sql`. Pass a `pathlib.Path` as the second
argument to `load_cards`, `load_card`, or `draw_spread` to use another database.
The bundled SQL database is loaded into read-only application memory. A draw seed is optional; supply one
whenever the result must be reproducible.

## Architecture

* `src/tarot/contracts.py` is the versioned input/output contract.
* `src/tarot/services/tarot_service.py` is the only SQLite boundary.
* `data/tarot.sql` is a reviewable export of the production database (78 cards
  and meanings), loaded into an in-memory SQLite connection by the service.
* `assets/cards/` contains every image named by the database; `reverse/` contains
  a rotated image for every card, using the legacy `_reversed` naming convention.
* `assets/tables/` contains all three backgrounds used to compose spreads.
* `tests/` checks database completeness, contract round trips, validation, and
  deterministic draws.

All illustrations are reviewable SVG text files rather than opaque binary diff
entries. Each SVG embeds its lossless source artwork and can be rendered directly
by browsers and image tooling. The image service validates the SVG document and dimensions before returning a
versioned `TarotImage` contract. Tests enforce a one-to-one match between all 78
database image names and both bundled orientations, so an incomplete image pack
cannot pass CI. The package does not depend on Astro Bot paths, logging files, or
its publishing pipeline and can be published independently as `tarot`.
