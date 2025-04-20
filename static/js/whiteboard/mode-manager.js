// static/js/whiteboard/mode-manager.js

/**
 * @typedef {'select' | 'pan' | 'draw' | 'shape' | 'text'} InteractionMode
 */

let _canvas = null;
/** @type {InteractionMode} */
let _currentMode = 'pan'; // Mode initial par défaut
let _updateModeButtonsUICallback = () => {}; // Callback pour mettre à jour l'UI des boutons

/**
 * Initialise le gestionnaire de modes.
 * @param {fabric.Canvas} canvasInstance - L'instance du canvas Fabric.js.
 * @param {function(InteractionMode): void} updateButtonsCallback - Fonction pour mettre à jour l'UI des boutons.
 * @param {InteractionMode} [initialMode='select'] - Le mode initial.
 */
export function initializeModeManager(canvasInstance, updateButtonsCallback, initialMode = 'pan') {
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

    // --- MODIFICATION START ---
    // Si on quitte le mode 'draw'...
    if (previousMode === 'draw') {
        console.log('[ModeManager] Cleaning up from DRAW mode.');
        // Vérifier si un pinceau est actif et si quelque chose a été dessiné
        if (_canvas.freeDrawingBrush && _canvas.freeDrawingBrush._drawn === true) {
            console.log('[ModeManager] Drawing detected (_drawn=true). Forcing convertToImg...');
            try {
                // Appeler convertToImg explicitement AVANT de changer quoi que ce soit d'autre
                _canvas.freeDrawingBrush.convertToImg();
                console.log('[ModeManager] convertToImg finished successfully.');
                // _drawn est remis à false par convertToImg lui-même
            } catch (error) {
                console.error('[ModeManager] Error calling convertToImg during cleanup:', error);
                // Nettoyer le canvas temporaire en cas d'erreur pour éviter les artefacts
                if (_canvas.contextTop) {
                    _canvas.clearContext(_canvas.contextTop);
                }
                // Réinitialiser le flag manuellement si convertToImg a échoué avant
                if (_canvas.freeDrawingBrush) {
                    _canvas.freeDrawingBrush._drawn = false;
                }
            }
        } else {
             console.log('[ModeManager] No drawing detected (_drawn=false or no brush). Skipping forced convertToImg.');
             // Nettoyer le canvas temporaire s'il n'y avait rien à convertir
             if (_canvas.contextTop) {
                 _canvas.clearContext(_canvas.contextTop);
             }
        }

        // On ne met toujours PAS isDrawingMode = false ici.
        // _configureCanvasForMode s'en chargera pour le nouveau mode.

        // Assurer le nettoyage des listeners de forme (au cas où)
        if (typeof _canvas.removeShapeListeners === 'function') {
            _canvas.removeShapeListeners();
        }

    } else {
        // Pour tous les autres modes, on peut mettre isDrawingMode = false sans risque
        _canvas.isDrawingMode = false;
    }
    // --- MODIFICATION END ---

    // Désactiver le flag de dessin de forme (si utilisé)
    _canvas.isDrawingShape = false;
    // Désactiver le panning spécifique du canvas (arrière-plan)
    _canvas.togglePanningMode(false);

    // Réinitialiser les curseurs (sera redéfini par le nouveau mode)
    _canvas.defaultCursor = 'default';
    _canvas.hoverCursor = 'move';

    // Assurer que la sélection est généralement réactivée (sauf si le nouveau mode la désactive)
    _canvas.selection = true;
}

/**
 * Configure les propriétés du canvas pour le nouveau mode.
 * @param {InteractionMode} newMode - Le mode à configurer.
 */
function _configureCanvasForMode(newMode) {
    if (!_canvas) return;

    // Définir les valeurs par défaut (seront écrasées si nécessaire)
    _canvas.isDrawingMode = false; // Important de le définir ici pour les modes NON-draw
    _canvas.selection = true;
    _canvas.defaultCursor = 'default';
    _canvas.hoverCursor = 'move';
    _canvas.togglePanningMode(false);

    switch (newMode) {
        case 'select':
            // Les valeurs par défaut sont correctes
            break;
        case 'pan':
            _canvas.defaultCursor = 'grab';
            _canvas.hoverCursor = 'grab'; // Ou 'grabbing' si géré dans canvas.js
            _canvas.togglePanningMode(true); // Active le pan de l'arrière-plan
            _canvas.selection = false;
            _canvas.discardActiveObject();
            _canvas.requestRenderAll(); // Mettre à jour l'affichage pour enlever les contrôles
            // isDrawingMode est déjà false par défaut
            break;
        case 'draw':
            _canvas.selection = false;
            _canvas.isDrawingMode = true; // Définir explicitement sur true
            _canvas.defaultCursor = 'crosshair'; // Ou le curseur spécifique du pinceau
            _canvas.hoverCursor = 'crosshair';
            // La configuration du pinceau est gérée par brush-manager.js
            break;
        // ... autres cas (shape, text) ...
        case 'shape':
            _canvas.selection = false; // Désactivé pendant le dessin de la forme
            _canvas.defaultCursor = 'crosshair';
            _canvas.hoverCursor = 'crosshair';
            _canvas.discardActiveObject();
            // isDrawingMode est déjà false par défaut
            // Les listeners pour dessiner la forme sont ajoutés par objects.js
            break;
        case 'text':
            _canvas.selection = false; // Désactivé temporairement jusqu'à ce que le texte soit ajouté
            _canvas.defaultCursor = 'text';
            _canvas.hoverCursor = 'text';
            _canvas.discardActiveObject();
            // isDrawingMode est déjà false par défaut
            // L'objet texte est ajouté immédiatement par objects.js
            break;
        default:
            console.warn(`Mode inconnu: ${newMode}. Retour au mode select.`);
            _configureCanvasForMode('select'); // Fallback
            _currentMode = 'select'; // Corriger l'état interne en cas d'erreur
            break;
    }
}