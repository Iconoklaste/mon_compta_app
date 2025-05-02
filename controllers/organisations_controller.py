from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, session, current_app, flash
from controllers.db_manager import db
from controllers.users_controller import login_required
from models import Organisation, User
from forms.forms import OrganisationForm  # Import the OrganisationForm
from werkzeug.utils import secure_filename
from io import BytesIO
import os
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # Importer les erreurs SQLAlchemy
import logging # Importer logging

# --- Importer la fonction de génération du plan comptable ---
from utils.plan_comptable_initial_setup import generate_default_plan_comptable
# --------------------------------------------------------------------


organisations_bp = Blueprint('organisations', __name__, url_prefix='/organisations')
# Configuration du logger pour ce contrôleur
logger = logging.getLogger(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@organisations_bp.route('/ajouter_organisation', methods=['POST'])
def ajouter_organisation():
    form = OrganisationForm()  # Create an instance of the form

    if form.validate_on_submit():
        try:
            logo_data = None
            logo_mimetype = None

            if form.logo.data:
                try:
                    logo_data = form.logo.data.read()
                    logo_mimetype = form.logo.data.mimetype
                except ValueError as e:
                    return jsonify({'success': False, 'error': str(e)}), 400

            # Création de l'organisation
            new_organisation = Organisation(
                designation=form.designation.data,
                siret=form.siret.data,
                exonere_tva=form.exonere_tva.data,
                tva_intracommunautaire=form.tva_intracommunautaire.data,
                forme_juridique=form.forme_juridique.data,
                adresse=form.adresse.data,
                code_postal=form.code_postal.data,
                ville=form.ville.data,
                telephone=form.telephone.data,
                mail_contact=form.mail_contact.data,
                iban=form.iban.data,
                bic=form.bic.data,
                logo=logo_data,
                logo_mimetype=logo_mimetype
            )

            db.session.add(new_organisation)
            db.session.commit()

            return jsonify({'success': True, 'organisation_id': new_organisation.id}), 201  # 201 Created
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        # Handle form validation errors
        errors = {field: errors for field, errors in form.errors.items()}
        return jsonify({'success': False, 'errors': errors}), 400

@organisations_bp.route('/modifier_organisation', methods=['GET', 'POST'])
@login_required
def modifier_organisation():
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation
    form = OrganisationForm(obj=organisation)

    if form.validate_on_submit():
        organisation.designation = form.designation.data
        organisation.siret = form.siret.data
        organisation.exonere_tva = form.exonere_tva.data
        organisation.tva_intracommunautaire = form.tva_intracommunautaire.data
        organisation.forme_juridique = form.forme_juridique.data
        organisation.adresse = form.adresse.data
        organisation.code_postal = form.code_postal.data
        organisation.ville = form.ville.data
        organisation.telephone = form.telephone.data
        organisation.mail_contact = form.mail_contact.data
        organisation.iban = form.iban.data
        organisation.bic = form.bic.data

        # Handle logo upload
        if form.logo.data:
            logo_file = request.files.get(form.logo.name)
            if logo_file and logo_file.filename != '':
                try:
                    logo_data = logo_file.read()
                    # Validate size (optional here, but good practice)
                    organisation.validate_logo('logo', logo_data) # Use the validator
                    organisation.logo = logo_data
                    organisation.logo_mimetype = logo_file.mimetype
                except ValueError as e:
                    flash(str(e), 'danger')
                    return render_template('modifier_organisation.html', organisation=organisation, form=form)

        db.session.commit()
        flash('Organisation modifiée avec succès!', 'success')
        return redirect(url_for('users.index'))
    else:
        # Handle form validation errors
        return render_template('modifier_organisation.html', organisation=organisation, form=form)

@organisations_bp.route('/get_logo/<int:organisation_id>', endpoint='get_logo')
def get_logo(organisation_id):
    organisation = Organisation.query.get_or_404(organisation_id)
    if organisation.logo:
        response = make_response(organisation.logo)
        response.headers.set('Content-Type', organisation.logo_mimetype)
        return response
    else:
        return "Logo not found", 404

# --- NOUVELLE ROUTE pour l'étape 2 de l'inscription démo ---
@organisations_bp.route('/creer-compte-demo/etape-2', methods=['GET', 'POST'])
def ajouter_organisation_demo():
    """Affiche et traite le formulaire d'informations organisation (Étape 2)."""
    # Vérifier si les données de l'utilisateur de l'étape 1 sont bien en session
    if 'demo_user_data' not in session:
        logger.warning("Tentative d'accès à l'étape 2 sans données utilisateur en session.")
        flash("Erreur : session utilisateur perdue. Veuillez recommencer depuis l'étape 1.", 'danger')
        return redirect(url_for('users.ajouter_user_demo'))

    form = OrganisationForm()

    # --- Récupérer la config AVANT d'appeler render_template ---
    # Calculer la taille max du logo en Ko pour l'affichage dans le template
    max_logo_size_kb = int(current_app.config.get('MAX_LOGO_SIZE', 1024*1024) / 1024)

    if form.validate_on_submit():
        # Récupérer les données utilisateur de la session
        user_data = session['demo_user_data']
        logger.info(f"Traitement de l'étape 2 pour l'utilisateur potentiel : {user_data.get('mail')}")

        # --- Création de l'organisation et de l'utilisateur ---
        try:
            logo_data = None
            logo_mimetype = None
            if form.logo.data:
                logger.debug("Traitement du logo uploadé.")
                try:
                    # Lire les données du fichier et vérifier la taille (la validation est dans le modèle)
                    logo_data = form.logo.data.read()
                    logo_mimetype = form.logo.data.mimetype
                    # Rembobiner le fichier si besoin
                    form.logo.data.seek(0)
                    logger.info(f"Logo lu : {len(logo_data)} bytes, type: {logo_mimetype}")
                except ValueError as e: # Erreur de taille du logo levée par le validateur du modèle
                    logger.warning(f"Erreur de validation du logo : {e}")
                    flash(f"Erreur avec le logo : {e}", 'danger')
                    # === PASSER LA CONFIG ICI AUSSI ===
                    return render_template('ajouter_organisation_demo.html', form=form, max_logo_size_kb=max_logo_size_kb)
                except Exception as e:
                    logger.error(f"Erreur inattendue lors de la lecture du logo : {e}", exc_info=True)
                    flash(f"Erreur lors de la lecture du logo : {e}", 'danger')
                    # === PASSER LA CONFIG ICI AUSSI ===
                    return render_template('ajouter_organisation_demo.html', form=form, max_logo_size_kb=max_logo_size_kb)

            # --- AJOUT/CORRECTION ICI ---
            # Convertir la chaîne vide en None pour tva_intracommunautaire
            tva_intra_value = form.tva_intracommunautaire.data if form.tva_intracommunautaire.data else None
            # --------------------------

            # 1. Créer l'objet Organisation
            new_organisation = Organisation(
                designation=form.designation.data,
                siret=form.siret.data,
                exonere_tva=form.exonere_tva.data,
                # --- Utiliser la valeur convertie ---
                tva_intracommunautaire=tva_intra_value,
                # ------------------------------------
                forme_juridique=form.forme_juridique.data,
                adresse=form.adresse.data,
                code_postal=form.code_postal.data,
                ville=form.ville.data,
                telephone=form.telephone.data,
                mail_contact=form.mail_contact.data,
                iban=form.iban.data,
                bic=form.bic.data,
                logo=logo_data,
                logo_mimetype=logo_mimetype
            )
            db.session.add(new_organisation)
            logger.info(f"Objet Organisation créé pour '{new_organisation.designation}'.")

            # 2. Créer l'objet Utilisateur
            new_user = User(
                nom=user_data['nom'],
                prenom=user_data['prenom'],
                mail=user_data['mail'],
                telephone=user_data['telephone'],
                organisation=new_organisation # Lier l'organisation créée
                # role='user' # ou le rôle par défaut si tu as un champ rôle
            )
            # Hasher le mot de passe avant de le sauvegarder
            new_user.set_password(user_data['password']) # Assure-toi que ta classe User a cette méthode
            db.session.add(new_user)
            logger.info(f"Objet User créé pour '{new_user.mail}'.")

            # --- Commit des deux objets (Organisation et User) ---
            try:
                db.session.commit()
                logger.info(f"Organisation ID {new_organisation.id} et User ID {new_user.id} commitées en base.")
                flash('Organisation et utilisateur créés avec succès !', 'success')
                session['user_id'] = new_user.id
                logger.info(f"Utilisateur ID {new_user.id} ajouté à la session (connecté).")
            except IntegrityError as ie: # Gère les erreurs d'unicité (SIRET, email user, etc.)
                db.session.rollback()
                logger.warning(f"Erreur d'intégrité lors du commit : {ie}")
                error_info = str(ie.orig)
                if 'uq_organisation_siret' in error_info or 'siret' in error_info.lower():
                     flash("Erreur : Ce numéro SIRET est déjà utilisé par une autre organisation.", 'danger')
                     form.siret.errors.append("Ce SIRET est déjà utilisé.")
                elif 'uq_user_mail' in error_info or 'mail' in error_info.lower():
                     flash("Erreur : Cet email utilisateur est déjà utilisé.", 'danger')
                     # Rediriger vers l'étape 1 pour changer l'email ? Ou afficher ici ?
                # --- CORRECTION : Vérifier aussi la contrainte TVA ---
                elif 'uq_organisation_tva_intracommunautaire' in error_info or 'tva_intracommunautaire' in error_info.lower():
                     flash("Erreur : Ce numéro TVA intracommunautaire est déjà utilisé.", 'danger')
                     form.tva_intracommunautaire.errors.append("Ce numéro TVA est déjà utilisé.")
                # ----------------------------------------------------
                else:
                     flash(f"Erreur de base de données (contrainte) lors de la création.", 'danger')
                # === PASSER LA CONFIG ICI AUSSI ===
                return render_template('ajouter_organisation_demo.html', form=form, max_logo_size_kb=max_logo_size_kb)
            except SQLAlchemyError as se: # Autres erreurs SQLAlchemy
                db.session.rollback()
                logger.error(f"Erreur SQLAlchemy lors du commit : {se}", exc_info=True)
                flash("Erreur de base de données lors de l'enregistrement.", 'danger')
                # === PASSER LA CONFIG ICI AUSSI ===
                return render_template('ajouter_organisation_demo.html', form=form, max_logo_size_kb=max_logo_size_kb)


            # --- Génération du plan comptable par défaut ---
            # Cette partie est exécutée SEULEMENT si le commit a réussi
            try:
                logger.info(f"Appel de generate_default_plan_comptable pour Organisation ID {new_organisation.id}")
                comptes_crees = generate_default_plan_comptable(new_organisation)
                if comptes_crees is not None:
                     logger.info(f"{len(comptes_crees)} comptes générés pour Organisation ID {new_organisation.id}")
                     flash(f"{len(comptes_crees)} comptes comptables par défaut ont été générés.", 'info')
                else:
                     logger.error(f"generate_default_plan_comptable a retourné None pour Organisation ID {new_organisation.id}")
                     flash("Attention : Une erreur est survenue lors de la génération du plan comptable par défaut. Contactez l'administrateur.", 'warning')
            except Exception as e:
                 logger.error(f"Erreur imprévue lors de l'appel à generate_default_plan_comptable pour Org ID {new_organisation.id}: {e}", exc_info=True)
                 flash("Attention : Une erreur critique est survenue pendant la configuration initiale du compte.", 'danger')


            # Nettoyer la session
            session.pop('demo_user_data', None)
            logger.debug("Données temporaires 'demo_user_data' nettoyées de la session.")

            # Rediriger vers la page de connexion
            flash("Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('projets.projets'))

        except Exception as e: # Attrape les erreurs générales avant le commit
            db.session.rollback()
            logger.error(f"Erreur générale lors de la création organisation/user demo: {e}", exc_info=True)
            flash(f"Une erreur inattendue est survenue : {e}", 'danger')
            # === PASSER LA CONFIG ICI AUSSI ===
            return render_template('ajouter_organisation_demo.html', form=form, max_logo_size_kb=max_logo_size_kb)

    # Si GET ou si validation du formulaire organisation échoue
    user_info_for_display = session.get('demo_user_data', {}).copy()
    user_info_for_display.pop('password', None)
    # === PASSER LA CONFIG ICI (cas GET) ===
    return render_template('ajouter_organisation_demo.html',
                           form=form,
                           user_info=user_info_for_display, # Passe la copie modifiée
                           max_logo_size_kb=max_logo_size_kb)