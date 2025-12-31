from pydantic import BaseModel
from core.utils.callables import call_if_zero_arg

class ResolvableModel(BaseModel):
    def __getattribute__(self, name: str):
        value = super().__getattribute__(name)

        try:
            fields = super().__getattribute__("model_fields")
        except Exception:
            return value

        if name not in fields:
            return value

        return call_if_zero_arg(value)
