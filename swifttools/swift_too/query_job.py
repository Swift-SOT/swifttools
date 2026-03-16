class QueryJob:
    """Deprecated QueryJob placeholder.

    QueryJob is no longer supported in this branch. Use asynchronous query
    objects directly (for example, `VisQuery.queue()`) and poll the same
    object for completion/results.
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "QueryJob is deprecated and disabled in this branch. "
            "Use queue() on the request object and poll that object directly."
        )
