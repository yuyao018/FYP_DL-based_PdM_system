def _apply_filters(query, filters):
    for operator, column, value in filters:
        if operator not in {"eq", "in_", "lte"}:
            raise ValueError(f"Unsupported database filter: {operator}")
        query = getattr(query, operator)(column, value)
    return query


def fetch_records(client, table, columns="*", *, filters=(), order_by=(), limit=None, row_range=None, single=False, count=None):
    """Retrieve rows; optionally sort, paginate, count, or request one row.

    order_by contains (column, descending) pairs. row_range is an inclusive
    (start, end) pair, matching Supabase's range convention.
    """
    options = {"count": count} if count is not None else {}
    query = client.table(table).select(columns, **options)
    query = _apply_filters(query, filters)
    for column, descending in order_by:
        query = query.order(column, desc=descending)
    if limit is not None:
        query = query.limit(limit)
    if row_range is not None:
        query = query.range(*row_range)
    if single:
        query = query.single()
    return query.execute()


def insert_records(client, table, data):
    """Insert a dictionary or list of dictionaries and return the SDK response."""
    return client.table(table).insert(data).execute()


def update_records(client, table, data, *, filters=()):
    """Update matching records; callers must supply their authorization filters."""
    return _apply_filters(client.table(table).update(data), filters).execute()


def delete_records(client, table, *, filters=()):
    """Permanently delete matching records (soft deletion uses update_records)."""
    return _apply_filters(client.table(table).delete(), filters).execute()


def call_database_function(client, name, params):
    """Execute a database RPC, including the existing login verification RPC."""
    return client.rpc(name, params).execute()


def get_alert_thresholds(client, columns="*"):
    """Read the latest threshold configuration; callers choose their fallbacks."""
    return fetch_records(client, "alert_thresholds", columns,
                         order_by=[("updated_at", True)], limit=1)


def get_engine(client, engine_id, columns="*"):
    """Retrieve one engine by its database primary key."""
    return fetch_records(client, "engines", columns,
                         filters=[("eq", "id", engine_id)], single=True)


def get_latest_prediction(client, engine_id, columns="*"):
    """Read the newest stored prediction by timestamp (response data is a list)."""
    return fetch_records(client, "rul_predictions", columns,
                         filters=[("eq", "engine_id", engine_id)],
                         order_by=[("predicted_at", True)], limit=1)


def download_file(client, bucket, path):
    return client.storage.from_(bucket).download(path)


def list_files(client, bucket, path):
    return client.storage.from_(bucket).list(path)


def remove_files(client, bucket, paths):
    return client.storage.from_(bucket).remove(paths)


def upload_file(client, bucket, *args, **kwargs):
    """Preserve Supabase upload options such as content type and upsert."""
    return client.storage.from_(bucket).upload(*args, **kwargs)
