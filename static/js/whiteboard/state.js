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
    canvas.loadFromJSON(data, function() { // Callback après chargement
        canvas.getObjects().forEach(function(obj) {
            // Ré-applique les contrôles après le chargement
            addControlsToObject(obj, canvas);
        });
        canvas.renderAll();
        // Sauvegarde l'état initial chargé dans l'historique undo
        // (Important pour que le premier 'undo' ne vide pas le canvas)
        saveCanvasState(canvas);
        // Réinitialise redoStack car on charge un nouvel état
        redoStack = [];
    });
}

export function saveWhiteboard(canvas, projetId) {
    // Inclure les noms des contrôles personnalisés dans toJSON
    const canvasData = canvas.toJSON(['deleteControl', 'duplicateControl']);
    const csrfTokenElement = document.getElementById('csrfToken'); // Vérifier si l'élément existe

    if (!csrfTokenElement) {
        console.error("L'élément CSRF token avec l'ID 'csrfToken' n'a pas été trouvé.");
        alert("Erreur de sécurité : Impossible de sauvegarder le tableau blanc.");
        return; // Arrêter si le token n'est pas trouvé
    }
    const csrfToken = csrfTokenElement.value;

    fetch(`/save_whiteboard/${projetId}`, { // Assure-toi que cette route est correcte
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(canvasData),
    })
    .then(response => {
        if (!response.ok) {
            // Essayer de lire le message d'erreur du serveur si possible
            return response.json().then(errData => {
                throw new Error(errData.message || `Erreur réseau ${response.status}`);
            }).catch(() => {
                // Si le corps n'est pas JSON ou vide
                throw new Error(`Erreur réseau ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Sauvegarde réussie:', data);
        // Optionnel: Afficher une notification de succès à l'utilisateur
        // alert('Tableau blanc sauvegardé avec succès !');
    })
    .catch((error) => {
        console.error('Erreur lors de la sauvegarde:', error);
        // Afficher une erreur plus visible à l'utilisateur
        alert(`Erreur lors de la sauvegarde du tableau blanc : ${error.message}`);
    });
}
