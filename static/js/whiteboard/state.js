// static/js/whiteboard/state.js

// --- SUPPRIMÉ : Imports liés aux anciens contrôles ---
// import { addCustomControls, deleteObject, renderIcon, deleteImg, cloneImg } from './controls.js';

let undoStack = [];
let redoStack = [];
let isSaving = false; // Flag pour éviter les sauvegardes concurrentes
let saveTimeout;      // Variable pour le debounce

// Fonction de sauvegarde avec debounce
function debouncedSaveCanvasState(canvas) {
    clearTimeout(saveTimeout); // Annule le timeout précédent
    if (isSaving) return; // Évite les sauvegardes concurrentes si une est déjà en cours de traitement

    saveTimeout = setTimeout(() => {
        isSaving = true; // Marque comme en cours de sauvegarde
        try {
            // --- MODIFIÉ : Ne plus inclure les noms des contrôles personnalisés ---
            const clonedCanvasState = canvas.toJSON(); // Obtenir l'état JSON standard
            undoStack.push(clonedCanvasState);
            redoStack = []; // Vider la pile redo lors d'une nouvelle action
            // console.log("Canvas state saved to undo stack.");
        } catch (error) {
            console.error("Erreur lors de la sauvegarde de l'état du canvas:", error);
        } finally {
            isSaving = false; // Marque la fin de la sauvegarde (même en cas d'erreur)
        }
    }, 300); // Délai de debounce (ajuster si nécessaire)
}

/**
 * Sauvegarde l'état actuel du canvas dans la pile undo (avec debounce).
 * @param {fabric.Canvas} canvas
 */
export function saveCanvasState(canvas) {
    debouncedSaveCanvasState(canvas);
}

// --- SUPPRIMÉ : Fonction addControlsToObject ---
// function addControlsToObject(obj, canvas) { ... }

/**
 * Annule la dernière action.
 * @param {fabric.Canvas} canvas
 */
export function undo(canvas) {
    if (undoStack.length > 1) { // Besoin d'au moins 2 états (l'état actuel et le précédent)
        redoStack.push(undoStack.pop()); // Déplace l'état actuel vers redo
        // Charge l'état précédent depuis undoStack
        const stateToLoad = undoStack[undoStack.length - 1];
        canvas.loadFromJSON(stateToLoad, () => { // Callback après chargement
            // --- SUPPRIMÉ : Boucle pour ré-appliquer les contrôles ---
            // canvas.getObjects().forEach(obj => addControlsToObject(obj, canvas));
            canvas.renderAll();
            console.log("Undo complete.");
        });
    } else {
        console.log("Undo stack empty or only initial state.");
    }
}

/**
 * Rétablit la dernière action annulée.
 * @param {fabric.Canvas} canvas
 */
export function redo(canvas) {
    if (redoStack.length > 0) {
        const stateToLoad = redoStack.pop(); // Prend l'état depuis redo
        undoStack.push(stateToLoad); // Le remet dans undo
        canvas.loadFromJSON(stateToLoad, () => { // Callback après chargement
            // --- SUPPRIMÉ : Boucle pour ré-appliquer les contrôles ---
            // canvas.getObjects().forEach(obj => addControlsToObject(obj, canvas));
            canvas.renderAll();
            console.log("Redo complete.");
        });
    } else {
        console.log("Redo stack empty.");
    }
}

/**
 * Charge les données du tableau blanc (objets, zoom, viewport) dans le canvas.
 * @param {fabric.Canvas} canvas
 * @param {object | string} data - Les données à charger (peut être l'objet complet {version, zoom, viewport, objects} ou juste les objets JSON).
 */
export function loadCanvas(canvas, data) {
    let objectsData = data;
    let initialZoom = 1;
    let initialViewport = fabric.iMatrix.concat(); // Matrice identité par défaut

    // Vérifier si les données ont la structure {version, zoom, viewport, objects}
    if (data && typeof data === 'object' && data.objects && data.zoom && data.viewport) {
        objectsData = data.objects; // Utiliser les objets imbriqués
        initialZoom = data.zoom;
        initialViewport = data.viewport;
        console.log("Loading canvas with zoom and viewport data.");
    } else {
        console.log("Loading canvas with legacy object data or empty data.");
        // Si data n'a pas la structure attendue, on suppose que c'est l'ancien format (juste les objets)
        // ou des données vides/invalides. loadFromJSON gérera les erreurs si objectsData n'est pas valide.
        objectsData = data; // Assigner data même si potentiellement invalide, loadFromJSON gère
    }

    // Charger les objets
    canvas.loadFromJSON(objectsData, () => { // Callback après chargement des objets
        // Appliquer le zoom et le viewport APRÈS le chargement des objets
        canvas.setViewportTransform(initialViewport); // Appliquer le viewport d'abord
        canvas.setZoom(initialZoom);                // Appliquer le zoom ensuite

        // --- SUPPRIMÉ : Boucle pour ré-appliquer les contrôles ---
        // canvas.getObjects().forEach(obj => addControlsToObject(obj, canvas));

        // Rendre le canvas avec le bon zoom/viewport
        canvas.renderAll();
        console.log("Canvas loaded successfully.");

        // Sauvegarder l'état initial chargé comme premier état dans l'historique undo
        // Utiliser une sauvegarde directe sans debounce pour l'état initial
        clearTimeout(saveTimeout); // Annuler tout debounce en cours
        isSaving = false;          // Réinitialiser le flag
        const initialCanvasState = canvas.toJSON(); // Obtenir l'état JSON standard
        undoStack = [initialCanvasState]; // Initialiser la pile undo avec cet état
        redoStack = []; // Réinitialiser redoStack car on charge un nouvel état
        console.log("Initial loaded state saved to undo stack.");
    }, (o, object) => {
        // Fonction de rappel pour chaque objet chargé (reviver) - utile pour le débogage
        // console.log("Loaded object:", o, object);
    });
}

/**
 * Sauvegarde l'état complet du tableau blanc (objets, zoom, viewport) sur le serveur.
 * @param {fabric.Canvas} canvas
 * @param {string} projetId
 */
export function saveWhiteboard(canvas, projetId) {
    // 1. Obtenir les données des objets (sans les contrôles)
    const objectsData = canvas.toJSON();
    // 2. Obtenir le niveau de zoom actuel
    const currentZoom = canvas.getZoom();
    // 3. Obtenir la transformation du viewport actuelle
    const currentViewport = canvas.viewportTransform;

    // 4. Créer l'objet de données complet à sauvegarder
    const saveData = {
        version: '1.1', // Version pour identifier la structure
        zoom: currentZoom,
        viewport: currentViewport,
        objects: objectsData // Les données des objets sont imbriquées
    };

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
        body: JSON.stringify(saveData), // Envoyer la nouvelle structure
    })
    .then(response => {
        if (!response.ok) {
            // Essayer de lire le message d'erreur JSON, sinon utiliser le statut HTTP
            return response.json().then(errData => {
                throw new Error(errData.message || `Erreur réseau ${response.status}`);
            }).catch(() => { // Si response.json() échoue aussi
                throw new Error(`Erreur réseau ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Sauvegarde réussie (avec zoom/viewport):', data);
        // Optionnel: Afficher une notification de succès discrète
        // showNotification('Tableau blanc sauvegardé !');
    })
    .catch((error) => {
        console.error('Erreur lors de la sauvegarde:', error);
        alert(`Erreur lors de la sauvegarde du tableau blanc : ${error.message}`);
    });
}
