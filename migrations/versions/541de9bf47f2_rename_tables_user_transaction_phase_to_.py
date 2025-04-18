"""Rename tables user, transaction, phase to avoid conflicts

Revision ID: 541de9bf47f2
Revises: e090df7c3508
Create Date: 2025-04-17 13:36:10.737005

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '541de9bf47f2'
down_revision = 'e090df7c3508'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('app_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(length=50), nullable=False),
    sa.Column('prenom', sa.String(length=50), nullable=False),
    sa.Column('mail', sa.String(length=100), nullable=False),
    sa.Column('telephone', sa.String(length=20), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('organisation_id', sa.Integer(), nullable=False),
    sa.Column('is_super_admin', sa.Boolean(), nullable=False),
    sa.Column('is_demo', sa.Boolean(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('mail')
    )
    op.create_table('financial_transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('type', sa.String(length=10), nullable=False),
    sa.Column('montant', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('mode_paiement', sa.String(length=50), nullable=True),
    sa.Column('projet_id', sa.Integer(), nullable=True),
    sa.Column('organisation_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('exercice_id', sa.Integer(), nullable=True),
    sa.Column('reglement', sa.String(length=20), nullable=True),
    sa.Column('compte_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['compte_id'], ['compte_comptable.id'], ),
    sa.ForeignKeyConstraint(['exercice_id'], ['exercice_comptable.id'], ),
    sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id'], ),
    sa.ForeignKeyConstraint(['projet_id'], ['projet.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('project_phase',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(length=255), nullable=False),
    sa.Column('date_debut', sa.Date(), nullable=True),
    sa.Column('date_fin', sa.Date(), nullable=True),
    sa.Column('statut', sa.String(length=50), nullable=True),
    sa.Column('projet_id', sa.Integer(), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['projet_id'], ['projet.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index('mail')

    op.drop_table('user')
    op.drop_table('phase')
    op.drop_table('transaction')
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])
        batch_op.create_foreign_key(None, 'compte_comptable', ['compte_comptable_id'], ['id'])

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

    with op.batch_alter_table('jalon', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'projet', ['projet_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key(None, 'project_phase', ['phase_id'], ['id'])

    with op.batch_alter_table('ligne_ecriture', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'compte_comptable', ['compte_id'], ['id'])
        batch_op.create_foreign_key(None, 'ecriture_comptable', ['ecriture_id'], ['id'])

    with op.batch_alter_table('projet', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'client', ['client_id'], ['id'])
        batch_op.create_foreign_key(None, 'app_user', ['user_id'], ['id'])
        batch_op.create_foreign_key(None, 'organisation', ['organisation_id'], ['id'])

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

    with op.batch_alter_table('ligne_ecriture', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('jalon', schema=None) as batch_op:
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

    op.create_table('transaction',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('date', sa.DATE(), nullable=False),
    sa.Column('type', mysql.VARCHAR(collation='utf8mb4_general_ci', length=10), nullable=False),
    sa.Column('montant', mysql.DECIMAL(precision=10, scale=2), nullable=False),
    sa.Column('description', mysql.VARCHAR(collation='utf8mb4_general_ci', length=200), nullable=True),
    sa.Column('mode_paiement', mysql.VARCHAR(collation='utf8mb4_general_ci', length=50), nullable=True),
    sa.Column('projet_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('organisation_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('user_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('exercice_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('reglement', mysql.VARCHAR(collation='utf8mb4_general_ci', length=20), nullable=True),
    sa.Column('compte_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_general_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    op.create_table('phase',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nom', mysql.VARCHAR(collation='utf8mb4_general_ci', length=255), nullable=False),
    sa.Column('date_debut', sa.DATE(), nullable=True),
    sa.Column('date_fin', sa.DATE(), nullable=True),
    sa.Column('statut', mysql.VARCHAR(collation='utf8mb4_general_ci', length=50), nullable=True),
    sa.Column('projet_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('progress', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_general_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    op.create_table('user',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('nom', mysql.VARCHAR(collation='utf8mb4_general_ci', length=50), nullable=False),
    sa.Column('prenom', mysql.VARCHAR(collation='utf8mb4_general_ci', length=50), nullable=False),
    sa.Column('mail', mysql.VARCHAR(collation='utf8mb4_general_ci', length=100), nullable=False),
    sa.Column('telephone', mysql.VARCHAR(collation='utf8mb4_general_ci', length=20), nullable=True),
    sa.Column('password_hash', mysql.VARCHAR(charset='utf8mb4', collation='utf8mb4_general_ci', length=255), nullable=True),
    sa.Column('organisation_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('is_super_admin', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('is_demo', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('role', mysql.VARCHAR(collation='utf8mb4_general_ci', length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_general_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index('mail', ['mail'], unique=True)

    op.drop_table('project_phase')
    op.drop_table('financial_transaction')
    op.drop_table('app_user')
    # ### end Alembic commands ###
