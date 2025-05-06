# c:\wamp\www\mon_compta_app\controllers\rag_retriever.py
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from mistralai import Mistral # Nécessaire pour get_embeddings_for_rag si on le déplace ici aussi

# Importations depuis vos autres modules RAG
from .rag_controller import get_rag_filepath, MISTRAL_EMBEDDING_MODEL, get_mistral_embeddings

# Constantes pour la récupération RAG (peuvent être ajustées)
NUM_TOP_CHUNKS = 3
SIMILARITY_THRESHOLD = 0.7 # Seuil de similarité

def get_context_from_rag(question: str, projet_id: int, api_key: str, logger) -> str:
    """
    Récupère le contexte pertinent des documents d'un projet pour une question donnée.

    Args:
        question: La question de l'utilisateur.
        projet_id: L'ID du projet pour lequel chercher le contexte.
        api_key: La clé API Mistral.
        logger: L'instance du logger pour enregistrer les messages.

    Returns:
        Une chaîne de caractères formatée contenant le contexte pertinent,
        ou une chaîne vide si aucun contexte pertinent n'est trouvé ou en cas d'erreur.
    """
    retrieved_context_for_prompt = ""
    logger.info(f"RAG: Début de la recherche de contexte pour projet_id: {projet_id} et question: '{question[:50]}...'")

    try:
        rag_file_path = get_rag_filepath(projet_id)
        project_texts = []
        project_embeddings = np.array([])

        if os.path.exists(rag_file_path):
            logger.info(f"RAG: Chargement du fichier RAG pour récupération : {rag_file_path}")
            with np.load(rag_file_path, allow_pickle=True) as data:
                if 'texts' in data and 'embeddings' in data:
                    project_texts = list(data['texts'])
                    project_embeddings = data['embeddings']
                    if project_embeddings.ndim == 1 and len(project_texts) == 1:
                        project_embeddings = project_embeddings.reshape(1, -1)
                    logger.info(f"RAG: {len(project_texts)} textes et {project_embeddings.shape[0] if project_embeddings.ndim > 0 and project_embeddings.size > 0 else 0} embeddings chargés.")
                else:
                    logger.warning(f"RAG: Fichier {rag_file_path} mal formaté pour la récupération.")
        else:
            logger.info(f"RAG: Aucun fichier RAG trouvé pour le projet {projet_id} à {rag_file_path}.")
            return "" # Pas de fichier, pas de contexte

        if not project_texts or project_embeddings.size == 0:
            logger.info("RAG: Aucun texte ou embedding chargé, pas de recherche de similarité.")
            return ""

        # Générer l'embedding pour la question de l'utilisateur
        # Utiliser la fonction get_mistral_embeddings importée de rag_controller
        question_embedding_list = get_mistral_embeddings([question], api_key) # Doit être une liste

        if not question_embedding_list or not question_embedding_list[0]:
            logger.warning("RAG: Impossible de générer l'embedding pour la question.")
            return ""
        
        question_embedding = np.array(question_embedding_list[0], dtype=np.float32).reshape(1, -1)
        logger.info("RAG: Embedding pour la question utilisateur généré.")

        # Vérifier la compatibilité des dimensions
        if project_embeddings.shape[1] != question_embedding.shape[1]:
            logger.error(f"RAG: Incompatibilité de dimension des embeddings. Projet: {project_embeddings.shape[1]}, Question: {question_embedding.shape[1]}")
            return ""

        # Calculer la similarité cosinus
        similarities = cosine_similarity(question_embedding, project_embeddings)
        similarity_scores = similarities[0] # On prend la première (et unique) ligne

        # Sélectionner les N morceaux de texte les plus similaires
        # argsort trie par ordre croissant, donc on prend les N derniers, puis on inverse
        top_n_indices = np.argsort(similarity_scores)[-NUM_TOP_CHUNKS:][::-1]
        
        relevant_chunks = []
        for index in top_n_indices:
            if similarity_scores[index] >= SIMILARITY_THRESHOLD:
                relevant_chunks.append(project_texts[index])
                logger.debug(f"RAG: Chunk '{project_texts[index][:50]}...' (score: {similarity_scores[index]:.2f}) ajouté.")
            else:
                logger.debug(f"RAG: Chunk à l'index {index} (score: {similarity_scores[index]:.2f}) écarté car < seuil {SIMILARITY_THRESHOLD}.")


        if relevant_chunks:
            logger.info(f"RAG: {len(relevant_chunks)} chunks pertinents trouvés.")
            context_header = "Contexte extrait de documents pertinents :\n"
            formatted_chunks = "\n\n---\n\n".join(relevant_chunks) # Séparer les chunks
            retrieved_context_for_prompt = f"{context_header}\n{formatted_chunks}\n\n---\nQuestion originale : "
            logger.debug(f"RAG: Contexte préparé:\n{retrieved_context_for_prompt[:200]}...")
        else:
            logger.info("RAG: Aucun chunk suffisamment pertinent trouvé après filtrage par seuil.")

    except ValueError as ve: # Pour les erreurs de configuration ou de données attendues (ex: RAG_STORAGE_PATH manquant)
        logger.error(f"RAG: Erreur de valeur lors de la récupération du contexte: {ve}", exc_info=True)
    except Exception as e:
        logger.error(f"RAG: Erreur inattendue durant la récupération du contexte pour projet {projet_id}: {e}", exc_info=True)
        # En cas d'erreur, on retourne une chaîne vide pour ne pas bloquer le chatbot
    
    return retrieved_context_for_prompt
