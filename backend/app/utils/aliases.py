"""Provider aliases for normalizing provider slugs."""

ALIASES = {
    "xai": "grok",
    "meta": "llama",  # if you add later
    # add others as needed
}

def normalize_provider(slug: str) -> str:
    """Normalize provider slug using aliases."""
    return ALIASES.get(slug, slug)
