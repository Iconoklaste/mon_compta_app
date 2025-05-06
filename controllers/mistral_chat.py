# c:\wamp\www\mon_compta_app\controllers\mistral_chat.py
import json
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

import time
import logging
import os
from controllers.users_controller import login_required # Pour protéger la route si besoin

from mistralai import Mistral
from mistralai import models as mistral_models
from .mistral_tools_config import TOOLS_LIST, AVAILABLE_FUNCTIONS
from .rag_retriever import get_context_from_rag # Nouvelle importation pour la logique RAG


logger = logging.getLogger(__name__) # Initialiser le logger
md = MarkdownIt().enable('table')

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
        if not data:
            logger.warning("Requête AJAX reçue sans données JSON.")
            return jsonify({"success": False, "error": "Données manquantes."}), 400

        question = data.get('question')
        projet_id_from_page_str = data.get('projet_id_from_page')
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

        # --- Mettre à jour le current_projet_id en session si fourni par AJAX ---
        if is_ajax and projet_id_from_page_str:
            try:
                projet_id_from_page_int = int(projet_id_from_page_str)
                if session.get('current_projet_id') != projet_id_from_page_int:
                    session['current_projet_id'] = projet_id_from_page_int
                    logger.info(f"ID de projet mis à jour en session via AJAX : {projet_id_from_page_int}")
            except ValueError:
                logger.warning(f"Impossible de convertir projet_id_from_page '{projet_id_from_page_str}' en entier.")
        # --------------------------------------------------------------------

        raw_answer = None # Initialiser la variable réponse BRUTE (Markdown)
        html_answer = None # Initialiser la variable réponse HTML
        redirect_url = None # Initialiser la variable pour l'URL de redirection

        # --- Logique RAG (maintenant externalisée) ---
        current_projet_id_for_rag = session.get('current_projet_id')
        retrieved_context_for_prompt = "" # Initialiser le contexte RAG
        if current_projet_id_for_rag:
            # Appel à la fonction externalisée
            retrieved_context_for_prompt = get_context_from_rag(question, current_projet_id_for_rag, api_key, logger)
        else:
             logger.info("Aucun projet_id courant en session, pas de recherche RAG spécifique au projet.")
         # --- Fin de la Logique RAG ---

        try:
            # --- Début de l'appel à Mistral  ---
            model_chat = "mistral-small-latest"
            client = Mistral(api_key=api_key)

            # --- Définir le prompt système ---
            system_prompt = """
            Tu es Loova, l’assistant virtuel expert en comptabilité et gestion de projet, dédié aux petites entreprises et freelances.  

            **Ton rôle**  
            - Traduire les demandes métier (“créer une facture”, “enregistrer une dépense”, “suivre l’avancement d’un projet”) en actions concrètes et réponses exploitables.  
            - Agir comme un véritable expert‑comptable et chef de projet, sans jargon inutile pour l’utilisateur non‑comptable.  

            **Ton style**  
            - Clair, direct et professionnel : pas de formule de politesse systématique, va à l’essentiel.  
            - Adapté au contexte : si la conversation est déjà lancée, poursuis sans réexposer ton rôle.  
            - Pédagogue : quand nécessaire, explique brièvement les principes (ex. principe de la partie double).  

            **Quand utiliser les outils (function calling)**  
            - Dès qu’une réponse nécessite une donnée dynamique (solde, liste de projets, statut de facture) ou une action (créer/mettre à jour un enregistrement), appelle l’outil approprié.  
            - Ne simule pas la logique : renvoie toujours la requête d’“outil” avec les paramètres exacts.  

            **Gestion des erreurs et limites**  
            - Si l’utilisateur sort du périmètre (hors compta/projet), réponds :  
            “Désolé, je ne suis pas spécialisé sur ce sujet.”  
            - En cas d’incertitude, pose une question de clarification ciblée (pas de questions ouvertes).  

            **UX et concision**  
            - Propose systématiquement, en fin de réponse, l’action suivante la plus pertinente (ex. bouton “Créer la facture”, “Voir le bilan”).  
            - Utilise des mini‑tableaux ou listes à puces pour synthétiser quand c’est utile.  

            **Exemples de formulation**  
            - Utile : “Solde exercice 2024 : 12 350 €. Voulez‑vous générer le bilan ?”  
            - À éviter : “Bonjour, je peux vous aider ? Souhaitez‑vous…, etc.”  
            """

            # --- Construire la liste des messages incluant l'historique ---
            messages = [{"role": "system", "content": system_prompt}]
            for msg in chat_history:
                 # Assurer que tous les éléments nécessaires sont présents
                 if isinstance(msg, dict) and "role" in msg:
                     # Copier le message pour éviter de modifier l'original en session
                     message_to_add = msg.copy()
                     # S'assurer que 'content' est présent ou None pour les messages assistant/user/system
                     if message_to_add["role"] in ["user", "assistant", "system"] and "content" not in message_to_add:
                         message_to_add["content"] = None # Ou une chaîne vide selon l'API
                     # S'assurer que les messages 'tool' ont bien 'content' et 'tool_call_id'
                     if message_to_add["role"] == "tool":
                         if "content" not in message_to_add: message_to_add["content"] = ""
                         if "tool_call_id" not in message_to_add:
                             logger.warning(f"Message 'tool' sans 'tool_call_id' ignoré: {message_to_add}")
                             continue # Ignorer ce message invalide
                     # S'assurer que les messages 'assistant' avec 'tool_calls' ont bien 'tool_calls'
                     if message_to_add["role"] == "assistant" and message_to_add.get("content") is None and "tool_calls" not in message_to_add:
                          logger.warning(f"Message 'assistant' sans 'content' ni 'tool_calls' ignoré: {message_to_add}")
                          continue # Ignorer ce message invalide

                     messages.append(message_to_add)
                 else:
                      logger.warning(f"Élément invalide trouvé dans l'historique du chat : {msg}")
            final_question_for_mistral = f"{retrieved_context_for_prompt}{question}"
            # Correction ici: utiliser final_question_for_mistral
            messages.append({"role": "user", "content": final_question_for_mistral})

            # --- Logique de relance avec temporisation exponentielle ---
            max_retries = 5
            base_delay = 1  # secondes
            response = None # Initialiser la réponse

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Tentative {attempt + 1}/{max_retries} d'appel à l'API Mistral Chat.")
                    response = client.chat.complete(
                        model=model_chat,
                        messages=messages,
                        tools=TOOLS_LIST,
                        tool_choice="auto"
                    )
                    break # Sortir de la boucle si succès
                except mistral_models.SDKError as e: # Utiliser mistral_models.SDKError
                    if e.status_code == 429:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Erreur 429 (Rate Limit Exceeded). Nouvelle tentative dans {delay} secondes...")
                            time.sleep(delay)
                        else:
                            logger.error(f"Erreur 429 après {max_retries} tentatives. Abandon.")
                            raise # Relancer l'exception si toutes les tentatives échouent
                    else:
                        raise # Relancer les autres erreurs SDK
            
            if response is None: # Si toutes les tentatives ont échoué sans lever d'exception (ne devrait pas arriver avec le raise)
                logger.error("Impossible d'obtenir une réponse de l'API Mistral après plusieurs tentatives.")
                # Gérer l'erreur comme vous le faisiez avant
                flash("Désolé, une erreur est survenue lors de la communication avec l'assistant (limite de requêtes atteinte).", "danger")
                error_message = "Erreur lors de la génération de la réponse (limite de requêtes)."
                html_answer = f'<p class="text-danger">{error_message}</p>'
                if is_ajax:
                    return jsonify({"success": False, "answer": html_answer, "redirect_url": None}), 500
                # Pour non-AJAX, on continue pour rendre le template avec le flash message
                # ... (vous devrez peut-être ajuster le flux d'erreur ici) ...
                # Pour l'instant, on va simplement relancer l'erreur si response est None après la boucle
                # ce qui sera attrapé par le bloc except Exception plus bas.
                # Cela simplifie la gestion d'erreur ici.
                # Cependant, il est préférable de gérer explicitement ce cas.
                # Pour cet exemple, on va supposer que si response est None, c'est une erreur fatale.
                # La logique ci-dessus avec `raise` dans la boucle `except` devrait déjà couvrir cela.
                # Donc, si on arrive ici avec response=None, c'est une situation anormale.
                # On va lever une exception pour être sûr.
                raise Exception("Échec de l'appel API Mistral après toutes les tentatives.")

            logger.debug(f"Messages envoyés à l'API: {messages}")
            # -------------------------------------------------------------

            response_message = response.choices[0].message
            logger.info("Première réponse de Mistral AI reçue.")
            logger.debug(f"Contenu brut de la réponse: {response_message}")

            # --- Ajouter la question utilisateur à l'historique ---
            # On le fait ici pour être sûr qu'elle est ajoutée avant toute réponse ou appel d'outil
            chat_history.append({"role": "user", "content": question})

            # --- Ajouter la réponse de l'assistant (même si elle contient tool_calls) à l'historique ---
            # Convertir l'objet Pydantic en dictionnaire pour la session JSON
            response_message_dict = response_message.model_dump(exclude_unset=True)
            chat_history.append(response_message_dict)

            # --- Vérifier si un appel de fonction est demandé ---
            if response_message.tool_calls:
                logger.info("Mistral demande un appel de fonction.")
                # --- Exécuter les fonctions demandées ---
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
                    function_args_str = tool_call.function.arguments

                    if function_to_call:
                        try:
                            logger.info(f"Appel de la fonction locale: {function_name} avec args: {function_args_str}")
                            # Décoder les arguments JSON (même si vide "{}")
                            function_args = json.loads(function_args_str)
                            # Appeler la fonction avec les arguments décompressés
                            function_response = function_to_call(**function_args)
                            logger.info(f"Résultat de la fonction '{function_name}': {function_response}")

                            # --- Analyser la réponse de la fonction ---
                            tool_result_data = json.loads(function_response)
                            is_multiple_matches = isinstance(tool_result_data, dict) and tool_result_data.get("status") == "multiple_matches"
                            is_multiple_matches_redirect = isinstance(tool_result_data, dict) and tool_result_data.get("status") == "multiple_matches_for_redirect"
                            is_redirect_needed = isinstance(tool_result_data, dict) and tool_result_data.get("status") == "redirect_needed"
                            # --- Ajouter le résultat de l'outil à l'historique ---
                            chat_history.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": function_response, # Le résultat (déjà une chaîne JSON)
                                }
                            )

                            # --- Cas 1: Plusieurs correspondances pour voir les détails ---
                            if is_multiple_matches: # (vient de get_project_details_by_name)
                                logger.info("Plusieurs correspondances trouvées par la fonction. Préparation de la réponse directe.")
                                # Construire la réponse pour l'utilisateur
                                matches_list = tool_result_data.get("matches", [])
                                response_text = tool_result_data.get("message", "Plusieurs projets correspondent.")
                                if matches_list:
                                    response_text += "\n\nProjets trouvés :"
                                    # Construire une liste Markdown avec des liens
                                    for match in matches_list:
                                        try:
                                            # Générer l'URL vers la page de détail du projet
                                            project_url = url_for('projets.projet_detail', projet_id=match.get('id'), _external=False)
                                            response_text += f"\n- [{match.get('nom')}]({project_url})" # Format Markdown: [Texte du lien](URL)
                                        except Exception as url_exc:
                                            logger.error(f"Erreur lors de la génération de l'URL pour projet ID {match.get('id')}: {url_exc}")
                                            response_text += f"\n- {match.get('nom')} (ID: {match.get('id')}) - Erreur lien" # Fallback texte
                                # Définir raw_answer directement, on ne fera pas de 2e appel Mistral
                                raw_answer = response_text
                                # On sort de la boucle for tool_call car on a notre réponse
                                break # Important: Gère un seul tool_call pour l'instant si multiple_matches
                            
                            # --- Cas 2: Plusieurs correspondances pour afficher la page ---
                            elif is_multiple_matches_redirect: # (vient de get_project_id_for_display)
                                logger.info("Plusieurs correspondances trouvées pour affichage page. Préparation de la réponse directe.")
                                matches_list = tool_result_data.get("matches", [])
                                response_text = tool_result_data.get("message", "Plusieurs projets correspondent.")
                                if matches_list:
                                    response_text += "\n\nPages trouvées :"
                                    for match in matches_list:
                                        try:
                                            # Générer l'URL vers la page de détail du projet
                                            project_url = url_for('projets.projet_detail', projet_id=match.get('id'), _external=False)
                                            # TODO: Idéalement, ces liens devraient déclencher une action spécifique (JS?)
                                            # pour soit rediriger, soit envoyer une nouvelle requête au bot avec l'ID choisi.
                                            # Pour l'instant, on affiche juste le lien.
                                            response_text += f"\n- [{match.get('nom')}]({project_url})"
                                        except Exception as url_exc:
                                            logger.error(f"Erreur lors de la génération de l'URL pour projet ID {match.get('id')}: {url_exc}")
                                            response_text += f"\n- {match.get('nom')} (ID: {match.get('id')}) - Erreur lien"
                                raw_answer = response_text
                                break

                            # --- Cas 3: Une seule correspondance pour afficher la page ---
                            elif is_redirect_needed: # (vient de get_project_id_for_display)
                                logger.info("Une seule correspondance trouvée pour affichage page. Préparation de la redirection.")
                                project_id = tool_result_data.get('id')
                                project_nom = tool_result_data.get('nom', 'ce projet')
                                if project_id:
                                    try:
                                        redirect_url = url_for('projets.projet_detail', projet_id=project_id, _external=False)
                                        raw_answer = f"OK, je vous redirige vers la page du projet '{project_nom}'." # Message de confirmation
                                    except Exception as url_exc:
                                        logger.error(f"Erreur lors de la génération de l'URL pour projet ID {project_id}: {url_exc}")
                                        raw_answer = f"J'ai trouvé le projet '{project_nom}' (ID: {project_id}) mais je n'ai pas pu générer le lien."
                        except Exception as func_exc:
                            logger.error(f"Erreur lors de l'exécution de la fonction {function_name}: {func_exc}", exc_info=True)
                            # Ajouter un message d'erreur pour le rôle 'tool'
                            chat_history.append({
                                "tool_call_id": tool_call.id, "role": "tool", "name": function_name,
                                "content": json.dumps({"error": f"Erreur interne lors de l'appel à {function_name}"})
                            })
                    else:
                        logger.error(f"Fonction '{function_name}' demandée par Mistral mais non trouvée localement.")
                        chat_history.append({
                            "tool_call_id": tool_call.id, "role": "tool", "name": function_name,
                            "content": json.dumps({"error": f"La fonction {function_name} n'est pas disponible."})
                        })

                # --- Faire le deuxième appel SEULEMENT si on n'a pas déjà une réponse (cas multiple_matches) ---
                if raw_answer is None and redirect_url is None: # raw_answer est défini si multiple_matches OU multiple_matches_redirect
                    logger.info("Envoi des résultats des outils à Mistral pour la réponse finale.")
                    # Construire les messages pour le deuxième appel (inclut la question, la réponse avec tool_calls, et les résultats des tools)
                    messages_for_second_call = [{"role": "system", "content": system_prompt}]
                    for msg in chat_history: # Utiliser l'historique mis à jour
                         if isinstance(msg, dict) and "role" in msg:
                             message_to_add = msg.copy()
                             if message_to_add["role"] in ["user", "assistant", "system"] and "content" not in message_to_add:
                                 message_to_add["content"] = None
                             if message_to_add["role"] == "tool":
                                 if "content" not in message_to_add: message_to_add["content"] = ""
                                 if "tool_call_id" not in message_to_add: continue
                             if message_to_add["role"] == "assistant" and message_to_add.get("content") is None and "tool_calls" not in message_to_add:
                                  continue
                             messages_for_second_call.append(message_to_add)
                         else:
                              logger.warning(f"Élément invalide dans l'historique lors du 2e appel: {msg}")

                    logger.debug(f"Messages pour le deuxième appel: {messages_for_second_call}")

                    
                    # --- Logique de relance pour le deuxième appel ---
                    second_api_response = None
                    for attempt in range(max_retries): # Utiliser les mêmes paramètres de relance
                        try:
                            logger.debug(f"Tentative {attempt + 1}/{max_retries} pour le deuxième appel API Mistral Chat.")
                            second_api_response = client.chat.complete(
                                model=model_chat,
                                messages=messages_for_second_call
                            )
                            break # Succès
                        except mistral_models.SDKError as e:
                            if e.status_code == 429:
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt)
                                    logger.warning(f"Erreur 429 (2e appel). Nouvelle tentative dans {delay} secondes...")
                                    time.sleep(delay)
                                else:
                                    logger.error(f"Erreur 429 (2e appel) après {max_retries} tentatives. Abandon.")
                                    raise 
                            else:
                                raise
                    final_response_message = second_api_response.choices[0].message

                    raw_answer = final_response_message.content
                    logger.info("Réponse finale de Mistral reçue après appel de fonction.")

                    # Offrir le lien vers la page projet si on vient de get_project_details_by_name ---
                    # On récupère le dernier message 'tool' qui devrait contenir les détails
                    last_tool_message = next((msg for msg in reversed(chat_history) if msg.get("role") == "tool"), None)
                    if last_tool_message and last_tool_message.get("name") == "get_project_details_by_name":
                        try:
                            tool_data = json.loads(last_tool_message.get("content", "{}"))
                            project_id_from_details = tool_data.get("id")
                            if project_id_from_details and isinstance(tool_data, dict) and "error" not in tool_data: # Assurer que ce n'est pas un message d'erreur
                                project_url = url_for('projets.projet_detail', projet_id=project_id_from_details, _external=False)
                                raw_answer += f"\n\n[Voir la page complète du projet]({project_url})" # Ajouter le lien Markdown
                        except Exception as link_exc:
                            logger.error(f"Erreur lors de l'ajout du lien projet à la réponse: {link_exc}")


                    # --- Ajouter la réponse finale de l'assistant à l'historique ---
                    final_response_dict = final_response_message.model_dump(exclude_unset=True)
                    chat_history.append(final_response_dict)
                else:
                    # Cas multiple_matches: on a déjà raw_answer, on ajoute un message assistant "manuel" à l'historique
                    logger.info("Ajout de la réponse 'multiple_matches' à l'historique.")
                    chat_history.append({"role": "assistant", "content": raw_answer})


            else:
                # --- Pas d'appel de fonction, réponse directe ---
                raw_answer = response_message.content # Réponse BRUTE (Markdown)
                logger.info("Réponse directe de Mistral AI reçue (pas d'appel de fonction).")
                # L'historique a déjà été mis à jour avec la question et la réponse de l'assistant


            # --- Conversion Markdown -> HTML ---
            # S'assurer que raw_answer n'est pas None avant de le rendre
            html_answer = md.render(raw_answer) if raw_answer is not None else "<p>Une erreur s'est produite.</p>"
            if redirect_url:
                 html_answer = f'<p>{raw_answer}</p>' # Garder un message simple si redirection

            # -----------------------------------

            # --- Mettre à jour l'historique ET retourner la réponse pour AJAX ICI ---
            # Mettre à jour l'historique avec la question et la réponse BRUTE
            # Note: L'historique est maintenant mis à jour au fur et à mesure dans les blocs conditionnels
            # On s'assure juste de le sauvegarder à la fin.
            # chat_history.append({"role": "user", "content": question}) # Déjà fait plus haut
            # chat_history.append({"role": "assistant", "content": raw_answer}) # Déjà fait dans les blocs if/else
            session['mistral_chat_history'] = chat_history
            logger.debug(f"DEBUG: Historique mis à jour et sauvegardé.")

            # Si c'est une requête AJAX, retourner la réponse HTML JSON maintenant
            if is_ajax:
                response_data = {"success": True, "answer": html_answer}
                if redirect_url:
                    response_data["redirect_url"] = redirect_url
                    logger.info(f"Réponse AJAX avec redirection vers: {redirect_url}")
                else:
                    logger.info("Réponse AJAX sans redirection.")
                return jsonify(response_data)


        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Mistral AI (ou traitement) : {e}", exc_info=True)
            flash("Désolé, une erreur est survenue lors de la communication avec l'assistant.", "danger")
            # En cas d'erreur API, on ne modifie pas l'historique
            error_message = "Erreur lors de la génération de la réponse."
            html_answer = f'<p class="text-danger">{error_message}</p>' # Renvoyer un message d'erreur HTML
            if is_ajax:
                 # Renvoyer l'erreur HTML dans la clé 'answer' pour l'afficher côté client
                 return jsonify({"success": False, "answer": html_answer, "redirect_url": None}), 500
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
                    # Gérer le cas où content est None (si tool_calls était présent)
                    assistant_content = processed_message.get('content')
                    processed_message['content'] = md.render(assistant_content) if assistant_content else "[Appel d'outil en cours...]" # Ou masquer complètement
                    # On pourrait choisir de ne pas afficher les messages 'tool' ou les 'assistant' avec tool_calls
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

