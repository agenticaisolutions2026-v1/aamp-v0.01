class Aggregator:
    """
    Aggregates deduplicated college entries into the final structured output.
    """

    def aggregate(
        self,
        colleges,
        state="Andhra Pradesh",
        category="engineering colleges"
    ):
        return {
            "state": state,
            "category": category,
            "count": len(colleges),
            "colleges": colleges
        }
