"""Change prix_total to Integer

Revision ID: 00e2a7c0ae1e
Revises: 8aa419c53727
Create Date: 2025-03-26 09:36:45.873290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00e2a7c0ae1e'
down_revision = '8aa419c53727'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('projet', schema=None) as batch_op:
        batch_op.alter_column('prix_total',
               existing_type=sa.FLOAT(),
               type_=sa.Integer(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('projet', schema=None) as batch_op:
        batch_op.alter_column('prix_total',
               existing_type=sa.Integer(),
               type_=sa.FLOAT(),
               existing_nullable=True)

    # ### end Alembic commands ###
