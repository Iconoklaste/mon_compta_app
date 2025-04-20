// static/js/whiteboard/brush-manager.js
import { saveCanvasState } from './state.js';
import { updateStrokePickerUI } from './color-picker.js'; // Pour mettre à jour l'UI si on change de pinceau

// Références aux éléments DOM (gardées localement si utilisées uniquement ici)
let freeDrawButtonIcon;
let brushSelectorsContainer;
let strokeColorPreviewIcon; // Pour obtenir la couleur actuelle
let strokeWidthSlider; // Pour obtenir l'épaisseur actuelle
// Référence au slider d'opacité (utilisé pour le marqueur)
let fillTransparencySlider;

let _setModeCallback = null; // Stocker le callback
/**
 * Initialise les sélecteurs de pinceaux et le bouton de dessin libre.
 * @param {fabric.Canvas} canvasInstance - L'instance du canvas Fabric.js.
 * @param {function(import('./mode-manager.js').InteractionMode): void} setModeCallback - Fonction pour changer le mode via le modeManager.
 */
export function initializeBrushSelectors(canvasInstance, setModeCallback) {
    const canvas = canvasInstance; // Renommer pour clarté
    _setModeCallback = setModeCallback;
    const freeDrawButton = document.getElementById('free-draw-button');
    freeDrawButtonIcon = freeDrawButton?.querySelector('.fas'); // Cible l'élément <i> avec la classe fas
    brushSelectorsContainer = document.getElementById('brush-options-dropdown'); // Le conteneur du dropdown
    strokeColorPreviewIcon = document.getElementById('stroke-color-preview-icon');
    strokeWidthSlider = document.getElementById('stroke-width-slider');
    // Récupérer le slider de transparence (utilisé pour le marqueur)
    fillTransparencySlider = document.getElementById('fill-transparency-slider');


    if (!canvas || !freeDrawButton || !brushSelectorsContainer || !strokeColorPreviewIcon || !strokeWidthSlider || !fillTransparencySlider) {
        console.error("Impossible de trouver tous les éléments DOM nécessaires pour le brush manager (y compris fill-transparency-slider).");
        return;
    }

    // Écouteur pour la sélection d'un pinceau dans le dropdown
    brushSelectorsContainer.addEventListener('click', (event) => {
        const target = event.target.closest('.brush-selector'); // Clic sur le bouton ou son contenu
        if (target && target.dataset.brushType) {
            const selectedType = target.dataset.brushType;

            // 1. Configurer le type de pinceau sur le canvas
            setBrushType(canvas, selectedType);

            // 2. Activer le mode dessin via le modeManager (AVEC DÉLAI)
            // --- MODIFICATION START ---
            setTimeout(() => {
                if (_setModeCallback) {
                    _setModeCallback('draw');
                }
            }, 1); // Délai de 1ms
            // --- MODIFICATION END ---

            // 3. Mettre à jour l'état visuel DANS le dropdown
            updateDropdownSelection(target);

            // 4. Mettre à jour l'icône du bouton principal
            updateFreeDrawButtonIcon(selectedType);

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

    // S'assurer que les listeners pour la couleur/largeur/opacité sont actifs
    ensureBrushUpdateListeners(canvas);
}

/**
 * Configure le pinceau de dessin libre sur le canvas.
 * @param {fabric.Canvas} canvas
 * @param {string} brushType - Le type de pinceau (ex: 'pencil', 'crayon', 'fur', 'ink', etc.).
 */
function setBrushType(canvas, brushType) {
    // Vérifier si les pinceaux personnalisés sont chargés (vérifier quelques exemples)
    const customBrushesAvailable = typeof fabric.CrayonBrush !== 'undefined' && typeof fabric.InkBrush !== 'undefined';
    const requiresCustom = ['crayon', 'fur', 'ink', 'longfur', 'marker', 'ribbon', 'shaded', 'sketchy', 'spraypaint', 'squares', 'web'].includes(brushType);

    if (requiresCustom && !customBrushesAvailable) {
        console.error(`Le pinceau personnalisé '${brushType}' n'est pas disponible. Assurez-vous que fabric-brushes.js est chargé correctement.`);
        // Revenir à un pinceau par défaut sûr
        brushType = 'pencil';
        // Optionnel: Mettre à jour l'UI pour refléter ce fallback
        const pencilButton = brushSelectorsContainer.querySelector('[data-brush-type="pencil"]');
        if (pencilButton) updateDropdownSelection(pencilButton);
    }

    // Récupérer la couleur et l'épaisseur actuelles depuis l'UI
    let brushColor = strokeColorPreviewIcon?.style.backgroundColor || 'black';
    const brushWidth = parseInt(strokeWidthSlider?.value, 10) || 1;
    // Récupérer l'opacité actuelle (pour le marqueur)
    const brushOpacity = parseFloat(fillTransparencySlider?.value) || 1;

    // Gérer la couleur transparente (ne pas dessiner en transparent)
    if (brushColor === 'transparent' || brushColor === 'rgba(0, 0, 0, 0)') {
        brushColor = 'black'; // Couleur de secours
        // Optionnel: Mettre à jour l'UI du sélecteur de contour pour refléter ce changement
        // updateStrokePickerUI(brushColor, brushWidth);
    }

    // Options communes pour les pinceaux personnalisés
    const commonOptions = {
        color: brushColor,
        width: brushWidth
    };

    // Configurer les propriétés spécifiques au type de pinceau
    try {
        switch (brushType) {
            // --- Pinceaux Fabric.js standards ---
            case 'pencil': // Pinceau Fabric.js par défaut
                canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
                canvas.freeDrawingBrush.color = brushColor;
                canvas.freeDrawingBrush.width = brushWidth;
                break;
            case 'circle': // Pinceau Cercle Fabric.js standard
                canvas.freeDrawingBrush = new fabric.CircleBrush(canvas);
                canvas.freeDrawingBrush.color = brushColor;
                canvas.freeDrawingBrush.width = brushWidth;
                break;
            case 'spray': // Spray Fabric.js standard
                canvas.freeDrawingBrush = new fabric.SprayBrush(canvas);
                canvas.freeDrawingBrush.color = brushColor;
                canvas.freeDrawingBrush.width = brushWidth * 2; // Le spray dépend de la largeur
                canvas.freeDrawingBrush.density = Math.max(10, brushWidth * 5); // Densité basée sur l'épaisseur
                canvas.freeDrawingBrush.dotWidth = Math.max(1, Math.floor(brushWidth / 2)); // Taille des points
                break;
            // case 'slash': // Si vous aviez un SlashBrush personnalisé
            //     // canvas.freeDrawingBrush = new fabric.SlashBrush(canvas, commonOptions);
            //     // break;

            // --- Pinceaux de fabric-brushes ---
            case 'crayon':
                canvas.freeDrawingBrush = new fabric.CrayonBrush(canvas, commonOptions);
                break;
            case 'fur':
                canvas.freeDrawingBrush = new fabric.FurBrush(canvas, commonOptions);
                break;
            case 'ink':
                canvas.freeDrawingBrush = new fabric.InkBrush(canvas, commonOptions);
                break;
            case 'longfur':
                canvas.freeDrawingBrush = new fabric.LongFurBrush(canvas, commonOptions);
                break;
            case 'marker':
                canvas.freeDrawingBrush = new fabric.MarkerBrush(canvas, {
                    ...commonOptions,
                    opacity: brushOpacity // Utilise l'opacité du slider de remplissage
                });
                break;
            case 'ribbon':
                canvas.freeDrawingBrush = new fabric.RibbonBrush(canvas, commonOptions);
                break;
            case 'shaded':
                canvas.freeDrawingBrush = new fabric.ShadedBrush(canvas, commonOptions);
                break;
            case 'sketchy':
                canvas.freeDrawingBrush = new fabric.SketchyBrush(canvas, commonOptions);
                break;
            case 'spraypaint':
                canvas.freeDrawingBrush = new fabric.SpraypaintBrush(canvas, {
                    ...commonOptions,
                    density: Math.max(5, Math.floor(brushWidth / 2)), // Ajuster selon vos préférences
                    dotWidth: Math.max(1, Math.floor(brushWidth / 3)), // Ajuster
                    dotWidthVariance: Math.max(1, Math.floor(brushWidth / 4)), // Ajuster
                    randomOpacity: true // Optionnel
                });
                break;
            case 'squares':
                canvas.freeDrawingBrush = new fabric.SquaresBrush(canvas, commonOptions);
                break;
            case 'web':
                canvas.freeDrawingBrush = new fabric.WebBrush(canvas, commonOptions);
                break;

            // --- Défaut ---
            default:
                console.warn(`Type de pinceau inconnu: ${brushType}. Utilisation du crayon par défaut.`);
                canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
                canvas.freeDrawingBrush.color = brushColor;
                canvas.freeDrawingBrush.width = brushWidth;
                brushType = 'pencil'; // Corriger le type pour la suite
                // Mettre à jour l'UI pour refléter le fallback
                const pencilButton = brushSelectorsContainer.querySelector('[data-brush-type="pencil"]');
                if (pencilButton) updateDropdownSelection(pencilButton);
                break;
        }
        console.log(`Brush type set to: ${brushType}`);
    } catch (error) {
        console.error(`Erreur lors de l'instanciation du pinceau '${brushType}':`, error);
        console.warn("Retour au pinceau 'pencil' par défaut.");
        // Revenir au pinceau par défaut en cas d'erreur d'instanciation
        canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
        canvas.freeDrawingBrush.color = brushColor;
        canvas.freeDrawingBrush.width = brushWidth;
        brushType = 'pencil';
        const pencilButton = brushSelectorsContainer.querySelector('[data-brush-type="pencil"]');
        if (pencilButton) updateDropdownSelection(pencilButton);
    }

    // Assurer que le mode dessin est actif (peut être redondant si setModeCallback le fait déjà)
    //if (canvas.isDrawingMode === false) {
    //    canvas.isDrawingMode = true;
    //}
}


/**
 * Met à jour l'état visuel (classe .active) des éléments dans le dropdown.
 * @param {HTMLElement} selectedElement - L'élément .brush-selector qui a été cliqué ou doit être activé.
 */
function updateDropdownSelection(selectedElement) {
    if (!brushSelectorsContainer || !selectedElement) return;
    // Retirer la classe 'active' de tous les sélecteurs
    brushSelectorsContainer.querySelectorAll('.brush-selector').forEach(el => {
        el.classList.remove('active');
    });
    // Ajouter la classe 'active' à l'élément sélectionné
    selectedElement.classList.add('active');
}

/**
 * Met à jour l'icône du bouton principal de dessin libre.
 * @param {string} activeBrushType - Le type de pinceau actif.
 */
function updateFreeDrawButtonIcon(activeBrushType) {
    if (!freeDrawButtonIcon) return;

    // Map des types de pinceaux vers les classes Font Awesome
    const iconMap = {
        // Standards
        pencil: 'fa-pencil-alt',
        circle: 'fa-circle',
        spray: 'fa-spray-can-sparkles',
        // slash: 'fa-minus', // Exemple pour slash

        // Custom (fabric-brushes)
        crayon: 'fa-paint-brush',
        fur: 'fa-feather',
        ink: 'fa-pen-fancy',
        longfur: 'fa-feather-alt',
        marker: 'fa-highlighter',
        ribbon: 'fa-ribbon',
        shaded: 'fa-fill-drip',
        sketchy: 'fa-signature',
        spraypaint: 'fa-spray-can',
        squares: 'fa-th-large',
        web: 'fa-spider'
    };

    const iconClass = iconMap[activeBrushType] || 'fa-paint-brush'; // Icône par défaut

    // Supposer que l'icône a une classe de base comme 'fas' et une classe spécifique au type
    // Remplacer toutes les classes fa-* par la nouvelle
    const currentClasses = freeDrawButtonIcon.className.split(' ');
    const newClasses = currentClasses.filter(cls => !cls.startsWith('fa-')); // Garde 'fas', 'me-2', etc.
    newClasses.push(iconClass); // Ajoute la nouvelle icône
    freeDrawButtonIcon.className = newClasses.join(' ');

    // console.log(`Updating main button icon for: ${activeBrushType} to ${iconClass}`);
}

// --- Écouteurs pour mettre à jour le pinceau si couleur/épaisseur/opacité changent PENDANT le mode dessin ---

let isColorListenerAdded = false;
let isWidthListenerAdded = false;
let isOpacityListenerAdded = false; // Pour le marqueur

export function ensureBrushUpdateListeners(canvas) {
     if (!strokeColorPreviewIcon || !strokeWidthSlider || !fillTransparencySlider) return; // Vérifier si les éléments existent

    // --- Couleur ---
    if (!isColorListenerAdded && typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    // Vérifier si on est en mode dessin ET qu'un pinceau est défini
                    if (canvas.isDrawingMode && canvas.freeDrawingBrush) {
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

    // --- Épaisseur ---
    if (!isWidthListenerAdded) {
        strokeWidthSlider.addEventListener('input', (event) => {
             // Vérifier si on est en mode dessin ET qu'un pinceau est défini
             if (canvas.isDrawingMode && canvas.freeDrawingBrush) {
                const newWidth = parseInt(event.target.value, 10) || 1;
                canvas.freeDrawingBrush.width = newWidth;

                // Mettre à jour les propriétés dépendantes pour certains pinceaux
                if (canvas.freeDrawingBrush instanceof fabric.SprayBrush) { // Spray Fabric standard
                     canvas.freeDrawingBrush.density = Math.max(10, newWidth * 5);
                     canvas.freeDrawingBrush.dotWidth = Math.max(1, Math.floor(newWidth / 2));
                } else if (canvas.freeDrawingBrush.constructor.name === 'SpraypaintBrush') { // Spray de fabric-brushes
                    canvas.freeDrawingBrush.density = Math.max(5, Math.floor(newWidth / 2));
                    canvas.freeDrawingBrush.dotWidth = Math.max(1, Math.floor(newWidth / 3));
                    canvas.freeDrawingBrush.dotWidthVariance = Math.max(1, Math.floor(newWidth / 4));
                }
                // Ajouter d'autres ajustements si nécessaire pour d'autres types de pinceaux
                // console.log("Brush width updated while drawing:", newWidth);
            }
        });
        isWidthListenerAdded = true;
    }

    // --- Opacité (pour le MarkerBrush) ---
    if (!isOpacityListenerAdded) {
        fillTransparencySlider.addEventListener('input', (event) => {
            // Vérifier si on est en mode dessin ET que le pinceau est un MarkerBrush
            if (canvas.isDrawingMode && canvas.freeDrawingBrush && canvas.freeDrawingBrush.constructor.name === 'MarkerBrush') {
                const newOpacity = parseFloat(event.target.value) || 1;
                canvas.freeDrawingBrush.opacity = newOpacity;
                // console.log("Marker brush opacity updated while drawing:", newOpacity);
            }
        });
        isOpacityListenerAdded = true;
    }
}
