# controllers/plan_comptable_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import User, Organisation, CompteComptable # Importer CompteComptable
from forms.forms import CompteComptableForm # Importer le formulaire
from sqlalchemy.exc import IntegrityError

plan_comptable_bp = Blueprint('plan_comptable', __name__, url_prefix='/plan-comptable')

@plan_comptable_bp.route('/')
@login_required
def lister_comptes():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation
    
    # Récupérer les comptes de l'organisation de l'utilisateur, triés par numéro
    comptes = CompteComptable.query.filter_by(organisation_id=organisation.id).order_by(CompteComptable.numero).all()
    
    return render_template('compta/plan_comptable/list.html', 
                           comptes=comptes, 
                           current_page='Plan Comptable') # Ajuste current_page si nécessaire

@plan_comptable_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_compte():
    form = CompteComptableForm()
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    if form.validate_on_submit():
        # Vérification supplémentaire d'unicité (même si la DB l'a) pour un meilleur feedback
        existing_compte = CompteComptable.query.filter_by(
            numero=form.numero.data, 
            organisation_id=organisation.id
        ).first()
        
        if existing_compte:
            flash(f"Le numéro de compte '{form.numero.data}' existe déjà pour cette organisation.", 'danger')
        else:
            try:
                nouveau_compte = CompteComptable(
                    numero=form.numero.data,
                    nom=form.nom.data,
                    type=form.type.data,
                    description=form.description.data,
                    organisation_id=organisation.id 
                )
                db.session.add(nouveau_compte)
                db.session.commit()
                flash('Compte comptable ajouté avec succès!', 'success')
                return redirect(url_for('plan_comptable.lister_comptes'))
            except IntegrityError: # Gère le cas où la contrainte DB est violée (juste au cas où)
                db.session.rollback()
                flash("Erreur lors de l'ajout du compte (possible doublon).", 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f"Une erreur est survenue: {e}", 'danger')

    # Si GET ou si validation échoue
    return render_template('compta/plan_comptable/form.html', 
                           form=form, 
                           titre="Ajouter un Compte Comptable",
                           current_page='Plan Comptable')

@plan_comptable_bp.route('/modifier/<int:compte_id>', methods=['GET', 'POST'])
@login_required
def modifier_compte(compte_id):
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation
    
    # Récupérer le compte et vérifier qu'il appartient bien à l'organisation de l'user
    compte = CompteComptable.query.filter_by(id=compte_id, organisation_id=organisation.id).first_or_404()
    
    form = CompteComptableForm(obj=compte) # Pré-remplir le formulaire

    if form.validate_on_submit():
        # Vérification d'unicité si le numéro a changé
        if compte.numero != form.numero.data:
            existing_compte = CompteComptable.query.filter(
                CompteComptable.id != compte_id, # Exclure le compte actuel
                CompteComptable.numero == form.numero.data,
                CompteComptable.organisation_id == organisation.id
            ).first()
            if existing_compte:
                 flash(f"Le numéro de compte '{form.numero.data}' existe déjà pour cette organisation.", 'danger')
                 # Rendre à nouveau le formulaire avec l'erreur
                 return render_template('compta/plan_comptable/form.html', 
                                        form=form, 
                                        titre="Modifier le Compte Comptable", 
                                        compte=compte,
                                        current_page='Plan Comptable')

        try:
            compte.numero = form.numero.data
            compte.nom = form.nom.data
            compte.type = form.type.data
            compte.description = form.description.data
            db.session.commit()
            flash('Compte comptable modifié avec succès!', 'success')
            return redirect(url_for('plan_comptable.lister_comptes'))
        except IntegrityError:
            db.session.rollback()
            flash("Erreur lors de la modification du compte (possible doublon).", 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue: {e}", 'danger')

    # Si GET ou si validation échoue
    return render_template('compta/plan_comptable/form.html', 
                           form=form, 
                           titre="Modifier le Compte Comptable", 
                           compte=compte, # Passer l'objet compte pour l'URL de suppression éventuelle
                           current_page='Plan Comptable')

@plan_comptable_bp.route('/supprimer/<int:compte_id>', methods=['POST'])
@login_required
def supprimer_compte(compte_id):
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    # Récupérer le compte et vérifier l'appartenance
    compte = CompteComptable.query.filter_by(id=compte_id, organisation_id=organisation.id).first_or_404()

    # Vérifier si le compte est utilisé par des transactions
    if compte.transactions.count() > 0: # Utilise la relation backref
        flash('Impossible de supprimer ce compte car il est utilisé par des transactions.', 'danger')
        return redirect(url_for('plan_comptable.lister_comptes'))

    try:
        db.session.delete(compte)
        db.session.commit()
        flash('Compte comptable supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression du compte: {e}", 'danger')

    return redirect(url_for('plan_comptable.lister_comptes'))

