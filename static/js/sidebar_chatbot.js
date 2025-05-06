document.addEventListener('DOMContentLoaded', () => {
    // Éléments principaux de la sidebar de chat
    const chatbotSidebarContainer = document.getElementById('chatbot-sidebar-container');
    const chatbotSidebarHeader = document.getElementById('chatbot-sidebar-header'); // Utilise l'ID direct
    const toggleChatbotSidebarBtn = document.getElementById('toggle-chatbot-sidebar-btn');
    const chatbotSidebarMessagesContainer = document.getElementById('chatbot-sidebar-messages'); // Utilise l'ID direct
    const sidebarLoadingIndicator = document.getElementById('sidebar-chat-loading-indicator'); // Indicateur dans la zone de messages

    // Éléments du formulaire
    const sidebarChatbotForm = document.getElementById('sidebar-chatbot-form');
    const sidebarChatbotQuestionInput = document.getElementById('sidebar-chatbot-question-input');
    const sidebarChatbotSubmitBtn = sidebarChatbotForm ? sidebarChatbotForm.querySelector('button[type="submit"]') : null;
    const chatbotInputArea = document.getElementById('chatbot-sidebar-input-area'); // Zone d'input pour déclencher l'ouverture

    // Spinner et avatar de la barre de saisie (si vous les conservez distinctement)
    const inputBarSpinner = document.getElementById('chatbot-input-spinner-sidebar');
    const inputBarAvatar = document.getElementById('chatbot-user-avatar-sidebar');

    // URL de l'avatar de Loova (depuis data-attribute pour un fichier JS statique)
    let loovaAvatarSrc = "/static/asset/avatar-loova.png"; // Fallback
    if (chatbotSidebarContainer && chatbotSidebarContainer.dataset.loovaAvatarSrc && chatbotSidebarContainer.dataset.loovaAvatarSrc.trim() !== "") {
        loovaAvatarSrc = chatbotSidebarContainer.dataset.loovaAvatarSrc;
    } else {
        console.warn("Chat Sidebar: Attribut 'data-loova-avatar-src' non trouvé ou vide sur #chatbot-sidebar-container. Utilisation du chemin par défaut pour l'avatar.");
    }

    // Vérification des éléments essentiels
    if (!chatbotSidebarContainer || !sidebarChatbotForm || !sidebarChatbotQuestionInput || !sidebarChatbotSubmitBtn || !chatbotSidebarMessagesContainer || !chatbotSidebarHeader || !toggleChatbotSidebarBtn || !sidebarLoadingIndicator || !chatbotInputArea) {
        console.error('Chat Sidebar: Un ou plusieurs éléments HTML requis sont manquants. La fonctionnalité du chat pourrait être altérée.');
        return;
    }

    const csrfTokenInput = sidebarChatbotForm.querySelector('input[name="csrf_token"]');
    const csrfToken = csrfTokenInput ? csrfTokenInput.value : null;

    if (!csrfToken) {
        console.error("Chat Sidebar: Token CSRF non trouvé. Les requêtes POST échoueront.");
        alert("Une erreur de sécurité critique est survenue (Token manquant). Veuillez rafraîchir la page et réessayer.");
        if(sidebarChatbotQuestionInput) sidebarChatbotQuestionInput.disabled = true;
        if(sidebarChatbotSubmitBtn) sidebarChatbotSubmitBtn.disabled = true;
        return;
    }

    let isSidebarChatExpanded = false;

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function scrollToSidebarMessagesBottom() {
        if (chatbotSidebarMessagesContainer) {
            chatbotSidebarMessagesContainer.scrollTop = chatbotSidebarMessagesContainer.scrollHeight;
        }
    }

    function addMessageToSidebarChat(content, role, isHtml = false) {
        if (!chatbotSidebarMessagesContainer) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message mb-2 p-2 ${role}-message`;

        if (role === 'user') {
            messageDiv.classList.add('text-end');
            messageDiv.innerHTML = `<p class="alert alert-primary d-inline-block p-2 mb-1">${escapeHTML(content)}</p>`;
        } else if (role === 'assistant') {
            messageDiv.classList.add('bot-message');
            const assistantContent = isHtml ? content : escapeHTML(content);
            messageDiv.innerHTML = `
                <div class="d-flex align-items-start">
                    <img src="${loovaAvatarSrc}" alt="Loova" class="rounded-circle me-2" style="width: 30px; height: 30px; margin-top: 5px;">
                    <div class="alert alert-secondary d-inline-block p-2 mb-1 chatbot-response-content">${assistantContent}</div>
                </div>`;
        }
        chatbotSidebarMessagesContainer.appendChild(messageDiv);
        scrollToSidebarMessagesBottom();
    }

    function openChatView() { // Affiche le header et les messages
        if (isSidebarChatExpanded || !chatbotSidebarContainer || !chatbotSidebarHeader || !chatbotSidebarMessagesContainer) return;
        chatbotSidebarContainer.classList.add('is-expanded'); // Pour CSS (ex: rotation flèche)
        chatbotSidebarHeader.style.display = 'flex';
        chatbotSidebarMessagesContainer.style.display = 'block';
        isSidebarChatExpanded = true;
        scrollToSidebarMessagesBottom();
        sidebarChatbotQuestionInput.focus();
    }

    function closeChatView() { // Cache le header et les messages, mais garde la barre d'input
        if (!isSidebarChatExpanded || !chatbotSidebarContainer || !chatbotSidebarHeader || !chatbotSidebarMessagesContainer) return;
        chatbotSidebarContainer.classList.remove('is-expanded');
        chatbotSidebarHeader.style.display = 'none';
        chatbotSidebarMessagesContainer.style.display = 'none';
        isSidebarChatExpanded = false;
    }

    // Le clic sur la zone d'input ouvre la vue chat si elle est fermée
    if (chatbotInputArea) {
        chatbotInputArea.addEventListener('click', () => { // Ou 'focusin' sur footerChatbotQuestionInput
            if (!isSidebarChatExpanded) {
                openChatView();
            }
        });
    }

    // Le bouton toggle ouvre ou ferme la vue chat
    if (toggleChatbotSidebarBtn) {
        toggleChatbotSidebarBtn.addEventListener('click', () => {
            if (isSidebarChatExpanded) {
                closeChatView();
            } else {
                openChatView();
            }
        });
    }



    sidebarChatbotForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const question = sidebarChatbotQuestionInput.value.trim();
        if (!question) {
            return;
        }

        if (!isSidebarChatExpanded) {
            openChatView(); // S'assurer que la vue est ouverte avant d'envoyer
        }

        addMessageToSidebarChat(question, 'user');
        sidebarChatbotQuestionInput.value = ''; // Vider l'input après avoir affiché le message utilisateur


        // Afficher l'indicateur de chargement dans la zone des messages
        if (sidebarLoadingIndicator && chatbotSidebarMessagesContainer) {
            chatbotSidebarMessagesContainer.appendChild(sidebarLoadingIndicator); // L'ajouter à la fin
            sidebarLoadingIndicator.style.display = 'flex'; // ou 'block' selon le style
            scrollToSidebarMessagesBottom();
        }

        // Désactiver les éléments du formulaire et gérer le spinner de la barre de saisie
        sidebarChatbotQuestionInput.disabled = true;
        if (sidebarChatbotSubmitBtn) sidebarChatbotSubmitBtn.disabled = true;
        if (inputBarSpinner) inputBarSpinner.classList.remove('d-none');
        if (inputBarAvatar) inputBarAvatar.classList.add('d-none');

        let isRedirecting = false;

        fetch(sidebarChatbotForm.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ question: question })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.error || `Erreur serveur (${response.status})`);
                }).catch(() => {
                    throw new Error(`Erreur HTTP ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (sidebarLoadingIndicator) sidebarLoadingIndicator.style.display = 'none';

            if (data.redirect_url) {
                isRedirecting = true;
                // Optionnel: afficher un message avant la redirection
                // if(data.answer) addMessageToFooterChat(data.answer, 'assistant', true);
                window.location.href = data.redirect_url;
            } else {
                if (!isSidebarChatExpanded) openChatView(); // S'assurer que c'est ouvert

                if (data.success && data.answer) {
                    addMessageToSidebarChat(data.answer, 'assistant', true);
                } else if (data.answer) { // Si 'success' n'est pas là mais 'answer' oui
                    addMessageToSidebarChat(data.answer, 'assistant', true);
                }
                else {
                    addMessageToSidebarChat(data.error || 'Réponse non valide du serveur.', 'assistant', false);
                }
            }
        })
        .catch(error => {
            console.error('Erreur avec le chatbot de la sidebar:', error);
            if (sidebarLoadingIndicator) sidebarLoadingIndicator.style.display = 'none';
            if (!isSidebarChatExpanded) openChatView(); // Ouvrir pour afficher l'erreur
            addMessageToSidebarChat(`Désolé, une erreur de communication est survenue: ${error.message}`, 'assistant', false);
        })
        .finally(() => {
            // Assurer que l'indicateur de chargement est caché
            if (sidebarLoadingIndicator && sidebarLoadingIndicator.parentElement === chatbotSidebarMessagesContainer) {
                // Le cacher simplement, car il est ajouté/retiré du DOM au besoin
                sidebarLoadingIndicator.style.display = 'none';
            }

            if (!isRedirecting) {
                sidebarChatbotQuestionInput.disabled = false;
                if (sidebarChatbotSubmitBtn) sidebarChatbotSubmitBtn.disabled = false;

                if (inputBarSpinner) inputBarSpinner.classList.add('d-none');
                if (inputBarAvatar) inputBarAvatar.classList.remove('d-none');

                if (isSidebarChatExpanded) { // Si la vue chat est ouverte, focus sur l'input
                    sidebarChatbotQuestionInput.focus();
                }
                scrollToSidebarMessagesBottom();
            } else {
                // En cas de redirection, réinitialiser l'état visuel de la barre de saisie
                if (inputBarSpinner) inputBarSpinner.classList.add('d-none');
                if (inputBarAvatar) inputBarAvatar.classList.remove('d-none');
            }
        });
    });

    // État initial : la vue détaillée du chat (header et messages) est cachée.
    // La barre d'input est toujours visible.
    if (chatbotSidebarHeader) chatbotSidebarHeader.style.display = 'none';
    if (chatbotSidebarMessagesContainer) chatbotSidebarMessagesContainer.style.display = 'none';
    if (chatbotSidebarContainer) chatbotSidebarContainer.classList.remove('is-expanded');
    isSidebarChatExpanded = false; // Confirmer l'état initial
});