// static/js/whiteboard/main.js
import { initializeCanvas } from './canvas.js';
// Importer les fonctions d'action depuis objects.js ou controls.js selon où elles sont définies
import { sendToBack, bringToFront, sendBackward, bringForward } from './objects.js';
import { deleteActiveObject } from './controls.js';
import { initializeUI, initializeModeButtons, updateModeButtonsUI, updateFontSizeSelector, updateFontFamilySelector, loadData, updateZoomIndicator } from './ui.js'; // Ajout updateZoomIndicator
import { undo, redo, saveCanvasState, loadCanvas, saveWhiteboard } from './state.js'; // Ajout loadCanvas, saveWhiteboard
import { initializeColorPickers, updateFillPickerUI, updateStrokePickerUI } from './color-picker.js';
import { initializeBrushSelectors } from './brush-manager.js';
import { initializeModeManager, setMode } from './mode-manager.js';
import { handlePaste } from './clipboard.js';
import { initializeToolbar, showToolbar, hideToolbar } from './toolbar.js';
// --- Import Minimap Functions (DÉSACTIVÉ) ---
// import { initMinimap, updateMinimap } from './minimap.js';

/*
// --- TODO: MINIMAP ---
// La fonctionnalité de minimap est actuellement désactivée en raison de problèmes de performance (scintillement).
// Problème principal : L'utilisation de canvas.toDataURL() dans updateMinimap est coûteuse et déclenche des
// mises à jour fréquentes via l'événement 'after:render', même avec un debounce.
//
// Pistes pour réactiver et améliorer :
// 1.  Alternative à toDataURL : Essayer d'utiliser directement minimapCtx.drawImage(mainCanvas.getElement(), ...)
//     et minimapCtx.drawImage(mainCanvas.upperCanvasEl, ...) pour dessiner les canvas principal et supérieur.
//     Cela pourrait être plus rapide mais nécessite de bien gérer l'état (notamment pendant le dessin libre).
// 2.  Ajuster le Debounce : Si on reste sur toDataURL, augmenter significativement le délai du debounce
//     (ex: 300ms ou plus) pour réduire la fréquence des mises à jour.
// 3.  Optimiser toDataURL : Réduire la qualité ('quality: 0.4') ou utiliser 'jpeg' pour accélérer la génération.
// 4.  Conditionner la mise à jour : Ne mettre à jour la minimap que sur des événements plus significatifs
//     (fin de pan/zoom, modification d'objet) plutôt que sur chaque 'after:render'.
// 5.  (Plus complexe) Utiliser un fabric.StaticCanvas dédié pour la minimap et cloner/synchroniser les objets.
// --- FIN TODO: MINIMAP ---
*/

// Debounce function (simple implementation - peut être commentée si non utilisée ailleurs)
/*
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};
*/

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM Loaded. Initializing canvas...");
    const canvas = initializeCanvas();
    if (!canvas) {
        console.error("ERREUR CRITIQUE : Le canvas n'a pas pu être initialisé !");
        return; // Arrêter si le canvas échoue
    }
    console.log("Canvas initialized:", canvas);

    const projetId = window.projetId; // Assurez-vous que projetId est défini globalement

    if (!projetId) {
        console.error("ID du projet non trouvé. L'application risque de ne pas fonctionner correctement.");
        // Peut-être désactiver la sauvegarde ou afficher un message plus visible
    }

    // --- Debounced Minimap Update (DÉSACTIVÉ) ---
    // const debouncedUpdateMinimap = debounce(() => updateMinimap(canvas), 250); // Augmenté à 250ms

    // 1. Initialiser le gestionnaire de modes
    initializeModeManager(canvas, updateModeButtonsUI, 'pan'); // Commence en mode 'pan'

    // 2. Initialiser les éléments UI généraux (police, zoom, sauvegarde)
    initializeUI(canvas, projetId);

    // 3. Initialiser les boutons de mode (Select, Pan, Formes, Texte)
    initializeModeButtons(canvas, setMode);

    // 4. Initialiser les sélecteurs de couleur
    initializeColorPickers(canvas);

    // 5. Initialiser les sélecteurs de pinceaux
    initializeBrushSelectors(canvas, setMode);

    // 6. Initialiser l'écouteur pour le collage
    document.addEventListener('paste', (event) => handlePaste(event, canvas));

    // 7. Initialiser la barre d'outils flottante
    console.log("Initializing toolbar...");
    initializeToolbar(canvas);
    console.log("Toolbar initialization called.");

    // 8. Charger les données existantes du tableau blanc
    // Note: loadData appelle maintenant loadCanvas qui gère le chargement initial et la sauvegarde de l'état initial
    loadData(canvas, projetId); // loadData est dans ui.js, il appelle loadCanvas de state.js

    // 9. --- Initialize Minimap (DÉSACTIVÉ) ---
    // initMinimap(canvas); // Passe l'instance du canvas principal

    // --- Écouteurs d'événements globaux ---

    // Annuler/Rétablir
    document.addEventListener('keydown', (event) => {
        const targetTagName = event.target.tagName.toLowerCase();
        const isInputFocused = targetTagName === 'input' || targetTagName === 'textarea' || event.target.isContentEditable;
        if (isInputFocused) {
            return; // Ignorer si un input/textarea/contentEditable est focus
        }

        if (event.ctrlKey || event.metaKey) { // metaKey pour macOS
            if (event.key === 'z') {
                event.preventDefault();
                undo(canvas);
            } else if (event.key === 'y') {
                event.preventDefault();
                redo(canvas);
            }
        }
    });

    // --- Écouteurs pour les actions qui NE changent PAS le mode ---
    // (Suppression, Z-Order depuis la barre latérale persistante)
    document.getElementById('delete')?.addEventListener('click', () => {
        deleteActiveObject(canvas);
    });
    document.getElementById('send-to-back')?.addEventListener('click', () => sendToBack(canvas));
    document.getElementById('bring-to-front')?.addEventListener('click', () => bringToFront(canvas));
    document.getElementById('send-backward')?.addEventListener('click', () => sendBackward(canvas));
    document.getElementById('bring-forward')?.addEventListener('click', () => bringForward(canvas));

    // --- Écouteurs d'événements du Canvas ---

    // Pour la barre d'outils flottante et l'UI contextuelle
    canvas.on('selection:created', (event) => {
        const selectedObject = event.selected ? event.selected[0] : null;
        if (selectedObject) {
            showToolbar(selectedObject);
        }
        updateContextualUI(canvas, selectedObject);
    });

    canvas.on('selection:updated', (event) => {
        const selectedObject = event.selected ? event.selected[0] : null;
         if (selectedObject) {
            showToolbar(selectedObject);
        } else {
            hideToolbar();
        }
        updateContextualUI(canvas, selectedObject);
    });

    canvas.on('selection:cleared', () => {
        hideToolbar();
        updateContextualUI(canvas, null);
    });

    // Pour la mise à jour de la minimap (DÉSACTIVÉ)
    /*
    canvas.on({
        // Utiliser la version debounced pour les événements fréquents comme pan/zoom
        'after:render': debouncedUpdateMinimap,
        // Mettre à jour immédiatement pour les changements de contenu
        'object:added': () => updateMinimap(canvas),
        'object:modified': () => updateMinimap(canvas), // Peut aussi être debounced si les modifs sont très fréquentes
        'object:removed': () => updateMinimap(canvas),
        // Mettre à jour si les dimensions du canvas changent (si vous implémentez le redimensionnement)
        // 'canvas:resized': () => updateMinimap(canvas) // Déjà géré par le listener 'resize' ci-dessous
    });
    */

    // Gérer le redimensionnement de la fenêtre (met à jour le canvas)
    // Note: initializeCanvas configure déjà un listener de redimensionnement qui appelle setCanvasDimensions.
    // L'appel à updateMinimap est commenté ici.
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // setCanvasDimensions() est appelé par le listener dans canvas.js
            // Il suffit de mettre à jour la minimap après le redimensionnement potentiel du canvas
            // updateMinimap(canvas); // <-- DÉSACTIVÉ
        }, 150); // Utiliser le même délai que dans canvas.js ou ajuster
    });

    // Rendu initial (peut être utile si le chargement prend du temps)
    canvas.requestRenderAll();

    console.log("Whiteboard main initialization complete.");

}); // Fin de DOMContentLoaded

/**
 * Met à jour les éléments UI contextuels (taille/famille de police, couleurs)
 * DANS UNE BARRE LATERALE (si elle existe toujours).
 * @param {fabric.Canvas} canvas
 * @param {fabric.Object | null} selectedObject
 */
function updateContextualUI(canvas, selectedObject) {
    // Mettre à jour les sélecteurs de police/taille (s'ils sont dans la barre latérale)
    updateFontSizeSelector(canvas);
    updateFontFamilySelector(canvas); // Note: peut être asynchrone

    // Mettre à jour les sélecteurs de couleur (s'ils sont dans la barre latérale)
    if (selectedObject) {
        const fill = selectedObject.fill || null;
        // Gérer l'opacité: utiliser la valeur si définie, sinon 1
        const opacity = selectedObject.opacity !== undefined ? selectedObject.opacity : 1;
        const stroke = selectedObject.stroke || null;
        // Gérer l'épaisseur: utiliser la valeur si définie, sinon 0 ou 1 selon le contexte
        const strokeWidth = selectedObject.strokeWidth !== undefined ? selectedObject.strokeWidth : 0;

        updateFillPickerUI(fill, opacity);
        updateStrokePickerUI(stroke, strokeWidth);

    } else {
        // Réinitialiser les pickers si rien n'est sélectionné (vers les valeurs par défaut)
        const defaultFillColor = 'black'; // Ou la couleur par défaut de votre UI
        const defaultFillOpacity = 1;
        const defaultStrokeColor = 'black'; // Ou la couleur par défaut de votre UI
        const defaultStrokeWidth = 1; // Ou 0 si vous préférez

        updateFillPickerUI(defaultFillColor, defaultFillOpacity);
        updateStrokePickerUI(defaultStrokeColor, defaultStrokeWidth);

        // Assurez-vous que les sliders sont aussi réinitialisés si updateUI ne le fait pas
        const fillSlider = document.getElementById('fill-transparency-slider');
        const strokeSlider = document.getElementById('stroke-width-slider');
        if (fillSlider) fillSlider.value = defaultFillOpacity;
        if (strokeSlider) strokeSlider.value = defaultStrokeWidth;
    }
}
