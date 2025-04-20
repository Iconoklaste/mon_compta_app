/**
 * Système de gestion des notifications Flash pour l'application.
 * Gère l'affichage initial et la disparition automatique des messages.
 * Fournit une fonction pour ajouter dynamiquement de nouvelles notifications.
 */

(function() {
    'use strict';

    const FLASH_CONTAINER_ID = 'flash-container'; // ID du conteneur dans la sidebar
    const FLASH_MESSAGE_SELECTOR = '.flash-message'; // Sélecteur pour les messages existants
    const AUTO_DISMISS_DELAY = 3000; // Délai en millisecondes avant disparition

    /**
     * Gère le comportement d'un message flash individuel.
     * @param {HTMLElement} flashElement L'élément DOM du message flash.
     */
    function handleFlashMessage(flashElement) {
        const category = flashElement.dataset.category;

        // Comportement pour success et info : disparition automatique
        if (category === 'success' || category === 'info') {
            setTimeout(() => {
                // Utilise l'API Bootstrap pour fermer l'alerte (si Bootstrap 5 est chargé)
                const alertInstance = bootstrap.Alert.getOrCreateInstance(flashElement);
                if (alertInstance) {
                    alertInstance.close();
                } else {
                    // Fallback si Bootstrap JS n'est pas là ou échoue
                    flashElement.style.opacity = '0';
                    // Attend la fin de la transition CSS avant de supprimer
                    flashElement.addEventListener('transitionend', () => flashElement.remove());
                    // Sécurité si pas de transition CSS
                    setTimeout(() => flashElement.remove(), 600);
                }
            }, AUTO_DISMISS_DELAY);
        }

        // Pour warning et error, on ne fait rien, Bootstrap gère la fermeture via le bouton [x]
        // S'assurer que le bouton de fermeture fonctionne même si l'alerte est ajoutée dynamiquement
        const closeButton = flashElement.querySelector('[data-bs-dismiss="alert"]');
        if (closeButton && !bootstrap.Alert.getInstance(flashElement)) {
             // Initialise l'alerte Bootstrap si elle n'est pas déjà initialisée
             // (utile surtout pour les messages ajoutés dynamiquement)
             new bootstrap.Alert(flashElement);
        }
    }

        /**
     * Fonction pour afficher une nouvelle notification dynamiquement.
     * Peut être appelée depuis d'autres scripts.
     * @param {string} message Le contenu du message.
     * @param {string} category La catégorie ('success', 'info', 'warning', 'error').
     */
        window.showFlashMessage = function(message, category = 'info') {
            const container = document.getElementById(FLASH_CONTAINER_ID);
            if (!container) {
                console.error(`Conteneur flash #${FLASH_CONTAINER_ID} non trouvé.`);
                return;
            }
    
            // Adapte la catégorie pour les classes Bootstrap
            const alertClass = category === 'error' ? 'danger' : category;
    
            // Crée l'élément d'alerte HTML - SANS la classe 'show' pour l'instant
            const alertDiv = document.createElement('div');
            // NOTE : On retire 'show' de la liste initiale des classes
            alertDiv.className = `alert alert-${alertClass} alert-dismissible fade flash-message mb-2`; // mb-2 pour l'espace entre notifs
            alertDiv.setAttribute('role', 'alert');
            alertDiv.setAttribute('data-category', category);
    
            // Ajoute le message et le bouton de fermeture
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close btn-sm" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
    
            // --- Modification pour l'animation ---
            // Ajoute la nouvelle alerte au conteneur (appendChild fonctionne avec column-reverse pour ajouter en bas)
            container.appendChild(alertDiv);
    
            // Force le navigateur à calculer le layout (reflow) avant d'ajouter les classes d'animation/visibilité
            void alertDiv.offsetHeight;
    
            // Ajoute la classe 'show' (pour Bootstrap) et notre classe d'animation
            // dans le prochain cycle de rendu pour déclencher les transitions/animations CSS
            requestAnimationFrame(() => {
                // 'show' rend l'élément visible (requis par Bootstrap 'fade')
                // 'flash-message-entering' déclenche notre animation de chute
                alertDiv.classList.add('show', 'flash-message-entering');
            });
    
            // Optionnel mais propre : retire la classe d'animation une fois terminée
            alertDiv.addEventListener('animationend', () => {
                alertDiv.classList.remove('flash-message-entering');
            }, { once: true }); // { once: true } supprime l'écouteur après son exécution
            // --- Fin de la modification ---
    
    
            // Fait défiler la zone de notification vers le bas pour voir le nouveau message
            // C'est toujours pertinent avec column-reverse car le contenu "pousse" vers le haut
            container.scrollTop = container.scrollHeight;
    
            // Applique le comportement (auto-dismiss ou non)
            handleFlashMessage(alertDiv);
        }
    
        // Traitement initial des messages flash présents au chargement de la page
        document.addEventListener('DOMContentLoaded', () => {
            const flashContainer = document.getElementById(FLASH_CONTAINER_ID);
            if (flashContainer) {
                // Appliquer les styles flexbox ici si ce n'est pas dans le CSS global
                // flashContainer.style.display = 'flex';
                // flashContainer.style.flexDirection = 'column-reverse';
    
                const existingMessages = flashContainer.querySelectorAll(FLASH_MESSAGE_SELECTOR);
                existingMessages.forEach(handleFlashMessage);
    
                // Si le conteneur est scrollable, s'assurer qu'on voit les derniers messages (en bas)
                // Cette logique reste correcte avec column-reverse
                if (flashContainer.scrollHeight > flashContainer.clientHeight) {
                     flashContainer.scrollTop = flashContainer.scrollHeight;
                }
            }
        });
    
    })(); // Fin de l'IIFE
    