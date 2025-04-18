// static/js/whiteboard/mode-manager.js

/**
 * @typedef {'select' | 'pan' | 'draw' | 'shape' | 'text'} InteractionMode
 */

let _canvas = null;
/** @type {InteractionMode} */
let _currentMode = 'select'; // Mode initial par défaut
let _updateModeButtonsUICallback = () => {}; // Callback pour mettre à jour l'UI des boutons

/**
 * Initialise le gestionnaire de modes.
 * @param {fabric.Canvas} canvasInstance - L'instance du canvas Fabric.js.
 * @param {function(InteractionMode): void} updateButtonsCallback - Fonction pour mettre à jour l'UI des boutons.
 * @param {InteractionMode} [initialMode='select'] - Le mode initial.
 */
export function initializeModeManager(canvasInstance, updateButtonsCallback, initialMode = 'select') {
    if (!canvasInstance) {
        console.error("ModeManager: Instance de canvas non fournie.");
        return;
    }
    _canvas = canvasInstance;
    _updateModeButtonsUICallback = updateButtonsCallback || (() => {});
    // Définir le mode initial sans effectuer de nettoyage (car c'est le premier état)
    _currentMode = initialMode;
    _configureCanvasForMode(_currentMode);
    _updateModeButtonsUICallback(_currentMode); // Mettre à jour l'UI initiale
    console.log(`Mode Manager Initialized. Initial mode: ${_currentMode}`);
}

/**
 * Définit le mode d'interaction actif sur le canvas.
 * @param {InteractionMode} newMode - Le nouveau mode à activer.
 */
export function setMode(newMode) {
    if (!_canvas) {
        console.error("ModeManager: Canvas non initialisé.");
        return;
    }
    if (newMode === _currentMode) {
        // console.log(`Mode already set to: ${newMode}`);
        return; // Pas de changement nécessaire
    }

    console.log(`Switching mode from ${_currentMode} to ${newMode}`);

    // 1. Nettoyer l'état du mode précédent
    _cleanupPreviousMode(_currentMode);

    // 2. Configurer le canvas pour le nouveau mode
    _configureCanvasForMode(newMode);

    // 3. Mettre à jour l'état interne
    _currentMode = newMode;

    // 4. Mettre à jour l'UI des boutons
    _updateModeButtonsUICallback(_currentMode);

    // 5. Rendre le canvas
    _canvas.requestRenderAll();
}

/**
 * Retourne le mode d'interaction actuellement actif.
 * @returns {InteractionMode} Le mode actuel.
 */
export function getCurrentMode() {
    return _currentMode;
}

// --- Fonctions internes ---

/**
 * Réinitialise les configurations spécifiques au mode précédent.
 * @param {InteractionMode} previousMode - Le mode qui était actif.
 */
function _cleanupPreviousMode(previousMode) {
    if (!_canvas) return;

    // Désactiver le mode dessin
    _canvas.isDrawingMode = false;
    // Désactiver le flag de dessin de forme (si utilisé)
    _canvas.isDrawingShape = false; // Assurez-vous que ce flag existe et est utilisé dans objects.js
    // Désactiver le panning spécifique du canvas (arrière-plan)
    _canvas.togglePanningMode(false); // Assurez-vous que canvas.js expose cette fonction
    // Supprimer les listeners spécifiques au dessin de formes (si présents)
    if (typeof _canvas.removeShapeListeners === 'function') {
        _canvas.removeShapeListeners();
    }
    // Réinitialiser les curseurs (sera redéfini par le nouveau mode)
    _canvas.defaultCursor = 'default';
    _canvas.hoverCursor = 'move'; // Ou 'default' selon votre préférence

    // Assurer que la sélection est généralement réactivée (sauf si le nouveau mode la désactive)
    _canvas.selection = true;
}

/**
 * Configure les propriétés du canvas pour le nouveau mode.
 * @param {InteractionMode} newMode - Le mode à configurer.
 */
function _configureCanvasForMode(newMode) {
    if (!_canvas) return;

    switch (newMode) {
        case 'select':
            _canvas.selection = true;
            _canvas.defaultCursor = 'default';
            _canvas.hoverCursor = 'move';
            _canvas.togglePanningMode(false); // Désactive le pan de l'arrière-plan
            _canvas.isDrawingMode = false;
            break;
        case 'pan':
            _canvas.selection = true; // Permet la sélection/déplacement d'objets *aussi*
            _canvas.defaultCursor = 'grab';
            _canvas.hoverCursor = 'grab'; // Ou 'grabbing' si géré dans canvas.js
            _canvas.togglePanningMode(true); // Active le pan de l'arrière-plan
            _canvas.isDrawingMode = false;
            break;
        case 'draw':
            _canvas.selection = false;
            _canvas.isDrawingMode = true;
            _canvas.defaultCursor = 'crosshair'; // Ou le curseur spécifique du pinceau
            _canvas.hoverCursor = 'crosshair';
            _canvas.togglePanningMode(false);
            // La configuration du pinceau (couleur, épaisseur) est gérée par brush-manager.js
            break;
        case 'shape':
            _canvas.selection = false; // Désactivé pendant le dessin de la forme
            _canvas.defaultCursor = 'crosshair';
            _canvas.hoverCursor = 'crosshair';
            _canvas.togglePanningMode(false);
            _canvas.isDrawingMode = false;
            // Les listeners pour dessiner la forme sont ajoutés par objects.js
            break;
        case 'text':
            _canvas.selection = false; // Désactivé temporairement jusqu'à ce que le texte soit ajouté
            _canvas.defaultCursor = 'text'; // Ou 'default' car l'objet est ajouté immédiatement
            _canvas.hoverCursor = 'text';
            _canvas.togglePanningMode(false);
            _canvas.isDrawingMode = false;
            // L'objet texte est ajouté immédiatement par objects.js
            break;
        default:
            console.warn(`Mode inconnu: ${newMode}. Retour au mode select.`);
            _configureCanvasForMode('select'); // Fallback
            _currentMode = 'select'; // Corriger l'état interne en cas d'erreur
            break;
    }
}
