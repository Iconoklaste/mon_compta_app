// state.js
// Importe addCustomControls au lieu de addDuplicateControl et duplicateObject
import { addCustomControls, deleteObject, renderIcon, deleteImg, cloneImg } from './controls.js';

let undoStack = [];
let redoStack = [];
let isSaving = false; // Flag to prevent concurrent saves

// Debounced save function
function debouncedSaveCanvasState(canvas) {
    if (isSaving) return; // Prevent concurrent saves
    isSaving = true;
    setTimeout(() => {
        // Inclure les noms des contrôles personnalisés dans toJSON
        const clonedCanvas = JSON.parse(JSON.stringify(canvas.toJSON(['deleteControl', 'duplicateControl'])));
        undoStack.push(clonedCanvas);
        redoStack = [];
        isSaving = false;
    }, 100); // Adjust delay as needed
}

export function saveCanvasState(canvas) {
    debouncedSaveCanvasState(canvas);
}

// Fonction simplifiée pour ajouter les contrôles via la fonction centralisée
function addControlsToObject(obj, canvas) {
    // Appelle la fonction centralisée de controls.js pour ajouter les deux contrôles
    addCustomControls(obj, canvas);
}

export function undo(canvas) {
    if (undoStack.length > 1) {
        redoStack.push(undoStack.pop());
        // Utilise le dernier état valide dans undoStack
        const stateToLoad = undoStack[undoStack.length - 1];
        canvas.loadFromJSON(stateToLoad, function() { // Callback après chargement
            canvas.getObjects().forEach(function(obj) {
                // Ré-applique les contrôles après le chargement
                addControlsToObject(obj, canvas);
            });
            canvas.renderAll();
        });
    }
}

export function redo(canvas) {
    if (redoStack.length > 0) {
        const stateToLoad = redoStack.pop();
        undoStack.push(stateToLoad);
        canvas.loadFromJSON(stateToLoad, function() { // Callback après chargement
            canvas.getObjects().forEach(function(obj) {
                // Ré-applique les contrôles après le chargement
                addControlsToObject(obj, canvas);
            });
            canvas.renderAll();
        });
    }
}

export function loadCanvas(canvas, data) {
    // --- MODIFICATION ICI ---
    // Vérifier si les données ont la nouvelle structure (avec zoom/viewport)
    // ou l'ancienne structure (juste les objets) pour la compatibilité descendante.
    let objectsData = data;
    let initialZoom = 1; // Zoom par défaut
    let initialViewport = fabric.iMatrix.concat(); // Viewport par défaut (identité)

    if (data && typeof data === 'object' && data.objects && data.zoom && data.viewport) {
        // Nouvelle structure détectée
        objectsData = data.objects;
        initialZoom = data.zoom;
        initialViewport = data.viewport;
        console.log("Loading canvas with zoom and viewport data.");
    } else {
        console.log("Loading canvas with legacy object data only.");
        // Si data n'est pas un objet ou n'a pas les clés attendues,
        // on suppose que c'est l'ancien format (juste les objets JSON)
        // ou des données invalides (loadFromJSON gérera les erreurs).
        objectsData = data;
    }
    // --- FIN MODIFICATION ---

    // Charger les objets
    canvas.loadFromJSON(objectsData, function() { // Callback après chargement des objets
        // Appliquer le zoom et le viewport APRÈS le chargement des objets
        canvas.setZoom(initialZoom);
        canvas.setViewportTransform(initialViewport);

        // Ré-appliquer les contrôles personnalisés après le chargement
        canvas.getObjects().forEach(function(obj) {
            addControlsToObject(obj, canvas);
        });

        // Rendre le canvas avec le bon zoom/viewport
        canvas.renderAll();

        // Sauvegarde l'état initial chargé dans l'historique undo
        saveCanvasState(canvas);
        // Réinitialise redoStack car on charge un nouvel état
        redoStack = [];
    });
}

export function saveWhiteboard(canvas, projetId) {
    // --- MODIFICATION ICI ---
    // 1. Obtenir les données des objets
    const objectsData = canvas.toJSON(['deleteControl', 'duplicateControl']);
    // 2. Obtenir le niveau de zoom actuel
    const currentZoom = canvas.getZoom();
    // 3. Obtenir la transformation du viewport actuelle
    const currentViewport = canvas.viewportTransform;

    // 4. Créer l'objet de données complet à sauvegarder
    const saveData = {
        version: '1.1', // Version pour identifier la structure
        zoom: currentZoom,
        viewport: currentViewport,
        objects: objectsData // Les données des objets sont maintenant imbriquées
    };
    // --- FIN MODIFICATION ---

    const csrfTokenElement = document.getElementById('csrfToken');
    if (!csrfTokenElement) {
        console.error("L'élément CSRF token avec l'ID 'csrfToken' n'a pas été trouvé.");
        alert("Erreur de sécurité : Impossible de sauvegarder le tableau blanc.");
        return;
    }
    const csrfToken = csrfTokenElement.value;

    fetch(`/save_whiteboard/${projetId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        // Envoyer la nouvelle structure de données
        body: JSON.stringify(saveData),
    })
    .then(response => {
        // ... (gestion de la réponse inchangée) ...
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error(errData.message || `Erreur réseau ${response.status}`);
            }).catch(() => {
                throw new Error(`Erreur réseau ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Sauvegarde réussie (avec zoom/viewport):', data);
        // alert('Tableau blanc sauvegardé avec succès !');
    })
    .catch((error) => {
        console.error('Erreur lors de la sauvegarde:', error);
        alert(`Erreur lors de la sauvegarde du tableau blanc : ${error.message}`);
    });
}
