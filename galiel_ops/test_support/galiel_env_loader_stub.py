"""No-op loader used ONLY by isolated operations tests. Never deployed as production loader."""

def load_private_env(*args, **kwargs):
    return None
