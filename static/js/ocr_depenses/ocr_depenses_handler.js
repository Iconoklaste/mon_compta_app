// c:\wamp\www\mon_compta_app\static\js\ocr_depenses_handler.js
document.addEventListener('DOMContentLoaded', function() {
    // Sélectionne le formulaire principal. On va y attacher les données nécessaires.
    const expenseForm = document.querySelector('form[enctype="multipart/form-data"]'); // Cible le formulaire d'ajout de dépense
    if (!expenseForm) {
        console.error("Le formulaire de dépense n'a pas été trouvé.");
        return; // Arrête si le formulaire n'est pas là
    }

    const fileInput = expenseForm.querySelector('#attachment_file'); // Recherche dans le formulaire
    const ocrButton = expenseForm.querySelector('#ocr-trigger-button'); // Recherche dans le formulaire

    // Éléments du formulaire à remplir (recherche dans le formulaire)
    const dateInput = expenseForm.querySelector('#date');
    const montantInput = expenseForm.querySelector('#montant');
    const descriptionInput = expenseForm.querySelector('#description');
    const compteChargeSelect = expenseForm.querySelector('#compte_id');

    // Vérifie si tous les éléments nécessaires sont présents
    if (!fileInput || !ocrButton || !dateInput || !montantInput || !descriptionInput || !compteChargeSelect) {
        console.warn("Un ou plusieurs éléments nécessaires pour l'OCR (fichier, bouton, date, montant, description, compte de charge) n'ont pas été trouvés dans le formulaire.");
        // On n'arrête pas forcément, mais le bouton OCR pourrait ne pas s'activer ou fonctionner correctement.
        // Le bouton OCR sera désactivé par défaut de toute façon.
    }

    // Récupérer les données dynamiques depuis les attributs data-* du formulaire
    const ocrProcessUrl = expenseForm.dataset.ocrUrl;
    const csrfToken = expenseForm.dataset.csrfToken;

    if (!ocrProcessUrl) {
        console.error("L'URL de traitement OCR (data-ocr-url) n'est pas définie sur le formulaire.");
        // Désactiver le bouton si l'URL manque, même si un fichier est sélectionné
        if(ocrButton) ocrButton.disabled = true;
        return; // Ne pas continuer sans URL
    }
     if (!csrfToken) {
        console.error("Le token CSRF (data-csrf-token) n'est pas défini sur le formulaire.");
        // On pourrait aussi désactiver le bouton ici par sécurité
        // if(ocrButton) ocrButton.disabled = true;
        // Mais on le vérifiera surtout au moment du clic
    }


    // Activer le bouton OCR quand un fichier est sélectionné (si le bouton existe)
    if (fileInput && ocrButton) {
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                ocrButton.disabled = false;
            } else {
                ocrButton.disabled = true;
            }
        });
    }

    // Gérer le clic sur le bouton OCR (si le bouton existe)
    if (ocrButton) {
        ocrButton.addEventListener('click', function() {
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                alert("Veuillez d'abord sélectionner un fichier.");
                return;
            }
             if (!csrfToken) {
                 alert("Erreur de sécurité (Token CSRF manquant). Impossible de continuer.");
                 return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('expense_file', file); // Le nom doit correspondre à celui attendu par Flask

            // --- Récupérer la liste des comptes de charge depuis le select ---
            let liste_comptes_str = "";
            if (compteChargeSelect) {
                const options = Array.from(compteChargeSelect.options);
                liste_comptes_str = options
                    .filter(option => option.value !== '') // Exclure l'option vide "-- Sélectionner --"
                    .map(option => option.text.trim()) // Prendre le texte de chaque option
                    .join(', '); // Joindre avec une virgule et un espace
            }
            formData.append('liste_comptes', liste_comptes_str || "Aucun compte disponible"); // Ajouter la liste au FormData
            // -------------------------------------------------------------

            // Afficher un indicateur de chargement et désactiver le bouton
            ocrButton.disabled = true;
            ocrButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Traitement...';

            // Envoyer le fichier au backend en utilisant l'URL récupérée
            fetch(ocrProcessUrl, {
                method: 'POST',
                headers: {
                    // IMPORTANT: Inclure le token CSRF
                     'X-CSRFToken': csrfToken
                    // 'Content-Type': 'multipart/form-data' est défini automatiquement par fetch avec FormData
                },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    // Essayer de lire l'erreur JSON du backend si possible
                    return response.json().then(errData => {
                        throw new Error(errData.error || `Erreur HTTP ${response.status}`);
                    }).catch(() => { // Si pas de JSON, erreur générique
                        throw new Error(`Erreur HTTP ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(result => {
                if (result.success && result.extracted_data) {
                    console.log("Données extraites reçues:", result.extracted_data);
                    // --- MODIFICATION : Accéder au premier élément de la liste et utiliser les bonnes clés ---
                    // Vérifier si c'est bien une liste non vide
                    if (Array.isArray(result.extracted_data) && result.extracted_data.length > 0) {
                        const data = result.extracted_data[0]; // Prend le premier objet de la liste

                        // Pré-remplir les champs avec les clés retournées par le chat
                        if (data.date_facture && dateInput) dateInput.value = data.date_facture;
                        if (data.montant_total_ttc && montantInput) montantInput.value = data.montant_total_ttc; // Utilise montant_total_ttc
                        if (data.nom_fournisseur && descriptionInput) descriptionInput.value = data.nom_fournisseur; // Utilise nom_fournisseur pour la description

                        let alertMessage = "Informations extraites et pré-remplies :\n";
                        if (data.date_facture) alertMessage += `- Date: ${data.date_facture}\n`;
                        if (data.montant_total_ttc) alertMessage += `- Montant: ${data.montant_total_ttc}\n`;
                        if (data.nom_fournisseur) alertMessage += `- Description (Fournisseur): ${data.nom_fournisseur}\n`;
                        if (data.compte_charge_suggere) alertMessage += `- Compte suggéré: ${data.compte_charge_suggere}\n`;
                        alertMessage += "\nVeuillez vérifier les champs.";

                        alert(alertMessage);
                    } else {
                         // Si extracted_data n'est pas une liste ou est vide
                         throw new Error("Les données extraites reçues sont dans un format inattendu.");
                    }
                } else {
                    throw new Error(result.error || "Erreur lors de l'extraction des données.");
                }
            })
            .catch(error => {
                console.error('Erreur lors du traitement OCR:', error);
                alert(`Erreur: ${error.message}`);
            })
            .finally(() => {
                // Rétablir l'état initial du bouton
                ocrButton.disabled = false; // Réactiver même en cas d'erreur
                ocrButton.innerHTML = '<i class="fas fa-magic"></i> Extraire';
            });
        });
    } // Fin if (ocrButton)

}); // Fin DOMContentLoaded
