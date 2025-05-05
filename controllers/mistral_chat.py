# c:\wamp\www\mon_compta_app\controllers\mistral_chat.py
from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   flash,
                   jsonify,
                   session,
                   request)
from forms.forms import ChatbotQuestionForm
from markdown_it import MarkdownIt # Importé
import logging
import os
from controllers.users_controller import login_required # Pour protéger la route si besoin

from mistralai import Mistral
# Note: L'import 'json' n'était pas utilisé et a été retiré.

logger = logging.getLogger(__name__) # Initialiser le logger
md = MarkdownIt() # Initialise le parseur Markdown une seule fois

# Création du Blueprint 'chatbot'
chatbot_bp = Blueprint('chatbot', __name__, template_folder='../templates/mistral')

@chatbot_bp.route('/chatbot_ask', methods=['POST']) # Assurez-vous que l'URL correspond à vos url_for
def chatbot_ask():
    """
    Reçoit la question de l'utilisateur via le formulaire WTForms ou AJAX,
    valide la saisie, récupère l'historique, appelle l'API Mistral,
    met à jour l'historique et retourne la réponse (JSON pour AJAX, template pour non-AJAX).
    """
    # --- Utilisation du formulaire WTForms pour la validation ---
    form = ChatbotQuestionForm() # Instancier le formulaire

    # --- Déterminer si c'est une requête AJAX ---
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    question = None # Initialiser la variable question

    # --- Gérer les données différemment pour AJAX (JSON) ---
    if is_ajax:
        data = request.get_json()
        question = data.get('question') if data else None
        # Validation simple pour AJAX (CSRF est géré par header X-CSRFToken)
        if not question:
             logger.warning("Requête AJAX reçue sans question valide.")
             return jsonify({"success": False, "error": "La question ne peut pas être vide."}), 400
    else:
        # Pour une soumission de formulaire classique (non-AJAX)
        if form.validate_on_submit(): # Gère la méthode POST et la validation
             question = form.question.data # Récupérer la question validée
        else:
            # Si la validation échoue pour une requête non-AJAX POST
            logger.warning(f"Échec de validation du formulaire chatbot (non-AJAX): {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Erreur : {error}", 'danger')
            # Rediriger si la validation échoue pour non-AJAX
            return redirect(url_for('users.accueil'))

    # --- La logique suivante s'exécute si la question est valide (AJAX ou non) ---
    if question:
        logger.info(f"Question reçue (via {'AJAX' if is_ajax else 'Form'}) : {question}")

        # 1. Récupérer la clé API de manière sécurisée
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            logger.error("Clé API Mistral (MISTRAL_API_KEY) non configurée.")
            flash("Erreur de configuration du serveur, l'assistant n'est pas disponible.", "danger")
            if is_ajax:
                return jsonify({"success": False, "error": "Erreur de configuration serveur."}), 500
            else:
                return redirect(url_for('users.accueil'))

        # --- Récupérer/Initialiser l'historique de la conversation depuis la session ---
        chat_history = session.get('mistral_chat_history', [])
        logger.debug(f"DEBUG: Historique récupéré de la session: {chat_history}")
        # --------------------------------------------------------------------------

        raw_answer = None # Initialiser la variable réponse BRUTE (Markdown)
        html_answer = None # Initialiser la variable réponse HTML

        try:
            # --- Début de l'appel à Mistral  ---
            model_chat = "mistral-small-latest"
            client = Mistral(api_key=api_key)

            # --- Définir le prompt système ---
            system_prompt = """
            Tu es Loova, un assistant virtuel spécialisé en comptabilité et gestion de projet pour les petites entreprises et freelances.
            Réponds de manière claire, concise et professionnelle.
            Si la question sort complètement du cadre de la comptabilité ou de la gestion de projet, indique poliment que ce n'est pas ton domaine d'expertise.
            """

            # --- Construire la liste des messages incluant l'historique ---
            messages = [{"role": "system", "content": system_prompt}]
            for msg in chat_history:
                 if isinstance(msg, dict) and "role" in msg and "content" in msg:
                      messages.append({"role": msg["role"], "content": msg["content"]})
                 else:
                      logger.warning(f"Élément invalide trouvé dans l'historique du chat : {msg}")
            messages.append({"role": "user", "content": question})

            logger.debug(f"Messages envoyés à l'API: {messages}")
            # -------------------------------------------------------------

            chat_response = client.chat.complete(
                model=model_chat,
                messages=messages
            )
            raw_answer = chat_response.choices[0].message.content # Réponse BRUTE (Markdown)
            logger.info(f"Réponse de Mistral AI reçue.")
            # --- Fin de l'appel à Mistral ---

            # --- Conversion Markdown -> HTML ---
            html_answer = md.render(raw_answer)
            # -----------------------------------

            # --- Mettre à jour l'historique ET retourner la réponse pour AJAX ICI ---
            # Mettre à jour l'historique avec la question et la réponse BRUTE
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": raw_answer}) # Stocker le brut
            session['mistral_chat_history'] = chat_history
            logger.debug(f"DEBUG: Historique mis à jour et sauvegardé.")

            # Si c'est une requête AJAX, retourner la réponse HTML JSON maintenant
            if is_ajax:
                return jsonify({"success": True, "answer": html_answer}) # Renvoie le HTML
            # --- FIN MODIFICATION ---

        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Mistral AI (ou traitement) : {e}", exc_info=True)
            flash("Désolé, une erreur est survenue lors de la communication avec l'assistant.", "danger")
            # En cas d'erreur API, on ne modifie pas l'historique
            error_message = "Erreur lors de la génération de la réponse."
            html_answer = f'<p class="text-danger">{error_message}</p>' # Renvoyer un message d'erreur HTML
            if is_ajax:
                 # Renvoyer l'erreur HTML dans la clé 'answer' pour l'afficher côté client
                 return jsonify({"success": False, "answer": html_answer}), 500
            # Pour non-AJAX, on continue pour rendre le template avec le flash message

        # --- Rendu du template (uniquement pour les requêtes non-AJAX) ---
        # Ce bloc est moins pertinent si tu utilises AJAX pour toutes les interactions,
        # mais il est conservé pour la complétude.
        if not is_ajax:
            logger.debug(f"Rendu non-AJAX demandé (ou fallback après erreur API).")
            new_chatbot_form = ChatbotQuestionForm()

            # --- Traiter l'historique pour l'affichage non-AJAX ---
            processed_history = []
            for message in chat_history:
                processed_message = message.copy()
                if processed_message.get('role') == 'assistant':
                    # Convertir le contenu brut stocké en HTML pour l'affichage
                    processed_message['content'] = md.render(processed_message.get('content', ''))
                processed_history.append(processed_message)
            # -------------------------------------------------------

            # Passer l'historique traité et le formulaire
            return render_template('chat.html',
                                   chat_history=processed_history, # Utiliser l'historique traité
                                   chatbot_form=new_chatbot_form)

        # Ce code ne devrait normalement pas être atteint pour une requête AJAX réussie
        logger.error("Atteinte inattendue de la fin de la fonction pour une requête AJAX.")
        return jsonify({"success": False, "error": "Erreur serveur inattendue."}), 500

    else:
         # Ce cas ne devrait pas être atteint si la validation initiale fonctionne correctement
         logger.error("La variable 'question' est vide après la validation, ce qui ne devrait pas arriver.")
         flash("Une erreur inattendue est survenue lors du traitement de votre question.", "danger")
         return redirect(url_for('users.accueil'))


# --- Route pour effacer l'historique (optionnel) ---
@chatbot_bp.route('/clear_chat', methods=['POST'])
@login_required # Assurez-vous que seul un utilisateur connecté peut effacer
def clear_chat():
    """Efface l'historique du chat dans la session."""
    # Vérifier si c'est une requête AJAX (bonne pratique)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not is_ajax:
        # Si ce n'est pas AJAX, on peut choisir de rediriger ou de renvoyer une erreur
        flash("Action non autorisée.", "warning")
        return redirect(url_for('users.accueil')) # Ou retourner une erreur 405 Method Not Allowed

    try:
        # Utilise la même clé spécifique
        if 'mistral_chat_history' in session:
            session.pop('mistral_chat_history')
            logger.info("Historique du chat effacé de la session via AJAX.")
            # Retourner une réponse JSON de succès
            return jsonify(success=True)
        else:
            logger.info("Tentative d'effacement AJAX de l'historique du chat, mais aucun historique trouvé.")
            # Même s'il n'y avait rien, l'opération est un succès du point de vue de l'appelant
            return jsonify(success=True)
    except Exception as e:
        logger.error(f"Erreur lors de l'effacement de l'historique du chat via AJAX: {e}", exc_info=True)
        # Retourner une réponse JSON d'erreur
        return jsonify(success=False, error="Une erreur interne est survenue lors de l'effacement."), 500

