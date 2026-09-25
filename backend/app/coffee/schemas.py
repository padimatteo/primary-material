from datetime import date as Date
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


class RecipeType(StrEnum):
    ESPRESSO = "espresso"
    POUR_OVER = "pour_over"
    DRIP = "drip"
    FRENCH_PRESS = "french_press"


LookupName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, strict=True, min_length=1, max_length=255),
]
PositiveAmount = Annotated[
    Decimal,
    Field(gt=0, max_digits=8, decimal_places=2, allow_inf_nan=False),
]
GrindAmount = Annotated[
    Decimal,
    Field(max_digits=8, decimal_places=2, allow_inf_nan=False),
]
ScaleValue = Annotated[int, Field(ge=1, le=5, strict=True)]


class CoffeeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CoffeeEntryCreate(CoffeeSchema):
    date: Date
    roaster: LookupName
    product: LookupName
    roast_level: ScaleValue
    recipe_type: RecipeType
    coffee_weight_g: PositiveAmount
    brew_time_seconds: Annotated[int, Field(gt=0, strict=True)]
    total_yield_g: PositiveAmount
    grind_setting: GrindAmount
    grinder: LookupName
    rating: ScaleValue
    notes: Annotated[str, Field(max_length=10_000)] | None = None

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_empty_notes(cls, value: Any) -> Any:
        return None if value == "" else value


class CoffeeEntryUpdate(CoffeeSchema):
    date: Date | None = None
    roaster: LookupName | None = None
    product: LookupName | None = None
    roast_level: ScaleValue | None = None
    recipe_type: RecipeType | None = None
    coffee_weight_g: PositiveAmount | None = None
    brew_time_seconds: Annotated[int, Field(gt=0, strict=True)] | None = None
    total_yield_g: PositiveAmount | None = None
    grind_setting: GrindAmount | None = None
    grinder: LookupName | None = None
    rating: ScaleValue | None = None
    notes: Annotated[str, Field(max_length=10_000)] | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_empty_update(cls, value: Any) -> Any:
        if isinstance(value, dict) and not value:
            raise ValueError("At least one field must be supplied")
        return value

    @model_validator(mode="after")
    def reject_null_editable_fields(self) -> "CoffeeEntryUpdate":
        for field_name in self.model_fields_set - {"notes"}:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_empty_notes(cls, value: Any) -> Any:
        return None if value == "" else value


class CoffeeEntryResponse(CoffeeSchema):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    date: Date
    roaster: str = Field(validation_alias=AliasPath("product", "roaster", "name"))
    product: str = Field(validation_alias=AliasPath("product", "name"))
    roast_level: int
    recipe_type: RecipeType
    coffee_weight_g: Decimal
    brew_time_seconds: int
    total_yield_g: Decimal
    grind_setting: Decimal
    grinder: str = Field(validation_alias=AliasPath("grinder", "name"))
    rating: int
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CoffeeEntryList(CoffeeSchema):
    items: list[CoffeeEntryResponse]
    total: int
    limit: int
    offset: int


class SortField(StrEnum):
    DATE = "date"
    ROASTER = "roaster"
    PRODUCT = "product"
    ROAST_LEVEL = "roast_level"
    RECIPE_TYPE = "recipe_type"
    COFFEE_WEIGHT_G = "coffee_weight_g"
    BREW_TIME_SECONDS = "brew_time_seconds"
    TOTAL_YIELD_G = "total_yield_g"
    GRIND_SETTING = "grind_setting"
    GRINDER = "grinder"
    RATING = "rating"
    CREATED_AT = "created_at"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class CoffeeEntryListQuery(CoffeeSchema):
    q: str | None = None
    roaster: LookupName | None = None
    product: LookupName | None = None
    grinder: LookupName | None = None
    recipe_type: RecipeType | None = None
    roast_level: ScaleValue | None = None
    rating: ScaleValue | None = None
    date_from: Date | None = None
    date_to: Date | None = None
    sort_by: SortField = SortField.DATE
    sort_dir: SortDirection = SortDirection.DESC
    limit: Annotated[int, Field(ge=1, le=100)] = 20
    offset: Annotated[int, Field(ge=0)] = 0

    @field_validator("q", mode="before")
    @classmethod
    def trim_search(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> "CoffeeEntryListQuery":
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must be on or before date_to")
        return self


class SuggestionField(StrEnum):
    ROASTER = "roaster"
    PRODUCT = "product"
    GRINDER = "grinder"


class CoffeeSuggestionsQuery(CoffeeSchema):
    field: SuggestionField
    q: str | None = None
    limit: Annotated[int, Field(ge=1, le=20)] = 10
    roaster: LookupName | None = None

    @field_validator("q", mode="before")
    @classmethod
    def trim_prefix(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_roaster_scope(self) -> "CoffeeSuggestionsQuery":
        if self.field is SuggestionField.PRODUCT and self.roaster is None:
            raise ValueError("roaster is required for product suggestions")
        if self.field is not SuggestionField.PRODUCT and self.roaster is not None:
            raise ValueError("roaster is only valid for product suggestions")
        return self


class CoffeeSuggestions(CoffeeSchema):
    values: list[str]
