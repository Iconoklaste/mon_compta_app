"""Add enum calsses de comptes

Revision ID: 7c81515dbbd0
Revises: 1b932367ab71
Create Date: 2025-04-09 10:09:15.287656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c81515dbbd0'
down_revision = '1b932367ab71'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('compte_comptable', schema=None) as batch_op:
        batch_op.add_column(sa.Column('actif', sa.Boolean(), nullable=False))
        batch_op.alter_column('type',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Enum('Classe 1 – les comptes de capitaux', "Classe 2 – les comptes d'immobilisations", 'Classe 3 – les stocks et en-cours', 'Classe 4 – les comptes de tiers', 'Classe 5 – les comptes financiers', 'Classe 6 – les comptes de charge', 'Classe 7 – les comptes de produit', 'Classe 8 – les comptes spéciaux', name='classe_compte_enum'),
               existing_nullable=False)
        batch_op.drop_column('etat')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('compte_comptable', schema=None) as batch_op:
        batch_op.add_column(sa.Column('etat', sa.BOOLEAN(), nullable=False))
        batch_op.alter_column('type',
               existing_type=sa.Enum('Classe 1 – les comptes de capitaux', "Classe 2 – les comptes d'immobilisations", 'Classe 3 – les stocks et en-cours', 'Classe 4 – les comptes de tiers', 'Classe 5 – les comptes financiers', 'Classe 6 – les comptes de charge', 'Classe 7 – les comptes de produit', 'Classe 8 – les comptes spéciaux', name='classe_compte_enum'),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
        batch_op.drop_column('actif')

    # ### end Alembic commands ###
