// static/js/whiteboard/brush-manager.js
import { saveCanvasState } from './state.js';
import { updateStrokePickerUI } from './color-picker.js'; // Pour mettre à jour l'UI si on change de pinceau

// Références aux éléments DOM (gardées localement si utilisées uniquement ici)
let freeDrawButtonIcon;
let brushSelectorsContainer;
let strokeColorPreviewIcon; // Pour obtenir la couleur actuelle
let strokeWidthSlider; // Pour obtenir l'épaisseur actuelle

/**
 * Initialise les sélecteurs de pinceaux et le bouton de dessin libre.
 * @param {fabric.Canvas} canvasInstance - L'instance du canvas Fabric.js.
 * @param {function(import('./mode-manager.js').InteractionMode): void} setModeCallback - Fonction pour changer le mode via le modeManager.
 */
export function initializeBrushSelectors(canvasInstance, setModeCallback) {
    const canvas = canvasInstance; // Renommer pour clarté
    const freeDrawButton = document.getElementById('free-draw-button');
    freeDrawButtonIcon = freeDrawButton?.querySelector('.text-icon'); // Ou l'élément img/svg
    brushSelectorsContainer = document.getElementById('brush-options-dropdown'); // Le conteneur du dropdown
    strokeColorPreviewIcon = document.getElementById('stroke-color-preview-icon');
    strokeWidthSlider = document.getElementById('stroke-width-slider');


    if (!canvas || !freeDrawButton || !brushSelectorsContainer || !strokeColorPreviewIcon || !strokeWidthSlider) {
        console.error("Impossible de trouver tous les éléments DOM nécessaires pour le brush manager.");
        return;
    }

    // Écouteur pour la sélection d'un pinceau dans le dropdown
    brushSelectorsContainer.addEventListener('click', (event) => {
        const target = event.target.closest('.brush-selector'); // Clic sur le bouton ou son contenu
        if (target && target.dataset.brushType) {
            const selectedType = target.dataset.brushType;

            // 1. Configurer le type de pinceau sur le canvas
            setBrushType(canvas, selectedType);

            // 2. Activer le mode dessin via le modeManager
            setModeCallback('draw'); // Ceci va gérer la désactivation des autres modes et l'UI du bouton principal

            // 3. Mettre à jour l'état visuel DANS le dropdown
            updateDropdownSelection(target);

            // 4. Mettre à jour l'icône du bouton principal (optionnel, si vous voulez montrer le pinceau actif)
            updateFreeDrawButtonIcon(selectedType); // Vous devrez implémenter cette fonction si nécessaire

            // Fermer le dropdown Bootstrap (si nécessaire)
            const dropdownInstance = bootstrap.Dropdown.getInstance(freeDrawButton);
            dropdownInstance?.hide();
        }
    });

    // Initialiser l'état visuel (ex: sélectionner le premier pinceau par défaut)
    const defaultBrush = brushSelectorsContainer.querySelector('.brush-selector');
    if (defaultBrush) {
        updateDropdownSelection(defaultBrush);
        setBrushType(canvas, defaultBrush.dataset.brushType); // Appliquer le pinceau par défaut
        updateFreeDrawButtonIcon(defaultBrush.dataset.brushType);
    }
}

/**
 * Configure le pinceau de dessin libre sur le canvas.
 * @param {fabric.Canvas} canvas
 * @param {string} brushType - Le type de pinceau ('pencil', 'marker', 'spray', etc.).
 */
function setBrushType(canvas, brushType) {
    if (!canvas.freeDrawingBrush) return;

    // Récupérer la couleur et l'épaisseur actuelles depuis l'UI
    let brushColor = strokeColorPreviewIcon?.style.backgroundColor || 'black';
    const brushWidth = parseInt(strokeWidthSlider?.value, 10) || 1;

    // Gérer la couleur transparente (ne pas dessiner en transparent)
    if (brushColor === 'transparent' || brushColor === 'rgba(0, 0, 0, 0)') {
        brushColor = 'black'; // Couleur de secours
        // Optionnel: Mettre à jour l'UI du sélecteur de contour pour refléter ce changement
        // updateStrokePickerUI(brushColor, brushWidth);
    }

    // Appliquer couleur et épaisseur communes
    canvas.freeDrawingBrush.color = brushColor;
    canvas.freeDrawingBrush.width = brushWidth;

    // Configurer les propriétés spécifiques au type de pinceau
    switch (brushType) {
        case 'pencil':
            // Le pinceau par défaut de Fabric est souvent de type crayon
            canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
            // Réappliquer couleur/épaisseur car on a créé une nouvelle instance
            canvas.freeDrawingBrush.color = brushColor;
            canvas.freeDrawingBrush.width = brushWidth;
            // Autres options spécifiques au crayon si nécessaire
            // canvas.freeDrawingBrush.shadow = null;
            break;
        case 'marker': // Exemple: un pinceau plus épais ou avec une forme différente
             // Pour un marqueur simple, on peut juste augmenter l'épaisseur par défaut
             // ou utiliser un autre type de pinceau si disponible/créé.
             // Ici, on utilise PencilBrush mais on pourrait vouloir un CircleBrush ou SprayBrush.
            canvas.freeDrawingBrush = new fabric.PencilBrush(canvas); // Ou autre type
            canvas.freeDrawingBrush.color = brushColor;
            canvas.freeDrawingBrush.width = Math.max(5, brushWidth); // Épaisseur minimale pour marqueur
            // canvas.freeDrawingBrush.strokeLineCap = 'round'; // Extrémités arrondies
            break;
        case 'spray':
            canvas.freeDrawingBrush = new fabric.SprayBrush(canvas);
            canvas.freeDrawingBrush.width = brushWidth * 2; // Le spray dépend de la largeur
            canvas.freeDrawingBrush.density = Math.max(10, brushWidth * 5); // Densité basée sur l'épaisseur
            canvas.freeDrawingBrush.dotWidth = Math.max(1, Math.floor(brushWidth / 2)); // Taille des points
            canvas.freeDrawingBrush.color = brushColor;
            // canvas.freeDrawingBrush.shadow = null;
            break;
        // Ajoutez d'autres types de pinceaux ici
        default:
            console.warn(`Type de pinceau inconnu: ${brushType}`);
            // Revenir au pinceau par défaut (crayon)
            canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
            canvas.freeDrawingBrush.color = brushColor;
            canvas.freeDrawingBrush.width = brushWidth;
            break;
    }
    console.log(`Brush type set to: ${brushType}`);
}

/**
 * Met à jour l'état visuel (classe .active) des éléments dans le dropdown.
 * @param {HTMLElement} selectedElement - L'élément .brush-selector qui a été cliqué.
 */
function updateDropdownSelection(selectedElement) {
    if (!brushSelectorsContainer) return;
    // Retirer la classe 'active' de tous les sélecteurs
    brushSelectorsContainer.querySelectorAll('.brush-selector').forEach(el => {
        el.classList.remove('active');
        // Réinitialiser les styles spécifiques si nécessaire (mieux géré par CSS)
        // el.style.backgroundColor = '';
    });
    // Ajouter la classe 'active' à l'élément sélectionné
    selectedElement.classList.add('active');
    // Appliquer des styles spécifiques si nécessaire (mieux géré par CSS)
    // selectedElement.style.backgroundColor = '#e0e0e0';
}

/**
 * Met à jour l'icône du bouton principal de dessin libre (optionnel).
 * @param {string} activeBrushType - Le type de pinceau actif.
 */
function updateFreeDrawButtonIcon(activeBrushType) {
    if (!freeDrawButtonIcon) return;
    // Logique pour changer la source de l'icône ou son style
    // Exemple simple: changer le contenu textuel si c'est un bouton texte
    // Ou changer la source si c'est une image/svg
    // freeDrawButtonIcon.src = `/path/to/icon/${activeBrushType}.svg`;
    // console.log(`Updating main button icon for: ${activeBrushType}`);
}

// --- Écouteurs pour mettre à jour le pinceau si couleur/épaisseur changent PENDANT le mode dessin ---
// Ces écouteurs sont ajoutés une fois dans initializeColorPickers ou ici

let isColorListenerAdded = false;
let isWidthListenerAdded = false;

export function ensureBrushUpdateListeners(canvas) {
     if (!strokeColorPreviewIcon || !strokeWidthSlider) return; // Vérifier si les éléments existent

    // Écouteur pour le changement de couleur de contour (depuis color-picker)
    // On utilise un MutationObserver car la couleur est changée via style.backgroundColor
    if (!isColorListenerAdded && typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    if (canvas.isDrawingMode) { // Mettre à jour seulement si en mode dessin
                        let newColor = strokeColorPreviewIcon.style.backgroundColor || 'black';
                        if (newColor === 'transparent' || newColor === 'rgba(0, 0, 0, 0)') {
                            newColor = 'black'; // Fallback
                        }
                        canvas.freeDrawingBrush.color = newColor;
                        // console.log("Brush color updated while drawing:", newColor);
                    }
                }
            });
        });
        observer.observe(strokeColorPreviewIcon, { attributes: true });
        isColorListenerAdded = true;
    }

    // Écouteur pour le changement d'épaisseur de contour
    if (!isWidthListenerAdded) {
        strokeWidthSlider.addEventListener('input', (event) => {
             if (canvas.isDrawingMode) { // Mettre à jour seulement si en mode dessin
                const newWidth = parseInt(event.target.value, 10) || 1;
                canvas.freeDrawingBrush.width = newWidth;
                // Pour certains pinceaux (Spray), d'autres propriétés peuvent dépendre de la largeur
                if (canvas.freeDrawingBrush instanceof fabric.SprayBrush) {
                     canvas.freeDrawingBrush.density = Math.max(10, newWidth * 5);
                     canvas.freeDrawingBrush.dotWidth = Math.max(1, Math.floor(newWidth / 2));
                }
                // console.log("Brush width updated while drawing:", newWidth);
            }
        });
        isWidthListenerAdded = true;
    }
}

// Appeler ensureBrushUpdateListeners après l'initialisation des color pickers
// dans main.js ou à la fin de initializeBrushSelectors.
// Exemple d'appel à la fin de initializeBrushSelectors:
// export function initializeBrushSelectors(...) {
//    ...
//    ensureBrushUpdateListeners(canvas); // Ajouter les listeners
// }
// Ou appeler explicitement depuis main.js après initializeColorPickers et initializeBrushSelectors.
