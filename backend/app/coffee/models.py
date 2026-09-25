from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Roaster(Base):
    __tablename__ = "roasters"
    __table_args__ = (
        CheckConstraint(
            "name = btrim(name) AND length(name) BETWEEN 1 AND 255",
            name="ck_roasters_name_trimmed",
        ),
        Index("uq_roasters_name_ci", func.lower(text("name")), unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    products: Mapped[list["Product"]] = relationship(back_populates="roaster")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "name = btrim(name) AND length(name) BETWEEN 1 AND 255",
            name="ck_products_name_trimmed",
        ),
        Index("uq_products_roaster_name_ci", "roaster_id", func.lower(text("name")), unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    roaster_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("roasters.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    roaster: Mapped[Roaster] = relationship(back_populates="products")
    entries: Mapped[list["CoffeeEntry"]] = relationship(back_populates="product")


class Grinder(Base):
    __tablename__ = "grinders"
    __table_args__ = (
        CheckConstraint(
            "name = btrim(name) AND length(name) BETWEEN 1 AND 255",
            name="ck_grinders_name_trimmed",
        ),
        Index("uq_grinders_name_ci", func.lower(text("name")), unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entries: Mapped[list["CoffeeEntry"]] = relationship(back_populates="grinder")


class CoffeeEntry(Base):
    __tablename__ = "coffee_entries"
    __table_args__ = (
        CheckConstraint("roast_level BETWEEN 1 AND 5", name="ck_coffee_entries_roast_level"),
        CheckConstraint(
            "recipe_type IN ('espresso', 'pour_over', 'drip', 'french_press')",
            name="ck_coffee_entries_recipe_type",
        ),
        CheckConstraint("coffee_weight_g > 0", name="ck_coffee_entries_coffee_weight_positive"),
        CheckConstraint("brew_time_seconds > 0", name="ck_coffee_entries_brew_time_positive"),
        CheckConstraint("total_yield_g > 0", name="ck_coffee_entries_total_yield_positive"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_coffee_entries_rating"),
        Index("ix_coffee_entries_product_id", "product_id"),
        Index("ix_coffee_entries_grinder_id", "grinder_id"),
        Index("ix_coffee_entries_date", "date"),
        Index("ix_coffee_entries_recipe_type", "recipe_type"),
        Index("ix_coffee_entries_rating", "rating"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    roast_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    recipe_type: Mapped[str] = mapped_column(String(32), nullable=False)
    coffee_weight_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    brew_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    total_yield_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    grind_setting: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    grinder_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("grinders.id", ondelete="RESTRICT"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    product: Mapped[Product] = relationship(back_populates="entries")
    grinder: Mapped[Grinder] = relationship(back_populates="entries")
