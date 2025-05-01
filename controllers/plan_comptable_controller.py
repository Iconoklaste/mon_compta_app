# controllers/plan_comptable_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from controllers.db_manager import db
from controllers.users_controller import login_required
# Importer les modèles nécessaires
from models import User, Organisation, CompteComptable, FinancialTransaction
# Importer l'Enum et le formulaire
from models.compte_comptable import ClasseCompte 
from forms.forms import CompteComptableForm 
from sqlalchemy.exc import IntegrityError
from collections import defaultdict # Pour regrouper les comptes par classe

# Ajuster le préfixe si vous préférez '/plan_comptable' au lieu de '/plan-comptable'
plan_comptable_bp = Blueprint('plan_comptable', __name__, url_prefix='/plan-comptable') 

# Descriptions courtes pour les classes (vous pouvez les améliorer)
# Mettez-les ici ou dans un fichier de configuration/constantes
classe_descriptions = {
    ClasseCompte.CLASSE_1: "Capitaux propres, réserves, résultat.",
    ClasseCompte.CLASSE_2: "Investissements durables (terrains, bâtiments, matériel...).",
    ClasseCompte.CLASSE_3: "Biens destinés à être vendus ou consommés.",
    ClasseCompte.CLASSE_4: "Créances (clients) et dettes (fournisseurs, état, personnel).",
    ClasseCompte.CLASSE_5: "Trésorerie (banques, caisse).",
    ClasseCompte.CLASSE_6: "Achats et frais consommés durant l'exercice.",
    ClasseCompte.CLASSE_7: "Ventes et revenus générés durant l'exercice.",
    ClasseCompte.CLASSE_8: "Comptes utilisés pour des opérations spécifiques (engagement...).",
}

@plan_comptable_bp.route('/')
@login_required
def lister_comptes():
    """Affiche la page du plan comptable avec la liste et les cards."""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation
    
    # Récupérer les comptes de l'organisation, triés par numéro
    comptes = CompteComptable.query.filter_by(organisation_id=organisation.id).order_by(CompteComptable.numero).all()
    
    # Formulaire vide pour le modal d'ajout
    form = CompteComptableForm() 

    # Préparer les données pour les cards
    classes_data = defaultdict(lambda: {"comptes": [], "actifs": 0, "description": ""})
    
    # Initialiser toutes les classes possibles
    for classe in ClasseCompte:
        classes_data[classe]["description"] = classe_descriptions.get(classe, "Pas de description.")

    # Remplir les données avec les comptes existants
    for compte in comptes:
        # Assurer que le type est bien un membre de l'Enum (pourrait être None si erreur DB)
        if isinstance(compte.type, ClasseCompte):
            classes_data[compte.type]["comptes"].append(compte)
            if compte.actif:
                classes_data[compte.type]["actifs"] += 1
        else:
             # Gérer le cas où compte.type n'est pas un Enum valide (log, ignorer, etc.)
             print(f"Attention: Compte ID {compte.id} a un type invalide: {compte.type}")


    # Convertir le defaultdict en dict normal pour le template si nécessaire (pas obligatoire)
    classes_data_dict = dict(classes_data)

    # Utiliser le template qui contient les cards ET le tableau
    # Adaptez le chemin si nécessaire ('compta/plan_comptable/list.html' ou autre)
    return render_template('compta/plan_comptable/plan_comptable_page.html',
                           organisation = organisation, 
                           comptes=comptes, 
                           form=form, # Passer le formulaire pour le modal d'ajout
                           classes_data=classes_data_dict, # Passer les données des cards
                           ClasseCompte=ClasseCompte, # Passer l'Enum pour accès dans le template
                           current_page='Plan Comptable') 

# Note: La route '/ajouter' est maintenant gérée par le modal dans la page principale,
# mais on garde une route POST distincte pour traiter la soumission du formulaire.

@plan_comptable_bp.route('/ajouter', methods=['POST'])
@login_required
def ajouter_compte_action():
    """Traite la soumission du formulaire d'ajout de compte."""
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
            # Si erreur, il faut recharger la page principale avec les données et le formulaire en erreur
            # pour que le modal puisse afficher les erreurs.
            show_add_modal = True # Indiquer au template de rouvrir le modal
        else:
            try:
                # Récupérer l'Enum membre basé sur le nom soumis par le formulaire
                classe_enum = ClasseCompte[form.type.data]

                nouveau_compte = CompteComptable(
                    numero=form.numero.data,
                    nom=form.nom.data,
                    type=classe_enum, # Assigner l'Enum membre
                    description=form.description.data,
                    # Récupérer le solde initial, mettre 0.0 si non fourni ou invalide
                    solde_initial=form.solde_initial.data if form.solde_initial.data is not None else 0.0,
                    actif=True, # Nouveau compte est actif par défaut
                    organisation_id=organisation.id 
                )
                db.session.add(nouveau_compte)
                db.session.commit()
                flash('Compte comptable ajouté avec succès!', 'success')
                return redirect(url_for('plan_comptable.lister_comptes')) # Rediriger vers la liste
            
            except KeyError:
                 db.session.rollback()
                 flash(f"Classe de compte invalide sélectionnée: {form.type.data}", "danger")
                 show_add_modal = True
            except IntegrityError: # Gère le cas où la contrainte DB est violée
                db.session.rollback()
                flash("Erreur lors de l'ajout du compte (possible doublon ou autre contrainte).", 'danger')
                show_add_modal = True
            except Exception as e:
                db.session.rollback()
                flash(f"Une erreur inattendue est survenue: {e}", 'danger')
                show_add_modal = True

    # Si GET (ne devrait pas arriver avec POST only), ou si validation WTForms échoue, ou si erreur custom (doublon, etc.)
    # Il faut recharger TOUTES les données nécessaires pour la page principale
    comptes = CompteComptable.query.filter_by(organisation_id=organisation.id).order_by(CompteComptable.numero).all()
    classes_data = defaultdict(lambda: {"comptes": [], "actifs": 0, "description": ""})
    for classe in ClasseCompte:
        classes_data[classe]["description"] = classe_descriptions.get(classe, "Pas de description.")
    for compte_item in comptes:
         if isinstance(compte_item.type, ClasseCompte):
             classes_data[compte_item.type]["comptes"].append(compte_item)
             if compte_item.actif:
                 classes_data[compte_item.type]["actifs"] += 1
    
    # Afficher les erreurs de validation WTForms
    if not show_add_modal: # Si on n'a pas déjà mis show_add_modal à True pour une erreur custom
        show_add_modal = bool(form.errors) # Rouvrir le modal s'il y a des erreurs WTForms
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur dans le champ '{getattr(form, field).label.text}': {error}", 'danger')

    return render_template('compta/plan_comptable/plan_comptable_page.html', 
                           form=form, # Passer le formulaire (avec erreurs potentielles)
                           comptes=comptes,
                           classes_data=dict(classes_data),
                           ClasseCompte=ClasseCompte,
                           show_add_modal=show_add_modal, # Passer l'indicateur au template
                           current_page='Plan Comptable')


@plan_comptable_bp.route('/modifier/<int:compte_id>', methods=['POST']) # Changé en POST only pour le traitement
@login_required
def modifier_compte_action(compte_id):
    """Traite la soumission du formulaire de modification de compte."""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation
    
    compte = CompteComptable.query.filter_by(id=compte_id, organisation_id=organisation.id).first_or_404()
    
    # Utiliser un formulaire distinct pour l'édition pourrait être plus propre, 
    # mais on réutilise le même pour l'instant.
    form = CompteComptableForm() 

    if form.validate_on_submit():
        # Vérification d'unicité si le numéro a changé
        if compte.numero != form.numero.data:
            existing_compte = CompteComptable.query.filter(
                CompteComptable.id != compte_id, # Exclure le compte actuel
                CompteComptable.numero == form.numero.data,
                CompteComptable.organisation_id == organisation.id
            ).first()
            if existing_compte:
                 flash(f"Le numéro de compte '{form.numero.data}' existe déjà pour un autre compte.", 'danger')
                 # Idéalement, rediriger vers la liste avec un paramètre pour rouvrir le modal d'édition avec l'erreur
                 return redirect(url_for('plan_comptable.lister_comptes') + f"?edit_error={compte_id}")

        try:
            # Récupérer l'Enum membre basé sur le nom soumis par le formulaire
            classe_enum = ClasseCompte[form.type.data]

            compte.numero = form.numero.data
            compte.nom = form.nom.data
            compte.type = classe_enum # Assigner l'Enum membre
            compte.description = form.description.data
            # Mettre à jour le solde initial
            compte.solde_initial = form.solde_initial.data if form.solde_initial.data is not None else compte.solde_initial
            # Le statut 'actif' n'est pas modifié ici, mais via une route dédiée
            
            db.session.commit()
            flash('Compte comptable modifié avec succès!', 'success')
            return redirect(url_for('plan_comptable.lister_comptes'))
        
        except KeyError:
             db.session.rollback()
             flash(f"Classe de compte invalide sélectionnée: {form.type.data}", "danger")
             return redirect(url_for('plan_comptable.lister_comptes') + f"?edit_error={compte_id}")
        except IntegrityError:
            db.session.rollback()
            flash("Erreur lors de la modification du compte (possible doublon ou autre contrainte).", 'danger')
            return redirect(url_for('plan_comptable.lister_comptes') + f"?edit_error={compte_id}")
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur inattendue est survenue: {e}", 'danger')
            return redirect(url_for('plan_comptable.lister_comptes') + f"?edit_error={compte_id}")

    # Si la validation WTForms échoue lors de la soumission POST du modal d'édition
    flash("Erreur de validation lors de la modification.", 'danger')
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Erreur dans le champ '{getattr(form, field).label.text}': {error}", 'danger')
    # Rediriger vers la page principale, idéalement avec un moyen de rouvrir le modal d'édition
    return redirect(url_for('plan_comptable.lister_comptes') + f"?edit_error={compte_id}")

# Il n'y a plus de route GET pour /modifier/<id> car le formulaire est dans un modal sur la page principale.
# Le pré-remplissage du modal se fait via JavaScript.

@plan_comptable_bp.route('/toggle-actif/<int:compte_id>', methods=['POST'])
@login_required
def toggle_actif_compte(compte_id):
    """Active ou désactive un compte."""
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    compte = CompteComptable.query.filter_by(id=compte_id, organisation_id=organisation.id).first_or_404()

    try:
        compte.actif = not compte.actif
        statut = "activé" if compte.actif else "désactivé"
        db.session.commit()
        flash(f'Compte "{compte.numero} - {compte.nom}" {statut}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du changement de statut : {e}', 'danger')

    return redirect(url_for('plan_comptable.lister_comptes'))


@plan_comptable_bp.route('/supprimer/<int:compte_id>', methods=['POST'])
@login_required
def supprimer_compte(compte_id):
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    organisation = user.organisation

    compte = CompteComptable.query.filter_by(id=compte_id, organisation_id=organisation.id).first_or_404()

    # Vérifier si le compte est utilisé par des transactions
    # Utiliser .first() est plus efficace que .count() si on veut juste savoir s'il y en a au moins une
    transaction_existante = FinancialTransaction.query.filter_by(compte_id=compte.id).first()
    if transaction_existante: 
        flash(f'Impossible de supprimer le compte "{compte.numero} - {compte.nom}" car il est utilisé par au moins une transaction.', 'warning')
        return redirect(url_for('plan_comptable.lister_comptes'))

    try:
        nom_compte = f"{compte.numero} - {compte.nom}" # Garder une trace avant suppression
        db.session.delete(compte)
        db.session.commit()
        flash(f'Compte comptable "{nom_compte}" supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression du compte: {e}", 'danger')

    return redirect(url_for('plan_comptable.lister_comptes'))

