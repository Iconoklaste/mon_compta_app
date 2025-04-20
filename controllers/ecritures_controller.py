# controllers/ecritures_controller.py

from flask import Blueprint, render_template, session, redirect, url_for, flash
from sqlalchemy.orm import joinedload, selectinload # Pour optimiser le chargement des relations
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import User, EcritureComptable, LigneEcriture, CompteComptable # Importer les modèles nécessaires

# Créer un Blueprint pour les écritures
ecritures_bp = Blueprint('ecritures', __name__, url_prefix='/ecritures')

@ecritures_bp.route('/')
@login_required
def lister_ecritures():
    """Affiche la liste des écritures comptables pour l'organisation de l'utilisateur."""
    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if not user or not user.organisation_id:
            flash("Utilisateur ou organisation non trouvé.", "warning")
            return redirect(url_for('users.index')) # Ou une autre page appropriée

        organisation_id = user.organisation_id

        # Récupérer les écritures de l'organisation, triées par date (la plus récente d'abord)
        # On utilise selectinload pour charger efficacement les lignes et les comptes associés
        ecritures = EcritureComptable.query.filter_by(organisation_id=organisation_id)\
            .options(
                selectinload(EcritureComptable.lignes) # Charger toutes les lignes de chaque écriture
                .selectinload(LigneEcriture.compte)    # Charger le compte associé à chaque ligne
            )\
            .order_by(EcritureComptable.date_ecriture.desc(), EcritureComptable.id.desc())\
            .all()

        return render_template('compta/ecritures/liste_ecritures.html',
                               ecritures=ecritures,
                               organisation_id=organisation_id,
                               current_page='Ecritures Comptables')

    except Exception as e:
        # Logguer l'erreur serait bien ici
        print(f"Erreur lors de la récupération des écritures: {e}") # Simple print pour le debug
        flash("Une erreur est survenue lors du chargement des écritures.", "danger")
        return redirect(url_for('compta.index')) # Rediriger vers le tableau de bord compta

