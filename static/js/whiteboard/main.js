// static/js/whiteboard/main.js
import { initializeCanvas } from './canvas.js';
// Importer les fonctions d'action depuis objects.js ou controls.js selon où elles sont définies
import { sendToBack, bringToFront, sendBackward, bringForward } from './objects.js';
import { deleteActiveObject } from './controls.js';
import { initializeUI, initializeModeButtons, updateModeButtonsUI, updateFontSizeSelector, updateFontFamilySelector, loadData } from './ui.js';
import { undo, redo, saveCanvasState } from './state.js';
import { initializeColorPickers, updateFillPickerUI, updateStrokePickerUI } from './color-picker.js';
import { initializeBrushSelectors } from './brush-manager.js';
import { initializeModeManager, setMode } from './mode-manager.js';
import { handlePaste } from './clipboard.js';
// Importer les fonctions de la nouvelle barre d'outils
import { initializeToolbar, showToolbar, hideToolbar } from './toolbar.js';

// --- SUPPRIMER l'import de addCustomControls si plus utilisé ---
// import { addCustomControls } from './controls.js'; // <-- Supprimé ou commenté

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
    }

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
    loadData(canvas, projetId);

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
    // (Suppression, Z-Order depuis une éventuelle barre latérale persistante)
    // NOTE: Si ces boutons n'existent QUE dans la toolbar flottante, ces listeners peuvent être supprimés.
    document.getElementById('delete')?.addEventListener('click', () => {
        deleteActiveObject(canvas); // Utilise la fonction importée (depuis objects.js ou controls.js)
    });
    document.getElementById('send-to-back')?.addEventListener('click', () => sendToBack(canvas));
    document.getElementById('bring-to-front')?.addEventListener('click', () => bringToFront(canvas));
    document.getElementById('send-backward')?.addEventListener('click', () => sendBackward(canvas));
    document.getElementById('bring-forward')?.addEventListener('click', () => bringForward(canvas));

    // --- SUPPRIMÉ : Listeners pour Gras/Italique (gérés par toolbar.js) ---
    // const boldButton = document.getElementById('bold-button');
    // const italicButton = document.getElementById('italic-button');
    // boldButton?.addEventListener('click', () => toggleTextStyle(...)); // <-- Supprimé
    // italicButton?.addEventListener('click', () => toggleTextStyle(...)); // <-- Supprimé

    // --- Écouteurs d'événements du Canvas pour la barre d'outils et l'UI contextuelle ---

    canvas.on('selection:created', (event) => {
        const selectedObject = event.selected ? event.selected[0] : null;
        if (selectedObject) {
            showToolbar(selectedObject); // AFFICHER LA TOOLBAR FLOTTANTE
        }
        updateContextualUI(canvas, selectedObject); // Mettre à jour l'UI latérale si elle existe
    });

    canvas.on('selection:updated', (event) => {
        const selectedObject = event.selected ? event.selected[0] : null;
         if (selectedObject) {
            showToolbar(selectedObject); // AFFICHER/METTRE À JOUR LA TOOLBAR FLOTTANTE
        } else {
            hideToolbar(); // Cacher si la sélection devient vide
        }
        updateContextualUI(canvas, selectedObject); // Mettre à jour l'UI latérale si elle existe
    });

    canvas.on('selection:cleared', () => {
        hideToolbar(); // CACHER LA TOOLBAR FLOTTANTE
        updateContextualUI(canvas, null); // Mettre à jour l'UI latérale si elle existe
    });

    // --- SUPPRIMÉ : Listener object:modified (géré par toolbar.js) ---
    // canvas.on('object:modified', (event) => { ... });

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
        const opacity = selectedObject.opacity === undefined ? 1 : selectedObject.opacity;
        const stroke = selectedObject.stroke || null;
        const strokeWidth = selectedObject.strokeWidth === undefined ? 0 : selectedObject.strokeWidth;

        updateFillPickerUI(fill, opacity);
        updateStrokePickerUI(stroke, strokeWidth);

        // --- SUPPRIMÉ : Mise à jour des boutons Gras/Italique (gérés par toolbar.js) ---
        // if (selectedObject.type === 'textbox') { ... } else { ... }

    } else {
        // Réinitialiser les pickers si rien n'est sélectionné
        updateFillPickerUI(null, 1); // Ou valeurs par défaut
        updateStrokePickerUI(null, 0); // Ou valeurs par défaut

        // --- SUPPRIMÉ : Réinitialisation des boutons Gras/Italique ---
        // document.getElementById('bold-button')?.classList.remove('active');
        // document.getElementById('italic-button')?.classList.remove('active');
    }
}

// --- SUPPRIMÉ : Fonction toggleTextStyle (gérée par toolbar.js) ---
// function toggleTextStyle(canvas, styleName, activeValue, inactiveValue, buttonElement) { ... }
