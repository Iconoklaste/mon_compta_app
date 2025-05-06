# c:\wamp\www\mon_compta_app\controllers\rag_controller.py
import os
import logging
import numpy as np
from flask import Blueprint, request, jsonify, current_app, session, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import Projet, User

# --- Bibliothèques pour l'extraction de texte ---
import PyPDF2
import docx # python-docx
import re # Ajouté pour le nettoyage de texte

# --- Client Mistral ---
from mistralai import Mistral

# --- Configuration ---
# Nous récupérerons RAG_STORAGE_PATH de app.config
# MISTRAL_API_KEY sera récupérée des variables d'environnement

# Initialiser le logger pour ce contrôleur
logger = logging.getLogger(__name__)

# Création du Blueprint 'rag_bp'
rag_bp = Blueprint('rag', __name__, url_prefix='/rag') # Le préfixe /rag est optionnel mais peut être utile

# --- Constantes ---
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
MISTRAL_EMBEDDING_MODEL = "mistral-embed" # Modèle d'embedding de Mistral

# --- Fonctions Utilitaires (nous les définirons plus tard) ---

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_stream):
    """Extrait le texte d'un flux de fichier PDF."""
    text = ""
    try:
        reader = PyPDF2.PdfReader(file_stream)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text() or "" # Ajouter or "" pour gérer les cas où extract_text retourne None
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte PDF: {e}", exc_info=True)
        # Retourner une chaîne vide ou lever une exception spécifique si vous préférez
        return ""
    return text

def extract_text_from_docx(file_stream):
    """Extrait le texte d'un flux de fichier DOCX."""
    text = ""
    try:
        document = docx.Document(file_stream)
        for para in document.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte DOCX: {e}", exc_info=True)
        return ""
    return text

def extract_text_from_txt(file_stream):
    """Extrait le texte d'un flux de fichier TXT."""
    try:
        # Le stream est en bytes, il faut le décoder. UTF-8 est un bon défaut.
        return file_stream.read().decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte TXT: {e}", exc_info=True)
        return ""

def chunk_text(text, chunk_size=500, chunk_overlap=50, separators=None):
    """
    Découpe le texte en morceaux (chunks) avec un chevauchement,
    en essayant de respecter les séparateurs sémantiques.
    chunk_size: nombre approximatif de caractères par chunk.
    chunk_overlap: nombre de caractères de chevauchement entre les chunks.
    separators: liste de séparateurs à essayer, du plus spécifique au plus générique.
    """
    if not text or not isinstance(text, str):
        logger.warning("chunk_text a reçu un texte vide ou invalide.")
        return []

    if separators is None:
        # Priorité : double saut de ligne (paragraphe), saut de ligne, fin de phrase, espace.
        separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]

    final_chunks = []

    # Si le texte est plus petit que la taille du chunk, le retourner tel quel s'il n'est pas vide.
    if len(text) <= chunk_size:
        stripped_text = text.strip()
        if stripped_text:
            logger.debug(f"Texte plus petit que chunk_size, retourné tel quel: '{stripped_text[:50]}...'")
            return [stripped_text]
        logger.debug("Texte plus petit que chunk_size et vide après strip, retourné liste vide.")
        return []

    # Tenter de diviser par le premier séparateur pertinent trouvé
    current_separator = ""
    for sep in separators:
        if sep in text: # Le séparateur vide "" sera toujours trouvé si aucun autre ne l'est.
            current_separator = sep
            break
    
    logger.debug(f"Utilisation du séparateur: '{current_separator}' (repr: {repr(current_separator)})")

    if current_separator:
        # Diviser le texte en utilisant le séparateur trouvé.
        # Si le séparateur est vide, cela signifie qu'aucun des séparateurs listés n'a été trouvé,
        # ou que le texte est un seul bloc sans ces séparateurs.
        # Dans ce cas, on traite le texte comme un seul grand "split".
        splits = text.split(current_separator) if current_separator else [text]
    else: # Devrait être couvert par current_separator = "" si la liste des séparateurs se termine par ""
        splits = [text]


    # Reconstruire des "documents" intermédiaires en essayant de ne pas dépasser chunk_size,
    # puis appliquer le chevauchement sur ces documents.
    intermediate_documents = []
    current_doc_content = ""
    for i, split_part in enumerate(splits):
        # Reconstituer la partie avec son séparateur (sauf pour la dernière partie si le séparateur n'est pas vide)
        # ou si le séparateur est vide (ce qui signifie qu'on traite le texte comme un seul bloc).
        part_to_add = split_part
        if current_separator and i < len(splits) - 1 : # Ne pas ajouter le séparateur après la dernière partie
            part_to_add += current_separator

        if len(current_doc_content) + len(part_to_add) > chunk_size and current_doc_content:
            # Si l'ajout de la nouvelle partie dépasse la taille et que current_doc n'est pas vide,
            # on sauvegarde current_doc et on commence un nouveau.
            if current_doc_content.strip():
                intermediate_documents.append(current_doc_content.strip())
            current_doc_content = part_to_add
        else:
            # Sinon, on continue d'ajouter à current_doc
            current_doc_content += part_to_add

    # Ajouter le dernier document en cours s'il n'est pas vide
    if current_doc_content.strip():
        intermediate_documents.append(current_doc_content.strip())
    
    if not intermediate_documents and text.strip(): # Cas où le texte est un seul bloc plus grand que chunk_size
        intermediate_documents = [text.strip()]


    logger.debug(f"{len(intermediate_documents)} documents intermédiaires créés avant fenêtrage.")

    # Appliquer la logique de fenêtrage glissante (avec chevauchement) sur chaque document intermédiaire
    for doc_item in intermediate_documents:
        if not doc_item.strip(): # Ignorer les documents vides
            continue

        if len(doc_item) <= chunk_size:
            final_chunks.append(doc_item) # Si le doc est déjà assez petit, on le prend tel quel
            logger.debug(f"  Document intermédiaire ajouté directement (taille {len(doc_item)}): '{doc_item[:50]}...'")
            continue
        
        # Appliquer la fenêtre glissante
        start = 0
        doc_len = len(doc_item)
        while start < doc_len:
            end = start + chunk_size
            chunk = doc_item[start:end].strip() # .strip() ici pour enlever les espaces en début/fin de chunk
            
            if chunk: # S'assurer que le chunk n'est pas vide après strip
                final_chunks.append(chunk)
                logger.debug(f"    Chunk fenêtré ajouté (de {start} à {end}, taille {len(chunk)}): '{chunk[:50]}...'")
            
            next_start = start + chunk_size - chunk_overlap
            
            if next_start <= start or end >= doc_len:
                # Si le prochain démarrage est avant ou égal au démarrage actuel (chevauchement trop grand ou mal calculé)
                # ou si on a atteint la fin du document, on avance simplement pour éviter des boucles infinies.
                start += chunk_size 
            else:
                start = next_start
                
    # Filtrer une dernière fois les chunks vides qui auraient pu se glisser
    # et s'assurer qu'il n'y a pas de doublons exacts (peut arriver avec certains overlaps/contenus)
    seen_chunks = set()
    unique_final_chunks = []
    for c in final_chunks:
        if c and c not in seen_chunks:
            unique_final_chunks.append(c)
            seen_chunks.add(c)
    
    logger.info(f"Chunking terminé. {len(unique_final_chunks)} chunks finaux générés.")
    return unique_final_chunks

def get_mistral_embeddings(texts, api_key):
    """
    Obtient les embeddings pour une liste de textes via l'API Mistral.
    Retourne une liste d'embeddings (liste de listes de floats).
    """
    if not texts:
        return []
    
    try:
        client = Mistral(api_key=api_key)
        embeddings_batch_response = client.embeddings.create(
            model=MISTRAL_EMBEDDING_MODEL,
            inputs=texts # L'API peut prendre une liste de textes directement
        )
        # La réponse contient une liste d'objets Embedding, chacun ayant un attribut 'embedding'
        return [data.embedding for data in embeddings_batch_response.data]
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API d'embedding Mistral: {e}", exc_info=True)
        # En cas d'erreur avec l'API, retourner une liste vide pour que le processus d'indexation puisse échouer proprement.
        return []

def get_rag_filepath(projet_id):
    """Construit le chemin complet du fichier .npz pour un projet_id donné."""
    rag_storage_dir = current_app.config.get('RAG_STORAGE_PATH')
    if not rag_storage_dir:
        logger.error("RAG_STORAGE_PATH n'est pas configuré dans l'application Flask.")
        raise ValueError("Configuration RAG_STORAGE_PATH manquante.")
    return os.path.join(rag_storage_dir, f"rag_projet_{projet_id}.npz")

# --- Route d'Indexation ---
@rag_bp.route('/projets/<int:projet_id>/indexer_document', methods=['POST'])
@login_required
def indexer_document_route(projet_id):
    """
    Reçoit un document uploadé pour un projet spécifique, l'extrait,
    génère les embeddings et les sauvegarde dans le fichier .npz du projet.
    """
    projet = Projet.query.filter_by(id=projet_id, organisation_id=current_user.organisation_id).first()
    if not projet:
        logger.warning(f"Tentative d'indexation pour projet non autorisé ou inexistant {projet_id} par user {current_user.id}")
        return jsonify({"success": False, "error": "Projet non trouvé ou accès non autorisé."}), 403

    if 'document' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier fourni."}), 400

    file = request.files['document']
    if file.filename == '':
        return jsonify({"success": False, "error": "Aucun fichier sélectionné."}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Type de fichier non autorisé. Extensions acceptées : " + ", ".join(ALLOWED_EXTENSIONS)}), 400

    filename = secure_filename(file.filename)
    logger.info(f"Début de l'indexation du document '{filename}' pour le projet ID {projet_id}.")

    try:
        text_content = ""
        file_extension = filename.rsplit('.', 1)[1].lower()

        if file_extension == 'pdf':
            text_content = extract_text_from_pdf(file.stream)
        elif file_extension == 'docx':
            text_content = extract_text_from_docx(file.stream)
        elif file_extension == 'txt':
            text_content = extract_text_from_txt(file.stream)

        if not text_content or not text_content.strip():
            return jsonify({"success": False, "error": "Impossible d'extraire le contenu du document ou document vide."}), 400
        
        # Nettoyage simple du texte
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        logger.info(f"Texte extrait et nettoyé de '{filename}' (longueur: {len(text_content)} caractères).")


        text_chunks = chunk_text(text_content) # Utilise la fonction chunk_text mise à jour
        if not text_chunks:
            logger.warning(f"Le document '{filename}' n'a pas pu être découpé en morceaux ou était vide après nettoyage.")
            return jsonify({"success": False, "error": "Le document n'a pas pu être découpé en morceaux."}), 400
        logger.info(f"{len(text_chunks)} chunks créés pour '{filename}'.")

        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            logger.error("MISTRAL_API_KEY non trouvée.")
            return jsonify({"success": False, "error": "Erreur de configuration serveur (API Key manquante)."}), 500

        new_embeddings_list = get_mistral_embeddings(text_chunks, api_key)
        if not new_embeddings_list or len(new_embeddings_list) != len(text_chunks):
            logger.error(f"Erreur lors de la génération des embeddings pour '{filename}'. Attendu: {len(text_chunks)}, Reçu: {len(new_embeddings_list) if new_embeddings_list else 0}")
            return jsonify({"success": False, "error": "Erreur lors de la génération des embeddings."}), 500
        logger.info(f"{len(new_embeddings_list)} embeddings générés pour '{filename}'.")
        new_embeddings_np = np.array(new_embeddings_list, dtype=np.float32)

        rag_file_path = get_rag_filepath(projet_id)
        all_texts_list = []
        all_metadata_list = [] # Initialisation pour les métadonnées
        # Init avec bonne dim si possible, sinon sera géré par np.vstack ou affectation directe
        existing_embeddings_np = np.array([], dtype=np.float32).reshape(0, new_embeddings_np.shape[1] if new_embeddings_np.ndim > 1 and new_embeddings_np.size > 0 else 1024) # 1024 est la dim de mistral-embed

        # --- Stratégie d'écrasement de l'index pour ce projet ---
        if os.path.exists(rag_file_path):
            try:
                os.remove(rag_file_path)
                logger.info(f"Ancien fichier RAG {rag_file_path} supprimé avant nouvelle indexation (stratégie d'écrasement).")
            except OSError as e:
                logger.error(f"Impossible de supprimer l'ancien fichier RAG {rag_file_path}: {e}")
                return jsonify({"success": False, "error": "Erreur lors de la suppression de l'index existant."}), 500
        
        all_texts_list = text_chunks # Remplacer, ne pas étendre
        new_metadata_list = [{"source_filename": filename} for _ in text_chunks] # Métadonnées simples
        all_metadata_list = new_metadata_list # Remplacer
        all_embeddings_np_combined = new_embeddings_np # Remplacer

        # --- Fin de la stratégie d'écrasement ---

        # Commentaire de l'ancienne logique de fusion si vous voulez la réactiver :
        # if os.path.exists(rag_file_path):
        #     logger.info(f"Chargement du fichier RAG existant : {rag_file_path}")
        #     try:
        #         with np.load(rag_file_path, allow_pickle=True) as data:
        #             if 'texts' in data and 'embeddings' in data:
        #                 all_texts_list = list(data['texts'])
        #                 existing_embeddings_np = data['embeddings']
        #                 if 'metadata' in data:
        #                     all_metadata_list = list(data['metadata'])
        #                 else:
        #                     all_metadata_list = [{} for _ in all_texts_list]
        #                 if existing_embeddings_np.ndim == 1 and len(all_texts_list) == 1 :
        #                     existing_embeddings_np = existing_embeddings_np.reshape(1, -1)
        #                 logger.info(f"{len(all_texts_list)} textes, {len(all_metadata_list)} méta et {existing_embeddings_np.shape[0] if existing_embeddings_np.ndim > 0 and existing_embeddings_np.size > 0 else 0} embeddings chargés.")
        #             else:
        #                 logger.warning(f"Fichier {rag_file_path} mal formaté. Il sera écrasé.")
        #     except Exception as e:
        #         logger.error(f"Erreur chargement {rag_file_path}: {e}. Fichier sera écrasé.", exc_info=True)
        #         all_texts_list = []
        #         all_metadata_list = []


        # if not all_texts_list: # Si on n'écrase pas et qu'il n'y avait rien ou erreur
        #     all_texts_list.extend(text_chunks)
        #     new_metadata_list = [{"source_filename": filename} for _ in text_chunks]
        #     all_metadata_list.extend(new_metadata_list)
        #     all_embeddings_np_combined = new_embeddings_np
        # else: # Fusionner si on n'écrase pas
        #     all_texts_list.extend(text_chunks)
        #     new_metadata_list = [{"source_filename": filename} for _ in text_chunks]
        #     all_metadata_list.extend(new_metadata_list)
        #     if existing_embeddings_np.size == 0:
        #          all_embeddings_np_combined = new_embeddings_np
        #     elif existing_embeddings_np.shape[1] != new_embeddings_np.shape[1]:
        #         logger.error(f"Incompatibilité de dimension des embeddings. Existants: {existing_embeddings_np.shape[1]}, Nouveaux: {new_embeddings_np.shape[1]}")
        #         return jsonify({"success": False, "error": "Erreur interne: Incompatibilité de dimension des embeddings."}), 500
        #     else:
        #         all_embeddings_np_combined = np.vstack([existing_embeddings_np, new_embeddings_np])


        try:
            os.makedirs(os.path.dirname(rag_file_path), exist_ok=True)
            np.savez_compressed(rag_file_path,
                                texts=np.array(all_texts_list, dtype=object),
                                embeddings=all_embeddings_np_combined,
                                metadata=np.array(all_metadata_list, dtype=object)) # Sauvegarder les métadonnées
            logger.info(f"Données RAG sauvegardées dans {rag_file_path} ({len(all_texts_list)} textes, {len(all_metadata_list)} métadonnées).")
        except Exception as e:
            logger.error(f"Erreur sauvegarde RAG {rag_file_path}: {e}", exc_info=True)
            return jsonify({"success": False, "error": "Erreur sauvegarde données d'indexation."}), 500

        return jsonify({
            "success": True,
            "message": f"Document '{filename}' indexé avec succès pour le projet {projet_id}.",
            "chunks_added": len(text_chunks), # C'est le nombre de nouveaux chunks de ce document
            "total_chunks_in_project": len(all_texts_list) # Total après écrasement/ajout
        }), 200

    except ValueError as ve: # Pour les erreurs de configuration comme RAG_STORAGE_PATH manquant
        logger.error(f"Erreur de valeur lors de l'indexation pour projet {projet_id}: {ve}", exc_info=True)
        return jsonify({"success": False, "error": str(ve)}), 400 # Renvoyer 400 pour une erreur de config/valeur
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'indexation de '{filename}' pour projet {projet_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erreur serveur lors de l'indexation."}), 500
