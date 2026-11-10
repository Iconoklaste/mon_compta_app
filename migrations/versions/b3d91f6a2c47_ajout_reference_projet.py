"""Ajout de la reference (numero d'affaire) sur projet

Revision ID: b3d91f6a2c47
Revises: 7e0157e7f2f0
Create Date: 2026-11-10 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3d91f6a2c47'
down_revision = '7e0157e7f2f0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projet', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reference', sa.String(length=50), nullable=True))
        batch_op.create_unique_constraint('uq_projet_reference_organisation', ['reference', 'organisation_id'])


def downgrade():
    with op.batch_alter_table('projet', schema=None) as batch_op:
        batch_op.drop_constraint('uq_projet_reference_organisation', type_='unique')
        batch_op.drop_column('reference')
