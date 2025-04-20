# reports/report_generators.py

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload # Pour charger les relations efficacement
# Importer ExerciceComptable si ce n'est pas déjà fait
from models import CompteComptable, LigneEcriture, EcritureComptable, Organisation, ExerciceComptable
from models.compte_comptable import ClasseCompte # Importer l'Enum
from controllers.db_manager import db
from datetime import date, timedelta
from collections import defaultdict # Utile pour agréger les totaux
import logging # Pour logger les erreurs potentielles

logger = logging.getLogger(__name__)

def _calculate_account_balance(compte_id: int, date_fin: date, session):
    """
    Calcule le solde cumulatif d'un compte à une date donnée.
    Solde = Solde Initial + SUM(Débits jusqu'à date_fin) - SUM(Crédits jusqu'à date_fin)
    (Ajout du paramètre session pour réutiliser la session existante)
    """
    # session = db.session # On utilise la session passée en argument
    compte = session.query(CompteComptable).get(compte_id)
    if not compte:
        logger.warning(f"Compte ID {compte_id} non trouvé lors du calcul du solde.")
        return 0.0 # Ou lever une exception

    solde_initial = compte.solde_initial or 0.0

    # Calculer la somme des débits et crédits jusqu'à la date_fin
    resultats = session.query(
        func.sum(LigneEcriture.montant_debit).label('total_debit'),
        func.sum(LigneEcriture.montant_credit).label('total_credit')
    ).join(EcritureComptable, LigneEcriture.ecriture_id == EcritureComptable.id)\
    .filter(
        LigneEcriture.compte_id == compte_id,
        EcritureComptable.date_ecriture <= date_fin
    ).one()

    total_debit = resultats.total_debit or 0.0
    total_credit = resultats.total_credit or 0.0

    # Le solde est calculé comme Débit - Crédit (convention comptable)
    # Un solde positif signifie Débiteur, négatif signifie Créditeur.
    # MAIS pour le bilan, on raisonne souvent en valeur absolue.
    # Le calcul ici est Solde = Initial + Mouvements Débit - Mouvements Crédit
    solde_calcule = solde_initial + total_debit - total_credit
    return solde_calcule

def _calculate_net_income(organisation_id: int, date_debut_exercice: date, date_fin_bilan: date, session):
    """
    Calcule le résultat net (Produits - Charges) sur une période donnée.
    """
    # session = db.session # On utilise la session passée en argument

    # 1. Calculer Total Produits (Classe 7) sur la période
    produits_result = session.query(
        func.sum(LigneEcriture.montant_credit).label('total_credit_p'),
        func.sum(LigneEcriture.montant_debit).label('total_debit_p')
    ).join(EcritureComptable, LigneEcriture.ecriture_id == EcritureComptable.id)\
    .join(CompteComptable, LigneEcriture.compte_id == CompteComptable.id)\
    .filter(
        CompteComptable.organisation_id == organisation_id,
        CompteComptable.type == ClasseCompte.CLASSE_7, # Filtrer sur la classe 7
        EcritureComptable.date_ecriture >= date_debut_exercice,
        EcritureComptable.date_ecriture <= date_fin_bilan
    ).one()
    total_produits = (produits_result.total_credit_p or 0.0) - (produits_result.total_debit_p or 0.0)

    # 2. Calculer Total Charges (Classe 6) sur la période
    charges_result = session.query(
        func.sum(LigneEcriture.montant_debit).label('total_debit_c'),
        func.sum(LigneEcriture.montant_credit).label('total_credit_c')
    ).join(EcritureComptable, LigneEcriture.ecriture_id == EcritureComptable.id)\
    .join(CompteComptable, LigneEcriture.compte_id == CompteComptable.id)\
    .filter(
        CompteComptable.organisation_id == organisation_id,
        CompteComptable.type == ClasseCompte.CLASSE_6, # Filtrer sur la classe 6
        EcritureComptable.date_ecriture >= date_debut_exercice,
        EcritureComptable.date_ecriture <= date_fin_bilan
    ).one()
    total_charges = (charges_result.total_debit_c or 0.0) - (charges_result.total_credit_c or 0.0)

    # 3. Calculer le Résultat Net
    resultat_net = total_produits - total_charges
    return resultat_net


def generate_balance_sheet(organisation_id: int, date_fin: date):
    """
    Génère les données pour le Bilan Comptable d'une organisation à une date donnée.
    """
    session = db.session # Utiliser une seule session pour toutes les requêtes
    organisation = session.query(Organisation).get(organisation_id)
    if not organisation:
        raise ValueError(f"Organisation avec ID {organisation_id} non trouvée.")

    # --- Trouver l'exercice comptable pertinent ---
    exercice_pertinent = session.query(ExerciceComptable).filter(
        ExerciceComptable.organisation_id == organisation_id,
        ExerciceComptable.date_debut <= date_fin,
        ExerciceComptable.date_fin >= date_fin # La date_fin du bilan doit être dans l'exercice
        # Optionnel: Ajouter un filtre sur le statut si nécessaire (ex: 'Ouvert')
        # ExerciceComptable.statut == "Ouvert"
    ).order_by(ExerciceComptable.date_debut.desc()).first() # Prendre le plus récent si chevauchement

    if not exercice_pertinent:
        # Que faire si aucun exercice ne correspond ?
        # Option 1: Lever une erreur
        # raise ValueError(f"Aucun exercice comptable trouvé pour l'organisation {organisation_id} contenant la date {date_fin}")
        # Option 2: Essayer de prendre le dernier exercice clôturé ? (Complexe)
        # Option 3: Calculer le résultat depuis le début de l'historique ? (Peut être faux)
        # Pour l'instant, on loggue un warning et on calcule sans résultat (ou avec résultat = 0)
        logger.warning(f"Aucun exercice comptable trouvé pour l'organisation {organisation_id} contenant la date {date_fin}. Le résultat ne sera pas calculé.")
        date_debut_exercice_pour_resultat = None
        resultat_net_exercice = 0.0
    else:
        date_debut_exercice_pour_resultat = exercice_pertinent.date_debut
        # Calculer le résultat net pour la période de l'exercice jusqu'à date_fin
        resultat_net_exercice = _calculate_net_income(
            organisation_id,
            date_debut_exercice_pour_resultat,
            date_fin,
            session # Passer la session
        )

    # 1. Récupérer tous les comptes actifs de l'organisation (Classes 1 à 5 pour le Bilan)
    comptes_bilan = session.query(CompteComptable).filter(
        CompteComptable.organisation_id == organisation_id,
        CompteComptable.actif == True,
        CompteComptable.type.in_([
            ClasseCompte.CLASSE_1,
            ClasseCompte.CLASSE_2,
            ClasseCompte.CLASSE_3,
            ClasseCompte.CLASSE_4,
            ClasseCompte.CLASSE_5
        ])
    ).order_by(CompteComptable.numero).all()

    actif_details = []
    passif_details = []
    capitaux_propres_details = []

    # 2. Calculer le solde pour chaque compte et le classifier
    for compte in comptes_bilan:
        # Utiliser la session existante pour le calcul du solde
        solde = _calculate_account_balance(compte.id, date_fin, session)

        # Ignorer les comptes avec solde nul (sauf si c'est un compte important comme Capital)
        # Affiner cette condition si nécessaire
        if abs(solde) < 0.001 and not compte.numero.startswith('101'): # Exemple: garder le capital même si nul
             continue

        compte_data = {
            'numero': compte.numero,
            'nom': compte.nom,
            # On stocke le solde calculé (positif = débiteur, négatif = créditeur)
            'solde': solde
        }

        classe = compte.type

        # 3. Classification affinée
        if classe in [ClasseCompte.CLASSE_2, ClasseCompte.CLASSE_3, ClasseCompte.CLASSE_5]:
            # Actifs (Immobilisations, Stocks, Financiers)
            # Normalement solde débiteur (positif). Si négatif (ex: découvert bancaire), reste à l'actif mais en négatif ou à reclasser au passif selon les normes.
            # Simplification : on garde à l'actif.
            actif_details.append(compte_data)
        elif classe == ClasseCompte.CLASSE_4:
            # Comptes de Tiers
            if solde > 0: # Solde débiteur -> Créance (Actif)
                actif_details.append(compte_data)
            elif solde < 0: # Solde créditeur -> Dette (Passif)
                # Pour l'affichage au passif, on prendra la valeur absolue.
                passif_details.append(compte_data)
        elif classe == ClasseCompte.CLASSE_1:
            # Capitaux, Réserves, Report à nouveau, Dettes LT (assimilées)
            # Normalement solde créditeur (négatif).
            # Si positif (ex: Report à nouveau débiteur), il vient en déduction des CP.
            capitaux_propres_details.append(compte_data)

    # 4. Ajouter le Résultat Net calculé aux Capitaux Propres
    # Le résultat est un bénéfice si positif, une perte si négatif.
    # Comptablement, un bénéfice augmente les CP (crédit), une perte les diminue (débit).
    # Notre solde CP est déjà négatif si créditeur.
    # Donc, on ajoute le résultat * (-1) pour l'intégrer correctement.
    # Exemple: CP = -1000 (créditeur), Résultat = +200 (bénéfice) => Nouveau CP = -1000 + (-1 * 200) = -1200
    # Exemple: CP = -1000 (créditeur), Résultat = -100 (perte)    => Nouveau CP = -1000 + (-1 * -100) = -900
    capitaux_propres_details.append({
        'numero': '120/129', # Numéro conventionnel pour le résultat
        'nom': "Résultat de l'exercice (Bénéfice ou Perte)",
        'solde': -resultat_net_exercice # Inverser le signe pour l'ajouter aux CP créditeurs
    })

    # 5. Calculer les totaux finaux
    # Actif : Somme des soldes débiteurs (positifs) + soldes créditeurs (négatifs) des comptes d'actif
    total_actif = sum(c['solde'] for c in actif_details)

    # Passif : Somme des valeurs absolues des soldes créditeurs (négatifs) des comptes de passif
    total_passif = sum(-c['solde'] for c in passif_details if c['solde'] < 0) \
                 + sum(c['solde'] for c in passif_details if c['solde'] > 0) # Gérer cas rare de passif débiteur

    # Capitaux Propres : Somme des valeurs absolues des soldes créditeurs (négatifs)
    #                    moins les soldes débiteurs (positifs)
    total_capitaux_propres = sum(-c['solde'] for c in capitaux_propres_details if c['solde'] < 0) \
                           - sum(c['solde'] for c in capitaux_propres_details if c['solde'] > 0)

    # 6. Vérification de l'équilibre (avec une petite tolérance pour les flottants)
    equilibre = abs(total_actif - (total_passif + total_capitaux_propres)) < 0.01 # Tolérance de 1 centime

    # 7. Retourner la structure de données complète
    return {
        'organisation_nom': organisation.designation,
        'date_fin': date_fin.strftime('%Y-%m-%d'),
        'exercice_debut': date_debut_exercice_pour_resultat.strftime('%Y-%m-%d') if date_debut_exercice_pour_resultat else "N/A",
        'actif': {
            'details': sorted(actif_details, key=lambda x: x['numero']), # Trier par numéro
            'total': total_actif
        },
        'passif': {
            'details': sorted(passif_details, key=lambda x: x['numero']), # Trier par numéro
            'total': total_passif
        },
        'capitaux_propres': {
            'details': sorted(capitaux_propres_details, key=lambda x: x['numero']), # Trier par numéro
            'total': total_capitaux_propres
        },
        'resultat_net_exercice': resultat_net_exercice, # Le résultat calculé
        'equilibre': equilibre, # True si Actif = Passif + CP
        'desequilibre': total_actif - (total_passif + total_capitaux_propres) if not equilibre else 0.0
    }

def generate_income_statement(organisation_id: int, date_debut: date, date_fin: date):
    """
    Génère les données pour le Compte de Résultat d'une organisation sur une période donnée.
    """
    session = db.session
    organisation = session.query(Organisation).get(organisation_id)
    if not organisation:
        raise ValueError(f"Organisation avec ID {organisation_id} non trouvée.")

    # Vérifier que les dates sont valides
    if not date_debut or not date_fin or date_debut > date_fin:
        raise ValueError("Les dates de début et de fin sont invalides ou manquantes.")

    # 1. Récupérer tous les comptes de Charges (Classe 6) et Produits (Classe 7) actifs
    comptes_resultat = session.query(CompteComptable).filter(
        CompteComptable.organisation_id == organisation_id,
        CompteComptable.actif == True,
        CompteComptable.type.in_([
            ClasseCompte.CLASSE_6,
            ClasseCompte.CLASSE_7
        ])
    ).order_by(CompteComptable.numero).all()

    charges_details = []
    produits_details = []

    # 2. Calculer le solde de chaque compte SUR LA PÉRIODE demandée
    for compte in comptes_resultat:
        # Calculer la somme des débits et crédits UNIQUEMENT sur la période [date_debut, date_fin]
        mouvements_periode = session.query(
            func.sum(LigneEcriture.montant_debit).label('total_debit'),
            func.sum(LigneEcriture.montant_credit).label('total_credit')
        ).join(EcritureComptable, LigneEcriture.ecriture_id == EcritureComptable.id)\
        .filter(
            LigneEcriture.compte_id == compte.id,
            EcritureComptable.date_ecriture >= date_debut,
            EcritureComptable.date_ecriture <= date_fin
        ).one()

        total_debit_periode = mouvements_periode.total_debit or 0.0
        total_credit_periode = mouvements_periode.total_credit or 0.0

        # Calcul du solde du compte SUR LA PÉRIODE
        # Pour les charges (Classe 6), solde = Débits - Crédits (normalement positif)
        # Pour les produits (Classe 7), solde = Crédits - Débits (normalement positif)
        solde_periode = 0.0
        if compte.type == ClasseCompte.CLASSE_6:
            solde_periode = total_debit_periode - total_credit_periode
        elif compte.type == ClasseCompte.CLASSE_7:
            solde_periode = total_credit_periode - total_debit_periode

        # Ignorer les comptes sans mouvement sur la période
        if abs(solde_periode) < 0.001:
            continue

        compte_data = {
            'numero': compte.numero,
            'nom': compte.nom,
            'solde_periode': solde_periode # Solde calculé sur la période
        }

        # 3. Classifier dans la bonne liste
        if compte.type == ClasseCompte.CLASSE_6:
            charges_details.append(compte_data)
        elif compte.type == ClasseCompte.CLASSE_7:
            produits_details.append(compte_data)

    # 4. Calculer les totaux et le résultat net
    total_charges = sum(c['solde_periode'] for c in charges_details)
    total_produits = sum(p['solde_periode'] for p in produits_details)
    resultat_net = total_produits - total_charges

    # 5. Retourner la structure de données
    return {
        'organisation_nom': organisation.designation,
        'date_debut': date_debut.strftime('%Y-%m-%d'),
        'date_fin': date_fin.strftime('%Y-%m-%d'),
        'charges': {
            'details': sorted(charges_details, key=lambda x: x['numero']), # Trier par numéro
            'total': total_charges
        },
        'produits': {
            'details': sorted(produits_details, key=lambda x: x['numero']), # Trier par numéro
            'total': total_produits
        },
        'resultat_net': resultat_net,
        'type_resultat': "Bénéfice" if resultat_net >= 0 else "Perte"
    }

def generate_general_ledger(organisation_id: int, date_debut: date, date_fin: date):
    """
    Génère les données pour le Grand Livre d'une organisation sur une période donnée.
    Liste toutes les écritures par compte.
    """
    session = db.session
    organisation = session.query(Organisation).get(organisation_id)
    if not organisation:
        raise ValueError(f"Organisation avec ID {organisation_id} non trouvée.")

    if not date_debut or not date_fin or date_debut > date_fin:
        raise ValueError("Les dates de début et de fin sont invalides ou manquantes.")

    # 1. Identifier les comptes pertinents
    #    Ce sont les comptes qui ont soit un solde initial non nul avant date_debut,
    #    soit des mouvements entre date_debut et date_fin.
    #    (Approche simplifiée pour commencer : prendre tous les comptes actifs)
    #    Une optimisation serait de filtrer plus précisément.
    comptes_actifs = session.query(CompteComptable).filter(
        CompteComptable.organisation_id == organisation_id,
        CompteComptable.actif == True
    ).order_by(CompteComptable.numero).all()

    grand_livre_data = []

    # 2. Pour chaque compte...
    for compte in comptes_actifs:
        # 2.a. Calculer le solde initial (solde *avant* date_debut)
        #     On peut réutiliser _calculate_account_balance avec date_fin = date_debut - 1 jour
        #     Attention à la gestion des dates (timedelta)
        from datetime import timedelta
        date_veille_debut = date_debut - timedelta(days=1)
        solde_initial_periode = _calculate_account_balance(compte.id, date_veille_debut, session)

        # 2.b. Récupérer toutes les lignes d'écriture pour ce compte DANS la période
        lignes_ecriture_periode = session.query(LigneEcriture).join(
            EcritureComptable, LigneEcriture.ecriture_id == EcritureComptable.id
        ).options(
            joinedload(LigneEcriture.ecriture) # Charger l'écriture associée pour accès facile au libellé/date
        ).filter(
            LigneEcriture.compte_id == compte.id,
            EcritureComptable.date_ecriture >= date_debut,
            EcritureComptable.date_ecriture <= date_fin
        ).order_by(EcritureComptable.date_ecriture, EcritureComptable.id, LigneEcriture.id).all() # Trier par date, puis ID pour cohérence

        # 2.c. Si pas de solde initial ET pas de mouvement, on peut ignorer ce compte pour le rapport
        if abs(solde_initial_periode) < 0.001 and not lignes_ecriture_periode:
            continue

        # 2.d. Calculer les totaux des mouvements de la période
        total_debit_periode = sum(ligne.montant_debit for ligne in lignes_ecriture_periode)
        total_credit_periode = sum(ligne.montant_credit for ligne in lignes_ecriture_periode)

        # 2.e. Calculer le solde final
        solde_final_periode = solde_initial_periode + total_debit_periode - total_credit_periode

        # 2.f. Préparer les données pour ce compte
        compte_data = {
            'compte_id': compte.id,
            'numero': compte.numero,
            'nom': compte.nom,
            'solde_initial': solde_initial_periode,
            'mouvements': [],
            'total_debit_periode': total_debit_periode,
            'total_credit_periode': total_credit_periode,
            'solde_final': solde_final_periode
        }

        # Formater les lignes d'écriture pour l'affichage
        solde_courant = solde_initial_periode # Pour calculer le solde après chaque ligne (optionnel)
        for ligne in lignes_ecriture_periode:
            solde_courant += ligne.montant_debit - ligne.montant_credit
            compte_data['mouvements'].append({
                'date': ligne.ecriture.date_ecriture.strftime('%Y-%m-%d'),
                'libelle_ecriture': ligne.ecriture.libelle,
                'libelle_ligne': ligne.libelle, # Libellé spécifique à la ligne
                'reference_origine': ligne.ecriture.reference_origine,
                #'journal': ligne.ecriture.journal.code if ligne.ecriture.journal else 'N/A', # Si tu as un modèle Journal lié
                'debit': ligne.montant_debit,
                'credit': ligne.montant_credit,
                'solde_apres_ligne': solde_courant # Optionnel: afficher le solde progressif
            })

        grand_livre_data.append(compte_data)

    # 3. Retourner la liste des données par compte
    return {
        'organisation_nom': organisation.designation,
        'date_debut': date_debut.strftime('%Y-%m-%d'),
        'date_fin': date_fin.strftime('%Y-%m-%d'),
        'comptes_detail': grand_livre_data # Liste des détails par compte
    }
def _classify_cash_flow(ecriture: EcritureComptable, cash_account_ids: set):
    """
    Tente de classifier le flux de trésorerie d'une écriture donnée.
    Analyse les lignes de contrepartie par rapport aux lignes de trésorerie.

    Args:
        ecriture: L'objet EcritureComptable à analyser.
        cash_account_ids: Un set contenant les IDs des comptes de trésorerie.

    Returns:
        Un tuple: (category, description, amount)
        category (str): 'OPERATING', 'INVESTING', 'FINANCING', 'TRANSFER', 'UNKNOWN'.
        description (str): Une description du flux détecté.
        amount (float): Le montant du mouvement de trésorerie (positif pour entrée, négatif pour sortie).
    """
    cash_movement = 0.0
    counterparty_lines = []

    # Séparer les lignes de trésorerie des autres lignes (contreparties)
    for ligne in ecriture.lignes:
        if ligne.compte_id in cash_account_ids:
            # Somme des débits moins crédits sur les comptes de trésorerie
            cash_movement += (ligne.montant_debit or 0.0) - (ligne.montant_credit or 0.0)
        else:
            counterparty_lines.append(ligne)

    # Si aucun mouvement de trésorerie détecté (ne devrait pas arriver si bien filtré avant)
    if abs(cash_movement) < 0.001:
        return 'UNKNOWN', 'Aucun mouvement de trésorerie détecté', 0.0

    # Cas 1: Pas de contrepartie claire (ex: virement interne entre comptes de trésorerie)
    if not counterparty_lines:
        # Vérifier si toutes les lignes concernent des comptes de trésorerie
        all_cash = all(l.compte_id in cash_account_ids for l in ecriture.lignes)
        if all_cash and len(ecriture.lignes) > 1:
             # C'est probablement un virement interne, on l'ignore dans les flux externes
             return 'TRANSFER', 'Virement interne', cash_movement
        else:
             # Mouvement de trésorerie isolé ou erreur dans l'écriture
             return 'UNKNOWN', 'Mouvement de trésorerie sans contrepartie claire', cash_movement

    # Cas 2: Classification basée sur la première contrepartie trouvée (simplification)
    # Une logique plus avancée pourrait analyser toutes les contreparties.
    counterparty_compte = counterparty_lines[0].compte
    if not counterparty_compte: # Sécurité si la relation n'est pas chargée
        return 'UNKNOWN', 'Compte de contrepartie non trouvé', cash_movement

    cp_num = counterparty_compte.numero
    cp_class = counterparty_compte.type

    # --- Règles de Classification (à adapter/affiner) ---

    # Exploitation (Operating)
    if cp_class in [ClasseCompte.CLASSE_6, ClasseCompte.CLASSE_7]:
        nature = "Charge" if cp_class == ClasseCompte.CLASSE_6 else "Produit"
        return 'OPERATING', f"Flux lié {nature} ({cp_num})", cash_movement
    if cp_class == ClasseCompte.CLASSE_4:
        if cp_num.startswith('40'): return 'OPERATING', f"Paiement Fournisseur ({cp_num})", cash_movement
        if cp_num.startswith('41'): return 'OPERATING', f"Encaissement Client ({cp_num})", cash_movement
        if cp_num.startswith(('42', '43')): return 'OPERATING', f"Salaires/Charges Sociales ({cp_num})", cash_movement
        if cp_num.startswith('44'): return 'OPERATING', f"TVA/Impôts/Taxes ({cp_num})", cash_movement
        # Autres comptes de tiers souvent liés à l'exploitation
        return 'OPERATING', f"Autre flux Tiers ({cp_num})", cash_movement

    # Investissement (Investing)
    if cp_class == ClasseCompte.CLASSE_2:
        action = "Acquisition" if cash_movement < 0 else "Cession"
        return 'INVESTING', f"{action} Immobilisation ({cp_num})", cash_movement
    if cp_num.startswith('50'): # Valeurs Mobilières de Placement (souvent investissement CT)
        action = "Achat" if cash_movement < 0 else "Vente"
        return 'INVESTING', f"{action} VMP ({cp_num})", cash_movement

    # Financement (Financing)
    if cp_class == ClasseCompte.CLASSE_1:
        if cp_num.startswith('101'): return 'FINANCING', "Apport/Retrait Capital", cash_movement
        if cp_num.startswith('16'):
            action = "Remboursement" if cash_movement < 0 else "Nouvel"
            return 'FINANCING', f"{action} Emprunt ({cp_num})", cash_movement
        if cp_num.startswith(('455', '457')): return 'FINANCING', f"Compte Courant Associé/Dividendes ({cp_num})", cash_movement
        # Autres comptes de capitaux propres
        return 'FINANCING', f"Autre flux Capitaux ({cp_num})", cash_movement

    # Si aucune règle n'a correspondu
    return 'UNKNOWN', f"Flux non classifié (Contrepartie: {cp_num})", cash_movement


def generate_cash_flow(organisation_id: int, date_debut: date, date_fin: date):
    """
    Génère les données pour le Tableau des Flux de Trésorerie (méthode directe simplifiée).
    """
    session = db.session
    organisation = session.query(Organisation).get(organisation_id)
    if not organisation:
        raise ValueError(f"Organisation avec ID {organisation_id} non trouvée.")

    if not date_debut or not date_fin or date_debut > date_fin:
        raise ValueError("Les dates de début et de fin sont invalides ou manquantes.")

    # 1. Identifier les comptes de trésorerie (ex: 512 pour banques, 53 pour caisse)
    #    Ajuste ces préfixes selon ton plan comptable si nécessaire.
    cash_accounts = session.query(CompteComptable).filter(
        CompteComptable.organisation_id == organisation_id,
        CompteComptable.actif == True,
        or_(CompteComptable.numero.startswith('512'), CompteComptable.numero.startswith('53'))
    ).all()
    cash_account_ids = {c.id for c in cash_accounts}

    if not cash_account_ids:
        logger.warning(f"Aucun compte de trésorerie (préfixe 512 ou 53) trouvé pour l'organisation {organisation_id}.")
        # Retourner une structure vide ou avec des zéros
        return {
            'organisation_nom': organisation.designation,
            'date_debut': date_debut.strftime('%Y-%m-%d'),
            'date_fin': date_fin.strftime('%Y-%m-%d'),
            'initial_cash': 0.0, 'flows': {'OPERATING': [], 'INVESTING': [], 'FINANCING': [], 'UNKNOWN': [], 'TRANSFER': []},
            'totals': {'operating': 0.0, 'investing': 0.0, 'financing': 0.0, 'unknown': 0.0, 'net_variation': 0.0},
            'final_cash_calculated': 0.0, 'final_cash_direct_balance': 0.0, 'is_verified': True, 'verification_difference': 0.0
        }

    # 2. Calculer la trésorerie initiale (solde de tous les comptes de trésorerie la veille du début)
    initial_cash = 0.0
    date_veille_debut = date_debut - timedelta(days=1)
    for compte_id in cash_account_ids:
        initial_cash += _calculate_account_balance(compte_id, date_veille_debut, session)

    # 3. Récupérer les écritures impliquant un compte de trésorerie sur la période
    #    On charge les lignes et les comptes associés pour l'analyse
    ecritures_cash = session.query(EcritureComptable).options(
        joinedload(EcritureComptable.lignes).joinedload(LigneEcriture.compte)
    ).join(LigneEcriture, EcritureComptable.id == LigneEcriture.ecriture_id)\
    .filter(
        EcritureComptable.organisation_id == organisation_id,
        EcritureComptable.date_ecriture >= date_debut,
        EcritureComptable.date_ecriture <= date_fin,
        LigneEcriture.compte_id.in_(cash_account_ids)
    ).distinct().order_by(EcritureComptable.date_ecriture, EcritureComptable.id).all()

    # 4. Classifier chaque flux et agréger
    flows_details = defaultdict(list) # Dictionnaire pour stocker les détails par catégorie
    totals = defaultdict(float)      # Dictionnaire pour stocker les totaux par catégorie

    for ecriture in ecritures_cash:
        # Optionnel: Vérifier l'équilibre de l'écriture avant de la traiter
        # total_debit = sum(l.montant_debit or 0.0 for l in ecriture.lignes)
        # total_credit = sum(l.montant_credit or 0.0 for l in ecriture.lignes)
        # if abs(total_debit - total_credit) > 0.01:
        #     logger.warning(f"Écriture ID {ecriture.id} déséquilibrée, ignorée pour le flux de trésorerie.")
        #     continue

        category, description, amount = _classify_cash_flow(ecriture, cash_account_ids)

        # Ajouter le détail du flux
        flows_details[category].append({
            'date': ecriture.date_ecriture.strftime('%Y-%m-%d'),
            'libelle_ecriture': ecriture.libelle,
            'description_flux': description, # Description générée par la classification
            'amount': amount
        })

        # Mettre à jour les totaux (sauf pour les virements internes)
        if category != 'TRANSFER':
            totals[category] += amount

    # 5. Calculer la variation nette et la trésorerie finale (basée sur les flux)
    total_operating = totals['OPERATING']
    total_investing = totals['INVESTING']
    total_financing = totals['FINANCING']
    total_unknown = totals['UNKNOWN'] # Garder une trace des flux non classifiés

    net_variation = total_operating + total_investing + total_financing + total_unknown
    final_cash_calculated = initial_cash + net_variation

    # 6. Vérification : Calculer la trésorerie finale directement à partir des soldes des comptes
    final_cash_direct_balance = 0.0
    for compte_id in cash_account_ids:
        final_cash_direct_balance += _calculate_account_balance(compte_id, date_fin, session)

    # Comparer les deux calculs de trésorerie finale
    verification_diff = final_cash_calculated - final_cash_direct_balance
    is_verified = abs(verification_diff) < 0.01 # Tolérance pour les erreurs d'arrondi

    if not is_verified:
         logger.warning(f"Flux de trésorerie - Vérification échouée pour Org ID {organisation_id} "
                        f"({date_debut} à {date_fin}). "
                        f"Différence: {verification_diff:.2f} € "
                        f"(Calculé via flux: {final_cash_calculated:.2f}, "
                        f"Calculé via soldes: {final_cash_direct_balance:.2f})")

    # 7. Retourner la structure de données complète
    return {
        'organisation_nom': organisation.designation,
        'date_debut': date_debut.strftime('%Y-%m-%d'),
        'date_fin': date_fin.strftime('%Y-%m-%d'),
        'initial_cash': initial_cash,
        'flows': dict(flows_details), # Convertir defaultdict en dict normal pour le retour
        'totals': {
            'operating': total_operating,
            'investing': total_investing,
            'financing': total_financing,
            'unknown': total_unknown,
            'net_variation': net_variation
        },
        'final_cash_calculated': final_cash_calculated, # Trésorerie finale = Initiale + Variation
        'final_cash_direct_balance': final_cash_direct_balance, # Trésorerie finale via solde des comptes
        'is_verified': is_verified, # Indique si les deux méthodes de calcul concordent
        'verification_difference': verification_diff
    }

# --- Fin de reports/report_generators.py ---
