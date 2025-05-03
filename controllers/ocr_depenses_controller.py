# c:\wamp\www\mon_compta_app\controllers\ocr_depenses_controller.py
import os
import logging
import base64
import json
from flask import Blueprint, request, jsonify, current_app, session # Ajout de session
from mistralai import Mistral
from mistralai import models as mistral_models
from mistralai.models import OCRResponse
from IPython.display import Markdown, display
from controllers.users_controller import login_required # Pour protéger la route si besoin
# Importer User pour vérifier l'organisation si nécessaire
from models import User

# Création du Blueprint pour l'OCR
# Utilise un préfixe d'URL pertinent, par exemple '/ocr'
ocr_depenses_bp = Blueprint('ocr', __name__, url_prefix='/ocr')

# Récupérer le logger
logger = logging.getLogger(__name__)

@ocr_depenses_bp.route('/process-expense', methods=['POST'])
@login_required # Important: Assure que seul un utilisateur connecté peut utiliser l'OCR
def process_ocr_expense():
    """
    Reçoit un fichier de dépense (via POST), l'envoie à Mistral OCR
    et retourne les données extraites en JSON.
    """
    user_id = current_user.id
    user = User.query.get(user_id)
    if not user or not user.organisation_id:
        logger.warning(f"Tentative d'accès OCR sans utilisateur valide ou organisation (user_id: {user_id}).")
        return jsonify({"success": False, "error": "Authentification ou organisation invalide."}), 403

    # 1. Récupérer la clé API de manière sécurisée
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        logger.error("Clé API Mistral (MISTRAL_API_KEY) non configurée dans les variables d'environnement.")
        return jsonify({"success": False, "error": "Erreur de configuration serveur (clé API manquante)."}), 500
    
    model_ocr = "mistral-ocr-latest"
    model_chat = "mistral-small-latest"

    # 2. Vérifier si un fichier a été envoyé dans la requête
    if 'expense_file' not in request.files:
        logger.warning("Requête reçue sur /ocr/process-expense sans fichier 'expense_file'.")
        return jsonify({"success": False, "error": "Aucun fichier n'a été envoyé."}), 400

    file = request.files['expense_file']

    # 3. Vérifier si le fichier a un nom
    if file.filename == '':
        logger.warning("Requête reçue sur /ocr/process-expense avec un champ 'expense_file' vide.")
        return jsonify({"success": False, "error": "Aucun fichier sélectionné."}), 400

    # Optionnel : Vérification type de fichier
    # allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
    # if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
    #     logger.warning(f"Tentative d'upload OCR d'un fichier non autorisé: {file.filename}")
    #     return jsonify({"success": False, "error": "Type de fichier non autorisé (PNG, JPG, PDF uniquement)."}), 400

    try:
        # 4. Initialiser le client Mistral
        
        
        client = Mistral(api_key=api_key)

        # 5. Lire le contenu du fichier
        file.seek(0)
        file_content = file.read()

        # 5b. Encoder en base64 et déterminer le type MIME
        base64_encoded_content = base64.b64encode(file_content).decode('utf-8')
        mime_type = file.content_type # Récupérer le type MIME détecté par le navigateur/Flask
        if not mime_type:
            # Fallback si le type MIME n'est pas fourni (rare) - essayer de deviner depuis l'extension
            # Tu peux améliorer cette partie si nécessaire
            ext = file.filename.rsplit('.', 1)[-1].lower()
            mime_type = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'pdf': 'application/pdf'}.get(ext, 'application/octet-stream')
        data_url = f"data:{mime_type};base64,{base64_encoded_content}"

        # 6. Envoyer à l'API OCR de Mistral
        logger.info(f"Étape 1: Envoi du fichier '{file.filename}' à Mistral OCR ({model_ocr})...")
        ocr_response = client.ocr.process(
            model=model_ocr,
            document={
                "type": "image_url",
                "image_url": data_url
            }
        )
        logger.info(f"Étape 1: Réponse OCR reçue pour '{file.filename}'.")

        # 7. Extraire le contenu Markdown de la réponse OCR
        if ocr_response.pages and len(ocr_response.pages) > 0:
            # Concaténer le markdown de toutes les pages (au cas où il y en aurait plusieurs)
            ocr_markdown_content = "\n\n".join([page.markdown for page in ocr_response.pages])
            logger.debug(f"Contenu Markdown extrait par OCR:\n{ocr_markdown_content[:500]}...") # Log un aperçu

            # 8. Définir le prompt pour le modèle de chat
            #    Exemples de prompts (choisis ou combine):
            # user_question = "Ce document est-il une facture ? Réponds par OUI ou NON."
            # user_question = "Quel est le nom du fournisseur mentionné dans ce document ?"
            # user_question = "Quel est le montant total TTC indiqué ?"

            liste_comptes_str = request.form.get('liste_comptes', 'Aucun compte fourni par le client')
            logger.debug(f"Liste des comptes reçue du frontend : {liste_comptes_str[:100]}...") # Log un aperçu


            user_question = f"""Extrais les informations suivantes de ce document et retourne-les au format JSON avec exactement ces clés : date_facture (format YYYY-MM-DD si possible), nom_fournisseur, montant_total_ttc, compte_charge_suggere (choisis le nom EXACT du compte de charge le plus pertinent dans la liste suivante : [{liste_comptes_str}]. Le nom doit correspondre parfaitement à une entrée de la liste fournie, incluant le numéro de compte. Si aucun compte de la liste ne semble approprié, utilise la valeur null.). Si une autre information n'est pas trouvée, utilise la valeur null."""

            # 9. Construire les messages pour l'API Chat
            messages = [
                {"role": "user", "content": f"Voici le contenu du document extrait par OCR :\n\n```markdown\n{ocr_markdown_content}\n```\n\nMa question est : {user_question}"}
            ]

            # 10. Appeler l'API Chat
            logger.info(f"Étape 2: Envoi du contenu OCR et de la question au modèle de chat ({model_chat})...")
            chat_response = client.chat.complete(
                model=model_chat,
                messages=messages,
                # --- Activer le mode JSON si le prompt le demande ---
                response_format={"type": "json_object"}
            )
            chat_answer_json_str = chat_response.choices[0].message.content
            logger.info(f"Étape 2: Réponse JSON (string) reçue du modèle de chat : {chat_answer_json_str}")

            # 11. Essayer de parser la réponse JSON et retourner les données extraites
            try:
                extracted_data = json.loads(chat_answer_json_str)
                logger.info(f"Données extraites par le chat : {extracted_data}")
                # Retourne les données extraites par le chat
                return jsonify({"success": True, "extracted_data": extracted_data})
            except json.JSONDecodeError:
                logger.error(f"Le modèle de chat n'a pas retourné un JSON valide : {chat_answer_json_str}")
                # Retourne quand même le texte brut si le JSON échoue, avec un avertissement
                return jsonify({"success": True, "warning": "La réponse du chat n'était pas un JSON valide.", "chat_answer_raw": chat_answer_json_str})

        
        else:
             logger.warning(f"Aucun document ou contenu extrait trouvé dans la réponse Mistral pour '{file.filename}'.")
             return jsonify({"success": False, "error": "Impossible d'extraire les données du document."}), 400

    except mistral_models.HTTPValidationError as e:
        # Erreur spécifique de validation (ex: mauvais format de requête)
        logger.error(f"Erreur de validation API Mistral lors du traitement de '{file.filename}': Status={e.status_code}, Message={e.message}, Body={e.body}", exc_info=True)
        # On peut renvoyer un message plus précis si disponible dans e.body ou e.message
        return jsonify({"success": False, "error": f"Erreur de validation lors du contact avec le service OCR: {e.message}"}), 422 # Utiliser 422 ou 400
    except mistral_models.SDKError as e:
        # Erreur générale de l'API Mistral (authentification, serveur, etc.)
        logger.error(f"Erreur API Mistral (SDKError) lors du traitement de '{file.filename}': Status={e.status_code}, Message={e.message}", exc_info=True)
        return jsonify({"success": False, "error": f"Erreur lors du contact avec le service OCR: {e.message}"}), e.status_code if e.status_code else 502
    except Exception as e:
        logger.error(f"Erreur inattendue lors du traitement OCR pour '{file.filename}': {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erreur interne du serveur lors du traitement du fichier."}), 500

