"""Create coffee lookup and entry tables.

Revision ID: 0001_coffee_foundation
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_coffee_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roasters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.CheckConstraint("name = btrim(name) AND length(name) BETWEEN 1 AND 255", name="ck_roasters_name_trimmed"),
    )
    op.create_index("uq_roasters_name_ci", "roasters", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("roaster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roasters.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.CheckConstraint("name = btrim(name) AND length(name) BETWEEN 1 AND 255", name="ck_products_name_trimmed"),
    )
    op.create_index("uq_products_roaster_name_ci", "products", ["roaster_id", sa.text("lower(name)")], unique=True)

    op.create_table(
        "grinders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.CheckConstraint("name = btrim(name) AND length(name) BETWEEN 1 AND 255", name="ck_grinders_name_trimmed"),
    )
    op.create_index("uq_grinders_name_ci", "grinders", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "coffee_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("roast_level", sa.SmallInteger(), nullable=False),
        sa.Column("recipe_type", sa.String(32), nullable=False),
        sa.Column("coffee_weight_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("brew_time_seconds", sa.Integer(), nullable=False),
        sa.Column("total_yield_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("grind_setting", sa.Numeric(8, 2), nullable=False),
        sa.Column("grinder_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grinders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("roast_level BETWEEN 1 AND 5", name="ck_coffee_entries_roast_level"),
        sa.CheckConstraint("recipe_type IN ('espresso', 'pour_over', 'drip', 'french_press')", name="ck_coffee_entries_recipe_type"),
        sa.CheckConstraint("coffee_weight_g > 0", name="ck_coffee_entries_coffee_weight_positive"),
        sa.CheckConstraint("brew_time_seconds > 0", name="ck_coffee_entries_brew_time_positive"),
        sa.CheckConstraint("total_yield_g > 0", name="ck_coffee_entries_total_yield_positive"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_coffee_entries_rating"),
    )
    op.create_index("ix_coffee_entries_product_id", "coffee_entries", ["product_id"])
    op.create_index("ix_coffee_entries_grinder_id", "coffee_entries", ["grinder_id"])
    op.create_index("ix_coffee_entries_date", "coffee_entries", ["date"])
    op.create_index("ix_coffee_entries_recipe_type", "coffee_entries", ["recipe_type"])
    op.create_index("ix_coffee_entries_rating", "coffee_entries", ["rating"])


def downgrade() -> None:
    op.drop_index("ix_coffee_entries_rating", table_name="coffee_entries")
    op.drop_index("ix_coffee_entries_recipe_type", table_name="coffee_entries")
    op.drop_index("ix_coffee_entries_date", table_name="coffee_entries")
    op.drop_index("ix_coffee_entries_grinder_id", table_name="coffee_entries")
    op.drop_index("ix_coffee_entries_product_id", table_name="coffee_entries")
    op.drop_table("coffee_entries")
    op.drop_index("uq_grinders_name_ci", table_name="grinders")
    op.drop_table("grinders")
    op.drop_index("uq_products_roaster_name_ci", table_name="products")
    op.drop_table("products")
    op.drop_index("uq_roasters_name_ci", table_name="roasters")
    op.drop_table("roasters")
