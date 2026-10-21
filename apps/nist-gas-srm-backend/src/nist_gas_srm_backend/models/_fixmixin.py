import sys
from typing import Any

from pydantic import model_validator
from sqlmodel import (
    SQLModel,
)
from sqlmodel._compat import (  # ruff: ignore[import-private-name]
    get_relationship_to,
)


class FixMixin(SQLModel):
    # see https://github.com/fastapi/sqlmodel/issues/293
    @model_validator(mode="before")
    @classmethod
    def convert_relationships(cls, model: Any) -> Any:
        class_module_globals: dict[str, Any] | None = None
        for rel_name, rel_info in cls.__sqlmodel_relationships__.items():
            if (attr := getattr(model, rel_name, None)) is None:
                continue

            # use sqlmodel internal function to get class
            ann = cls.__annotations__[rel_name].__args__[0]
            rel_class_name = get_relationship_to(
                name=rel_name, rel_info=rel_info, annotation=ann
            )

            # might be type or string depending on how it was declared
            # Updated this to work across modules
            rel_class: Any
            if isinstance(rel_class_name, type):
                rel_class = rel_class_name
            else:
                if class_module_globals is None:
                    class_module_globals = sys.modules[cls.__module__].__dict__

                if rel_class_name not in class_module_globals:
                    msg = f"Couldn't find {rel_class_name} for cls {cls} with module {cls.__module__}"
                    raise ValueError(msg)
                rel_class = class_module_globals[rel_class_name]

            # rel_class: Any = (
            #     rel_class_name
            #     if isinstance(rel_class_name, type)
            #     else globals()[rel_class_name]
            # )  # ruff: ignore[commented-out-code]

            # convert attribute(s) with their model's validator
            items: Any
            if isinstance(attr, list):
                items = [rel_class.model_validate(item) for item in attr]  # pyright: ignore[reportUnknownVariableType]
                setattr(model, rel_name, items)
            else:
                item = rel_class.model_validate(attr)
                setattr(model, rel_name, item)

        return model
