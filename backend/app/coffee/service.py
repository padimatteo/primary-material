from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.coffee.models import CoffeeEntry, Grinder, Product, Roaster
from app.coffee.schemas import CoffeeEntryCreate, CoffeeEntryUpdate


def _name(value: str) -> str:
    """Apply the same surrounding-whitespace normalization as the request schemas."""
    return value.strip()


def _resolve_roaster(session: Session, submitted_name: str) -> Roaster:
    name = _name(submitted_name)
    session.execute(
        insert(Roaster)
        .values(name=name)
        .on_conflict_do_nothing(index_elements=[func.lower(Roaster.name)])
    )
    return session.execute(
        select(Roaster).where(func.lower(Roaster.name) == name.lower())
    ).scalar_one()


def _resolve_product(session: Session, roaster: Roaster, submitted_name: str) -> Product:
    name = _name(submitted_name)
    session.execute(
        insert(Product)
        .values(roaster_id=roaster.id, name=name)
        .on_conflict_do_nothing(
            index_elements=[Product.roaster_id, func.lower(Product.name)]
        )
    )
    return session.execute(
        select(Product).where(
            Product.roaster_id == roaster.id,
            func.lower(Product.name) == name.lower(),
        )
    ).scalar_one()


def _resolve_grinder(session: Session, submitted_name: str) -> Grinder:
    name = _name(submitted_name)
    session.execute(
        insert(Grinder)
        .values(name=name)
        .on_conflict_do_nothing(index_elements=[func.lower(Grinder.name)])
    )
    return session.execute(
        select(Grinder).where(func.lower(Grinder.name) == name.lower())
    ).scalar_one()


def create_entry(session: Session, data: CoffeeEntryCreate) -> CoffeeEntry:
    """Resolve lookups and create an entry atomically in one database transaction."""
    values = data.model_dump()
    with session.begin():
        roaster = _resolve_roaster(session, values.pop("roaster"))
        product = _resolve_product(session, roaster, values.pop("product"))
        grinder = _resolve_grinder(session, values.pop("grinder"))
        entry = CoffeeEntry(product=product, grinder=grinder, **values)
        session.add(entry)
        session.flush()
        # Materialize server-generated ID and timestamps before leaving the transaction.
        session.refresh(entry)
    return entry


def update_entry(
    session: Session, entry_id: UUID, data: CoffeeEntryUpdate
) -> CoffeeEntry | None:
    """Update only supplied fields and resolve all changed lookups transactionally."""
    values = data.model_dump(exclude_unset=True)
    with session.begin():
        entry = session.scalar(
            select(CoffeeEntry)
            .where(CoffeeEntry.id == entry_id)
            .options(
                selectinload(CoffeeEntry.product).selectinload(Product.roaster),
                selectinload(CoffeeEntry.grinder),
            )
        )
        if entry is None:
            return None

        submitted_roaster = values.pop("roaster", None)
        submitted_product = values.pop("product", None)
        if submitted_roaster is not None or submitted_product is not None:
            roaster = (
                _resolve_roaster(session, submitted_roaster)
                if submitted_roaster is not None
                else entry.product.roaster
            )
            product_name = (
                submitted_product if submitted_product is not None else entry.product.name
            )
            entry.product = _resolve_product(session, roaster, product_name)

        submitted_grinder = values.pop("grinder", None)
        if submitted_grinder is not None:
            entry.grinder = _resolve_grinder(session, submitted_grinder)

        for field, value in values.items():
            setattr(entry, field, value)

        # Explicitly touch the column, including when submitted values equal stored values.
        entry.updated_at = func.now()
        session.flush()
        session.refresh(entry, attribute_names=["updated_at"])
    return entry


def delete_entry(session: Session, entry_id: UUID) -> bool:
    """Delete only the brew entry; lookup rows remain available for future entries."""
    with session.begin():
        entry = session.get(CoffeeEntry, entry_id)
        if entry is None:
            return False
        session.delete(entry)
        session.flush()
    return True
