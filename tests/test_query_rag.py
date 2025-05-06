import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from mistralai import Mistral # Assurez-vous que c'est bien Mistral et non MistralClient si vous utilisez une version plus ancienne

# --- Configuration ---
# Adaptez ces valeurs
MISTRAL_API_KEY='wsIBgLThyxVzJTWhqogqNskLbM6EQmhB' # Remplacez par votre clé API
PROJET_ID_A_INTERROGER = 6 # Remplacez par l'ID du projet dont vous voulez interroger le RAG
QUESTION_UTILISATEUR = "peut tu résumer le contexte du projet ?" # Votre question

# Constantes (similaires à celles de rag_retriever.py)
MISTRAL_EMBEDDING_MODEL = "mistral-embed"
NUM_TOP_CHUNKS_A_AFFICHER = 3 # Combien de chunks les plus similaires afficher
SIMILARITY_THRESHOLD_POUR_AFFICHAGE = 0.5 # Seuil pour considérer un chunk comme pertinent (ajustez au besoin)

# --- Fonctions (simplifiées/reprises de votre code) ---

def get_mistral_embeddings_for_query(texts, api_key):
    """Obtient les embeddings pour une liste de textes via l'API Mistral."""
    if not texts:
        return []
    try:
        client = Mistral(api_key=api_key) # ou MistralClient(api_key=api_key)
        embeddings_batch_response = client.embeddings.create(
            model=MISTRAL_EMBEDDING_MODEL,
            inputs=texts
        )
        return [data.embedding for data in embeddings_batch_response.data]
    except Exception as e:
        print(f"Erreur lors de l'appel à l'API d'embedding Mistral: {e}")
        return []

def get_rag_filepath_for_query(projet_id, base_rag_storage_path):
    """Construit le chemin complet du fichier .npz."""
    if not base_rag_storage_path:
        raise ValueError("Chemin de stockage RAG non fourni.")
    return os.path.join(base_rag_storage_path, f"rag_projet_{projet_id}.npz")

def query_rag_file(question: str, projet_id: int, api_key: str, rag_storage_path: str):
    """
    Interroge un fichier RAG .npz spécifique.
    """
    print(f"Interrogation du RAG pour projet_id: {projet_id} avec la question: '{question}'")

    try:
        rag_file_path = get_rag_filepath_for_query(projet_id, rag_storage_path)
        project_texts = []
        project_embeddings = np.array([])

        if os.path.exists(rag_file_path):
            print(f"Chargement du fichier RAG : {rag_file_path}")
            with np.load(rag_file_path, allow_pickle=True) as data:
                if 'texts' in data and 'embeddings' in data:
                    project_texts = list(data['texts'])
                    project_embeddings = data['embeddings']
                    if project_embeddings.ndim == 1 and len(project_texts) == 1:
                        project_embeddings = project_embeddings.reshape(1, -1)
                    print(f"{len(project_texts)} textes et {project_embeddings.shape[0] if project_embeddings.ndim > 0 and project_embeddings.size > 0 else 0} embeddings chargés.")
                else:
                    print(f"Fichier {rag_file_path} mal formaté.")
                    return
        else:
            print(f"Aucun fichier RAG trouvé pour le projet {projet_id} à {rag_file_path}.")
            return

        if not project_texts or project_embeddings.size == 0:
            print("Aucun texte ou embedding chargé, pas de recherche.")
            return

        question_embedding_list = get_mistral_embeddings_for_query([question], api_key)

        if not question_embedding_list or not question_embedding_list[0]:
            print("Impossible de générer l'embedding pour la question.")
            return
        
        question_embedding = np.array(question_embedding_list[0], dtype=np.float32).reshape(1, -1)
        print("Embedding pour la question utilisateur généré.")

        if project_embeddings.shape[1] != question_embedding.shape[1]:
            print(f"Incompatibilité de dimension des embeddings. Projet: {project_embeddings.shape[1]}, Question: {question_embedding.shape[1]}")
            return

        similarities = cosine_similarity(question_embedding, project_embeddings)
        similarity_scores = similarities[0]

        top_n_indices = np.argsort(similarity_scores)[-NUM_TOP_CHUNKS_A_AFFICHER:][::-1]
        
        print(f"\n--- Chunks les plus pertinents (seuil > {SIMILARITY_THRESHOLD_POUR_AFFICHAGE}) ---")
        found_relevant_chunk = False
        for i, index in enumerate(top_n_indices):
            score = similarity_scores[index]
            if score >= SIMILARITY_THRESHOLD_POUR_AFFICHAGE:
                found_relevant_chunk = True
                print(f"\nChunk #{i+1} (Index original: {index}, Score: {score:.4f}):")
                print(project_texts[index])
            else:
                print(f"\nChunk #{i+1} (Index original: {index}, Score: {score:.4f}) - Sous le seuil.")
        
        if not found_relevant_chunk:
            print("Aucun chunk n'a dépassé le seuil de similarité.")

    except Exception as e:
        print(f"Erreur durant l'interrogation manuelle: {e}")

# --- Exécution ---
if __name__ == "__main__":
    # IMPORTANT: Définissez le chemin vers votre dossier RAG_STORAGE_PATH
    # Ce chemin est défini dans votre app.py:
    # RAG_STORAGE_PATH = os.path.join(app.root_path, 'data', 'rag_storage')
    # Vous devrez le reconstituer ici ou le passer en argument.
    # Exemple (adaptez 'chemin/vers/votre/application'):
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    # Supposons que votre script est dans un dossier à côté de 'mon_compta_app'
    # ou que vous ajustez ce chemin pour pointer vers la racine de votre projet Flask
    app_root_path = os.path.abspath(os.path.join(current_script_path, "..")) # Ajustez si besoin
    rag_storage_directory = os.path.join(app_root_path, 'data', 'rag_storage')
    
    # Vérifiez que le MISTRAL_API_KEY est bien défini
    if MISTRAL_API_KEY == "VOTRE_CLE_API_MISTRAL":
        print("ERREUR: Veuillez remplacer 'VOTRE_CLE_API_MISTRAL' par votre véritable clé API Mistral.")
    elif not os.path.exists(rag_storage_directory):
        print(f"ERREUR: Le dossier RAG_STORAGE_PATH '{rag_storage_directory}' n'existe pas. Vérifiez le chemin.")
    else:
        query_rag_file(QUESTION_UTILISATEUR, PROJET_ID_A_INTERROGER, MISTRAL_API_KEY, rag_storage_directory)

