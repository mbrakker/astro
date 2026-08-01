# Astro Bot Repository

## Reuse and Modularization

A full audit identifying reusable service/module extraction candidates and the required refactor steps for universal standalone reuse is documented here:

- `docs/reuse_extraction_audit.md`

The audit includes:
- reusable service library candidates,
- domain-specific modules to keep local,
- mandatory architecture changes (contracts, role boundaries, adapters, error taxonomy, structured logs),
- migration sequence.

## Standalone tarot extraction

The `tarot/` directory is a self-contained repository payload containing the
complete tarot database and portable lookup/draw API. See [`tarot/README.md`](tarot/README.md)
for installation, architecture, and usage details.
