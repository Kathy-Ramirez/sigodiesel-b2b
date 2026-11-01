"""Actualizar restriccion de litros asignados

Revision ID: 23f507e10308
Revises: 6a9692da84f8
Create Date: 2026-11-01 14:05:49.064335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23f507e10308'
down_revision = '6a9692da84f8'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "ck_cupo_litros_asignados",
        "cupo_semanal",
        type_="check"
    )

    op.create_check_constraint(
        "ck_cupo_litros_asignados",
        "cupo_semanal",
        "litros_asignados > 0"
    )


def downgrade():
    op.drop_constraint(
        "ck_cupo_litros_asignados",
        "cupo_semanal",
        type_="check"
    )

    op.create_check_constraint(
        "ck_cupo_litros_asignados",
        "cupo_semanal",
        "litros_asignados >= 0"
    )