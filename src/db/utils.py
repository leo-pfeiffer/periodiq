from datetime import datetime
from typing import Any


def orm_to_dict(obj: Any, recurse_relationships=True, visited=None):
    if obj is None:
        return None

    if visited is None:
        visited = set()

    # Prevent infinite recursion by checking visited identity
    obj_id = id(obj)
    if obj_id in visited:
        return {"_ref": str(obj)}  # or None, or skip entirely
    visited.add(obj_id)

    result = {}

    # Regular columns
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, datetime):
            result[column.name] = val.isoformat()
        else:
            result[column.name] = val

    # Related objects
    if recurse_relationships:
        for rel in obj.__mapper__.relationships:
            val = getattr(obj, rel.key)
            if val is None:
                result[rel.key] = None
            elif rel.uselist:
                result[rel.key] = [orm_to_dict(i, recurse_relationships, visited) for i in val]
            else:
                result[rel.key] = orm_to_dict(val, recurse_relationships, visited)

    return result
