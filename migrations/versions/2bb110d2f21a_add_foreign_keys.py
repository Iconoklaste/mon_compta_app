"""Add foreign keys

Revision ID: 2bb110d2f21a
Revises: 541de9bf47f2
Create Date: 2025-04-17 14:25:50.953417

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bb110d2f21a'
down_revision = '541de9bf47f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('app_user', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])

    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'compte_comptable', ['compte_comptable_id'], ['id'])
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])

    with op.batch_alter_table('compte_comptable', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])

    with op.batch_alter_table('ecriture_comptable', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'exercice_comptable', ['exercice_id'], ['id'])
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])

    with op.batch_alter_table('equipe_membre', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'projet', ['projet_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'app_user', ['user_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('exercice_comptable', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])

    with op.batch_alter_table('financial_transaction', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'exercice_comptable', ['exercice_id'], ['id'])
        batch_op.create_foreign_key(None, 'app_user', ['user_id'], ['id'])
        batch_op.create_foreign_key(None, 'compte_comptable', ['compte_id'], ['id'])
        batch_op.create_foreign_key(None, 'projet', ['projet_id'], ['id'])
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])

    with op.batch_alter_table('jalon', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'project_phase', ['phase_id'], ['id'])
        batch_op.create_foreign_key(None, 'projet', ['projet_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('ligne_ecriture', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'compte_comptable', ['compte_id'], ['id'])
        batch_op.create_foreign_key(None, 'ecriture_comptable', ['ecriture_id'], ['id'])

    with op.batch_alter_table('project_phase', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'projet', ['projet_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('projet', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'app_user', ['user_id'], ['id'])
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])
        batch_op.create_foreign_key(None, 'client', ['client_id'], ['id'])

    with op.batch_alter_table('whiteboard', schema=None) as batch_op:
        batch_op.drop_index('fk_whiteboard_projet')
        batch_op.create_foreign_key('fk_whiteboard_projet', 'projet', ['projet_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('whiteboard', schema=None) as batch_op:
        batch_op.drop_constraint('fk_whiteboard_projet', type_='foreignkey')
        batch_op.create_index('fk_whiteboard_projet', ['projet_id'], unique=False)

    with op.batch_alter_table('projet', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('project_phase', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('ligne_ecriture', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('jalon', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('financial_transaction', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('exercice_comptable', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('equipe_membre', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('ecriture_comptable', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('compte_comptable', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('app_user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    # ### end Alembic commands ###
