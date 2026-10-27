"""Resolve registered engine IDs to their simulation dataset."""


def resolve_engine_dataset(engine_id, model_type):
    """Four-digit IDs encode dataset + three-digit engine number.

    Older short IDs remain usable with the explicitly selected model type.
    """
    text = str(engine_id).strip()
    if not text.isascii() or not text.isdigit() or int(text) < 1:
        raise ValueError("Engine ID must be a positive whole number.")
    if len(text) == 4:
        if text[0] not in "1234" or int(text[1:]) == 0:
            raise ValueError("Use a dataset digit from 1 to 4 followed by an engine number from 001 to 999.")
        model_type = f"FD00{text[0]}"
        number = int(text[1:])
    elif len(text) < 4:
        number = int(text)
    else:
        raise ValueError("Engine ID must have at most four digits, for example 3001.")
    if model_type not in {"FD001", "FD002", "FD003", "FD004"}:
        raise ValueError("Select a supported engine model.")
    return model_type, f"{model_type}/engine_test_{number}.json"
