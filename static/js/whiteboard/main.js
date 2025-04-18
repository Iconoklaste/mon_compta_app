// static/js/whiteboard/main.js
import { initializeCanvas } from './canvas.js';
import { deleteActiveObject, sendToBack, bringToFront, sendBackward, bringForward } from './objects.js'; // Fonctions qui ne changent pas de mode
import { initializeUI, initializeModeButtons, updateModeButtonsUI, updateFontSizeSelector, updateFontFamilySelector, loadData } from './ui.js';
import { undo, redo, saveCanvasState } from './state.js'; // Ajout saveCanvasState si nécessaire ici
import { initializeColorPickers, updateFillPickerUI, updateStrokePickerUI } from './color-picker.js';
import { initializeBrushSelectors } from './brush-manager.js';
import { initializeModeManager, setMode } from './mode-manager.js'; // Import du mode manager

document.addEventListener('DOMContentLoaded', () => {
    const canvas = initializeCanvas();
    const projetId = window.projetId; // Assurez-vous que projetId est défini globalement

    if (!projetId) {
        console.error("ID du projet non trouvé. L'application risque de ne pas fonctionner correctement.");
        // Afficher une erreur à l'utilisateur ?
    }

    // 1. Initialiser le gestionnaire de modes (AVANT l'UI qui en dépend)
    // Passe la fonction de mise à jour de l'UI des boutons
    initializeModeManager(canvas, updateModeButtonsUI, 'select'); // Commence en mode 'select'

    // 2. Initialiser les éléments UI généraux (police, zoom, sauvegarde)
    initializeUI(canvas, projetId);

    // 3. Initialiser les boutons de mode (Select, Pan, Formes, Texte)
    // Passe la fonction setMode du manager pour que les boutons puissent changer le mode
    initializeModeButtons(canvas, setMode);

    // 4. Initialiser les sélecteurs de couleur
    initializeColorPickers(canvas);

    // 5. Initialiser les sélecteurs de pinceaux (pour le mode dessin)
    // Passe la fonction setMode pour activer le mode 'draw' lors de la sélection d'un pinceau
    initializeBrushSelectors(canvas, setMode);

    // 6. Charger les données existantes du tableau blanc
    loadData(canvas, projetId);

    // --- Écouteurs d'événements globaux ---

    // Annuler/Rétablir
    document.addEventListener('keydown', (event) => {
        // Ignorer si un input/textarea est focus pour éviter de déclencher undo/redo en tapant
        const targetTagName = event.target.tagName.toLowerCase();
        if (targetTagName === 'input' || targetTagName === 'textarea') {
            return;
        }

        if (event.ctrlKey || event.metaKey) { // metaKey pour macOS
            if (event.key === 'z') {
                event.preventDefault(); // Empêche l'action undo native du navigateur
                undo(canvas);
            } else if (event.key === 'y') {
                event.preventDefault(); // Empêche l'action redo native du navigateur
                redo(canvas);
            }
        }
    });

    // --- Écouteurs pour les actions qui NE changent PAS le mode ---
    // (Suppression, Z-Order, Gras/Italique)

    document.getElementById('delete')?.addEventListener('click', () => {
        deleteActiveObject(canvas);
        // Pas besoin de changer de mode ici
    });

    document.getElementById('send-to-back')?.addEventListener('click', () => sendToBack(canvas));
    document.getElementById('bring-to-front')?.addEventListener('click', () => bringToFront(canvas));
    document.getElementById('send-backward')?.addEventListener('click', () => sendBackward(canvas));
    document.getElementById('bring-forward')?.addEventListener('click', () => bringForward(canvas));

    const boldButton = document.getElementById('bold-button');
    const italicButton = document.getElementById('italic-button');

    boldButton?.addEventListener('click', () => toggleTextStyle(canvas, 'fontWeight', 'bold', 'normal', boldButton));
    italicButton?.addEventListener('click', () => toggleTextStyle(canvas, 'fontStyle', 'italic', 'normal', italicButton));

    // --- Écouteurs d'événements du Canvas pour mettre à jour l'UI contextuelle ---

    canvas.on('selection:created', (event) => {
        // console.log("selection:created event fired");
        updateContextualUI(canvas, event.selected ? event.selected[0] : null);
    });

    canvas.on('selection:updated', (event) => {
        // console.log("selection:updated event fired");
        updateContextualUI(canvas, event.selected ? event.selected[0] : null);
    });

    canvas.on('selection:cleared', () => {
        // console.log("selection:cleared event fired");
        updateContextualUI(canvas, null); // Réinitialiser l'UI contextuelle
    });

    // Mettre à jour l'UI après modification d'un objet (ex: redimensionnement)
    canvas.on('object:modified', (event) => {
        // console.log("object:modified event fired");
        if (canvas.getActiveObject() === event.target) {
            updateContextualUI(canvas, event.target);
        }
    });

}); // Fin de DOMContentLoaded

/**
 * Met à jour les éléments UI contextuels (taille/famille de police, couleurs)
 * en fonction de l'objet sélectionné.
 * @param {fabric.Canvas} canvas
 * @param {fabric.Object | null} selectedObject
 */
function updateContextualUI(canvas, selectedObject) {
    // Mettre à jour les sélecteurs de police/taille
    updateFontSizeSelector(canvas);
    updateFontFamilySelector(canvas); // Note: peut être asynchrone

    // Mettre à jour les sélecteurs de couleur
    if (selectedObject) {
        const fill = selectedObject.fill || null;
        const opacity = selectedObject.opacity === undefined ? 1 : selectedObject.opacity;
        const stroke = selectedObject.stroke || null;
        const strokeWidth = selectedObject.strokeWidth === undefined ? 0 : selectedObject.strokeWidth;

        updateFillPickerUI(fill, opacity);
        updateStrokePickerUI(stroke, strokeWidth);

        // Mettre à jour l'état des boutons Gras/Italique si c'est un Textbox
        if (selectedObject.type === 'textbox') {
            const isBold = selectedObject.fontWeight === 'bold';
            const isItalic = selectedObject.fontStyle === 'italic';
            document.getElementById('bold-button')?.classList.toggle('active', isBold);
            document.getElementById('italic-button')?.classList.toggle('active', isItalic);
        } else {
            // Désactiver/Réinitialiser les boutons si l'objet n'est pas un textbox
             document.getElementById('bold-button')?.classList.remove('active');
             document.getElementById('italic-button')?.classList.remove('active');
        }

    } else {
        // Réinitialiser les pickers et boutons si rien n'est sélectionné
        updateFillPickerUI(null, 1); // Ou valeurs par défaut
        updateStrokePickerUI(null, 0); // Ou valeurs par défaut
        document.getElementById('bold-button')?.classList.remove('active');
        document.getElementById('italic-button')?.classList.remove('active');
    }
}

/**
 * Fonction générique pour basculer les styles de texte (gras, italique).
 * @param {fabric.Canvas} canvas
 * @param {'fontWeight' | 'fontStyle'} styleName - La propriété de style à modifier.
 * @param {string} activeValue - La valeur quand le style est actif (ex: 'bold').
 * @param {string} inactiveValue - La valeur quand le style est inactif (ex: 'normal').
 * @param {HTMLElement} buttonElement - Le bouton associé pour mettre à jour son état 'active'.
 */
function toggleTextStyle(canvas, styleName, activeValue, inactiveValue, buttonElement) {
    const activeObject = canvas.getActiveObject();
    // Vérifier si c'est un Textbox
    if (activeObject && activeObject.type === 'textbox') {
        const target = activeObject; // C'est un Textbox
        const isActive = target.get(styleName) === activeValue;
        const newValue = isActive ? inactiveValue : activeValue;

        // Appliquer au texte sélectionné ou à tout le textbox
        if (target.selectionStart !== target.selectionEnd) {
            target.setSelectionStyles({ [styleName]: newValue }, target.selectionStart, target.selectionEnd);
        } else {
            target.set(styleName, newValue);
        }

        // Mettre à jour l'état du bouton
        buttonElement?.classList.toggle('active', !isActive);

        canvas.requestRenderAll();
        saveCanvasState(canvas); // Sauvegarder après modification
    } else {
        // Optionnel: Gérer le cas où l'objet sélectionné n'est pas un Textbox
        // console.log("L'objet sélectionné n'est pas un Textbox.");
    }
}
