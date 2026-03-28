from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict, field_validator, model_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import root_validator, validator

    ConfigDict = dict
    PYDANTIC_V2 = False

    def field_validator(*fields, **kwargs):
        def decorator(func: Callable[..., Any]) -> classmethod:
            return validator(*fields, allow_reuse=True)(func)
        return decorator

    def model_validator(*, mode: str):
        pre = mode == "before"
        def decorator(func: Callable[..., Any]):
            if pre:
                return root_validator(pre=True, allow_reuse=True)(func)

            def wrapper(cls, values):
                obj = cls.construct(**values)
                result = func(obj)
                if isinstance(result, cls):
                    return result.dict()
                if isinstance(result, dict):
                    return result
                return values
            return root_validator(pre=False, allow_reuse=True)(wrapper)
        return decorator


class StrictModel(BaseModel):
    if PYDANTIC_V2:
        model_config = ConfigDict(
            extra="forbid",
            populate_by_name=True,
            use_enum_values=True,
            str_strip_whitespace=True,
        )
    else:
        class Config:
            extra = "forbid"
            allow_population_by_field_name = True
            use_enum_values = True
            anystr_strip_whitespace = True


def compat_field(*args, min_length=None, max_length=None, pattern=None, **kwargs):
    if PYDANTIC_V2:
        if pattern is not None:
            kwargs["pattern"] = pattern
        return Field(*args, min_length=min_length, max_length=max_length, **kwargs)
    if pattern is not None:
        kwargs["regex"] = pattern
    if min_length is not None and max_length is not None and len(args) == 1:
        default = args[0]
        if default_factory := kwargs.get("default_factory"):
            return Field(*args, min_items=min_length, max_items=max_length, **kwargs)
        origin = kwargs.pop('_compat_origin', None)
    return Field(*args, min_length=min_length, max_length=max_length, **kwargs)
