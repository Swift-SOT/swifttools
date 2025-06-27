from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Just define from_attributes for every Schema"""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, extra="allow")
