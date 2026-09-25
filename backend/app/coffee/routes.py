from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.coffee import service
from app.coffee.models import CoffeeEntry, Grinder, Product, Roaster
from app.coffee.schemas import (
    CoffeeEntryCreate,
    CoffeeEntryList,
    CoffeeEntryListQuery,
    CoffeeEntryResponse,
    CoffeeEntryUpdate,
    CoffeeSuggestions,
    CoffeeSuggestionsQuery,
    SortDirection,
    SortField,
    SuggestionField,
)
from app.database import get_db

router = APIRouter(prefix="/coffee/recipes", tags=["coffee"])
DbSession = Annotated[Session, Depends(get_db)]
EntryRelations = (
    selectinload(CoffeeEntry.product).selectinload(Product.roaster),
    selectinload(CoffeeEntry.grinder),
)


@router.post("", response_model=CoffeeEntryResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    data: CoffeeEntryCreate,
    response: Response,
    session: DbSession,
) -> CoffeeEntry:
    entry = service.create_entry(session, data)
    response.headers["Location"] = f"/api/coffee/recipes/{entry.id}"
    return entry


@router.get("", response_model=CoffeeEntryList)
def list_recipes(
    session: DbSession,
    query: Annotated[CoffeeEntryListQuery, Depends()],
) -> CoffeeEntryList:
    filters = _filters(query)
    joins = (
        CoffeeEntry.product,
        Product.roaster,
        CoffeeEntry.grinder,
    )
    count_statement = (
        select(func.count(CoffeeEntry.id))
        .join(joins[0])
        .join(joins[1])
        .join(joins[2])
    )
    total = session.scalar(count_statement.where(*filters)) or 0

    sort_column = _sort_columns()[query.sort_by]
    if query.sort_dir is SortDirection.DESC:
        ordering = (sort_column.desc(), CoffeeEntry.id.desc())
    else:
        ordering = (sort_column.asc(), CoffeeEntry.id.asc())

    statement = (
        select(CoffeeEntry)
        .join(joins[0])
        .join(joins[1])
        .join(joins[2])
        .where(*filters)
        .options(*EntryRelations)
        .order_by(*ordering)
        .limit(query.limit)
        .offset(query.offset)
    )
    items = list(session.scalars(statement).all())
    return CoffeeEntryList(items=items, total=total, limit=query.limit, offset=query.offset)


@router.get("/suggestions", response_model=CoffeeSuggestions)
def suggest_names(
    session: DbSession,
    query: Annotated[CoffeeSuggestionsQuery, Query()],
) -> CoffeeSuggestions:
    if query.field is SuggestionField.ROASTER:
        name = Roaster.name
        referenced = exists(
            select(CoffeeEntry.id)
            .join(Product, CoffeeEntry.product_id == Product.id)
            .where(Product.roaster_id == Roaster.id)
        )
        statement = select(name).where(referenced)
    elif query.field is SuggestionField.PRODUCT:
        name = Product.name
        referenced = exists(select(CoffeeEntry.id).where(CoffeeEntry.product_id == Product.id))
        statement = (
            select(name)
            .join(Roaster, Product.roaster_id == Roaster.id)
            .where(func.lower(Roaster.name) == query.roaster.lower(), referenced)
        )
    else:
        name = Grinder.name
        referenced = exists(select(CoffeeEntry.id).where(CoffeeEntry.grinder_id == Grinder.id))
        statement = select(name).where(referenced)

    if query.q:
        escaped = query.q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(name.ilike(f"{escaped}%", escape="\\"))
    values = session.scalars(statement.order_by(func.lower(name), name).limit(query.limit)).all()
    return CoffeeSuggestions(values=list(values))


@router.get("/{entry_id}", response_model=CoffeeEntryResponse)
def get_recipe(entry_id: UUID, session: DbSession) -> CoffeeEntry:
    statement = (
        select(CoffeeEntry)
        .where(CoffeeEntry.id == entry_id)
        .options(*EntryRelations)
    )
    entry = session.scalar(statement)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coffee entry not found")
    return entry


@router.put("/{entry_id}", response_model=CoffeeEntryResponse)
def update_recipe(
    entry_id: UUID,
    data: CoffeeEntryUpdate,
    session: DbSession,
) -> CoffeeEntry:
    entry = service.update_entry(session, entry_id, data)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coffee entry not found")
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(entry_id: UUID, session: DbSession) -> Response:
    deleted = service.delete_entry(session, entry_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coffee entry not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _filters(query: CoffeeEntryListQuery) -> list:
    filters = []
    if query.q:
        escaped = (
            query.q.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        pattern = f"%{escaped}%"
        filters.append(
            or_(
                Roaster.name.ilike(pattern, escape="\\"),
                Product.name.ilike(pattern, escape="\\"),
                Grinder.name.ilike(pattern, escape="\\"),
                CoffeeEntry.notes.ilike(pattern, escape="\\"),
            )
        )
    if query.roaster is not None:
        filters.append(func.lower(Roaster.name) == query.roaster.lower())
    if query.product is not None:
        filters.append(func.lower(Product.name) == query.product.lower())
    if query.grinder is not None:
        filters.append(func.lower(Grinder.name) == query.grinder.lower())
    if query.recipe_type is not None:
        filters.append(CoffeeEntry.recipe_type == query.recipe_type.value)
    if query.roast_level is not None:
        filters.append(CoffeeEntry.roast_level == query.roast_level)
    if query.rating is not None:
        filters.append(CoffeeEntry.rating == query.rating)
    if query.date_from is not None:
        filters.append(CoffeeEntry.date >= query.date_from)
    if query.date_to is not None:
        filters.append(CoffeeEntry.date <= query.date_to)
    return filters


def _sort_columns() -> dict[SortField, object]:
    return {
        SortField.DATE: CoffeeEntry.date,
        SortField.ROASTER: func.lower(Roaster.name),
        SortField.PRODUCT: func.lower(Product.name),
        SortField.ROAST_LEVEL: CoffeeEntry.roast_level,
        SortField.RECIPE_TYPE: CoffeeEntry.recipe_type,
        SortField.COFFEE_WEIGHT_G: CoffeeEntry.coffee_weight_g,
        SortField.BREW_TIME_SECONDS: CoffeeEntry.brew_time_seconds,
        SortField.TOTAL_YIELD_G: CoffeeEntry.total_yield_g,
        SortField.GRIND_SETTING: CoffeeEntry.grind_setting,
        SortField.GRINDER: func.lower(Grinder.name),
        SortField.RATING: CoffeeEntry.rating,
        SortField.CREATED_AT: CoffeeEntry.created_at,
    }
