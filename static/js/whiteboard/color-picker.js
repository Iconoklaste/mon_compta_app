// static/js/whiteboard/color-picker.js
import { saveCanvasState } from './state.js'; // Import pour sauvegarder après modification

// Définissez vos jeux de couleurs ici ou importez-les si définis ailleurs
const mainColors = [
    "#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3",
    "#800000", "#808000", "#008000", "#000080", "#800080", "#008080", "#C0C0C0",
    "#808080", "#FFFFFF", "#000000", "#FFA500", "#00FFFF", "#FF00FF", "#FFC0CB",
    "#ADD8E6", "#90EE90", "#F0E68C", "#E6E6FA", "#D3D3D3", "#A9A9A9", "#778899",
    "#B0C4DE", "#696969", "#F0F8FF", "#FAEBD7", "#008B8B", "#00CED1", "#4682B4",
    "#00008B", "#191970", "#8B008B", "#8B4513", "#2F4F4F", "#228B22", "#006400",
    "#BDB76B", "#556B2F", "#8FBC8F", "#6B8E23", "#DAA520", "#D2691E", "#CD853F",
    "#DEB887"
];
const strokeColors = ['#000000', '#808080', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#FFA500', '#800080']; // Couleurs de contour exemple

let fabricCanvas = null; // Référence au canvas Fabric.js

// --- Références aux éléments DOM ---
let fillColorPickerButton, fillColorPreviewIcon, fillColorPalette, fillTransparencySlider, fillNoColorButton;
let strokeColorPickerButton, strokeColorPreviewIcon, strokeColorPalette, strokeWidthSlider;
export let fillDropdownInstance, strokeDropdownInstance; // Instances Bootstrap Dropdown

/**
 * Initialise le module color-picker.
 * @param {fabric.Canvas} canvasInstance - L'instance du canvas Fabric.js.
 */
export function initializeColorPickers(canvasInstance) {
    fabricCanvas = canvasInstance; // Stocke la référence au canvas

    // Récupérer les éléments DOM après le chargement du DOM
    fillColorPickerButton = document.getElementById('fill-color-picker-button');
    fillColorPreviewIcon = document.getElementById('fill-color-preview-icon');
    fillColorPalette = document.getElementById('fill-color-palette');
    fillTransparencySlider = document.getElementById('fill-transparency-slider');
    fillNoColorButton = document.getElementById('fill-no-color-button');

    strokeColorPickerButton = document.getElementById('stroke-color-picker-button');
    strokeColorPreviewIcon = document.getElementById('stroke-color-preview-icon');
    strokeColorPalette = document.getElementById('stroke-color-palette');
    strokeWidthSlider = document.getElementById('stroke-width-slider');

    // Vérification plus robuste des éléments essentiels
    if (!fillColorPickerButton || !strokeColorPickerButton || !fillColorPalette || !strokeColorPalette || !fillNoColorButton) {
        console.error("Impossible de trouver tous les éléments DOM nécessaires pour les sélecteurs de couleur.");
        return;
    }

    // Créer les palettes
    createColorPalette(fillColorPalette, mainColors, 'fill');
    createColorPalette(strokeColorPalette, strokeColors, 'stroke');

    // Ajouter les écouteurs pour les sliders
    fillTransparencySlider.addEventListener('input', handleTransparencyChange);
    strokeWidthSlider.addEventListener('input', handleStrokeWidthChange);

    // Ajouter l'écouteur pour le bouton "Aucune Couleur"
    fillNoColorButton.addEventListener('click', handleNoFillColor);

    const defaultFillColor = 'black';
    const defaultFillOpacity = 1;
    const defaultStrokeColor = 'black';
    const defaultStrokeWidth = 1;

    // Appliquer l'état initial à l'UI des pickers
    updateFillPickerUI(defaultFillColor, defaultFillOpacity);
    updateStrokePickerUI(defaultStrokeColor, defaultStrokeWidth);
    // Assurer que les valeurs des sliders sont aussi mises à jour (si updateUI ne le fait pas déjà)
    if (fillTransparencySlider) fillTransparencySlider.value = defaultFillOpacity;
    if (strokeWidthSlider) strokeWidthSlider.value = defaultStrokeWidth;

    // Gérer la fermeture des dropdowns Bootstrap
    fillDropdownInstance = bootstrap.Dropdown.getOrCreateInstance(fillColorPickerButton);
    strokeDropdownInstance = bootstrap.Dropdown.getOrCreateInstance(strokeColorPickerButton);

    fillColorPickerButton.addEventListener('show.bs.dropdown', () => {
        strokeDropdownInstance.hide(); // Ferme l'autre dropdown
    });

    strokeColorPickerButton.addEventListener('show.bs.dropdown', () => {
        fillDropdownInstance.hide(); // Ferme l'autre dropdown
    });
}

/**
 * Crée dynamiquement une palette de couleurs.
 * @param {HTMLElement} container - L'élément conteneur pour la palette.
 * @param {string[]} colors - Le tableau de couleurs hexadécimales.
 * @param {'fill' | 'stroke'} type - Le type de couleur (remplissage ou contour).
 */
function createColorPalette(container, colors, type) {
    container.innerHTML = '';
    colors.forEach(color => {
        const colorCell = document.createElement('div');
        colorCell.classList.add('color-cell');
        colorCell.style.backgroundColor = color;
        colorCell.dataset.color = color;

        colorCell.addEventListener('click', () => {
            // Désélectionner le bouton "Aucune couleur" si une couleur est choisie
            if (type === 'fill' && fillNoColorButton) {
                 fillNoColorButton.classList.remove('active'); // Optionnel: style visuel pour le bouton "Aucune couleur"
            }

            if (type === 'fill') {
                applyFillColor(color);
                updateFillPickerUI(color, parseFloat(fillTransparencySlider.value));
                // Activer le slider de transparence quand une couleur est sélectionnée
                if (fillTransparencySlider) fillTransparencySlider.disabled = false;
            } else { // type === 'stroke'
                applyStrokeColor(color);
                updateStrokePickerUI(color, parseInt(strokeWidthSlider.value, 10));

                if (fabricCanvas && fabricCanvas.isDrawingMode) {
                    let brushColor = (color === 'transparent') ? 'black' : color; // Utilise noir si transparent
                    fabricCanvas.freeDrawingBrush.color = brushColor;
                }
            }
            // Gérer la classe 'selected' pour les cellules de couleur
            container.querySelectorAll('.color-cell').forEach(cell => cell.classList.remove('selected'));
            colorCell.classList.add('selected');
        });
        container.appendChild(colorCell);
    });
}

// --- Gestionnaire pour "Aucune Couleur" ---
function handleNoFillColor() {
    applyFillColor(null); // Appliquer 'null' pour enlever le remplissage
    updateFillPickerUI(null, 1); // Mettre à jour l'UI pour refléter l'absence de couleur
    // Désélectionner toutes les cellules de couleur
    fillColorPalette.querySelectorAll('.color-cell').forEach(cell => cell.classList.remove('selected'));
    // Optionnel: Ajouter une classe 'active' au bouton "Aucune couleur"
    if (fillNoColorButton) fillNoColorButton.classList.add('active');
    // Désactiver le slider de transparence
    if (fillTransparencySlider) fillTransparencySlider.disabled = true;
}

// --- Fonctions pour appliquer les changements à l'objet Fabric ---
function applyFillColor(color) { // color peut être une string ou null
    if (!fabricCanvas) return;
    const activeObject = fabricCanvas.getActiveObject();
    if (activeObject) {
        // Fabric.js utilise null ou '' pour signifier "pas de remplissage"
        activeObject.set('fill', color);
        // Si la couleur est null, l'opacité n'a plus de sens visuel direct sur le remplissage
        // On pourrait la réinitialiser ou la laisser telle quelle pour une éventuelle recoloration.
        // Laisser l'opacité telle quelle est souvent moins surprenant pour l'utilisateur.
        // if (color === null) {
        //     activeObject.set('opacity', 1); // Optionnel: réinitialiser l'opacité
        // }
        fabricCanvas.renderAll();
        saveCanvasState(fabricCanvas);
    }
}


function applyStrokeColor(color) {
    if (!fabricCanvas) return;
    const activeObject = fabricCanvas.getActiveObject();
    if (activeObject) {
        // Ne pas appliquer de contour aux types 'textbox' par défaut, sauf si déjà présent
        if (activeObject.type !== 'textbox' || activeObject.stroke) {
             activeObject.set('stroke', color);
             // Si on ajoute un contour pour la première fois, définir une épaisseur par défaut si elle est nulle
             if (activeObject.strokeWidth === null || activeObject.strokeWidth === 0) {
                 const defaultStrokeWidth = 1;
                 activeObject.set('strokeWidth', defaultStrokeWidth);
                 // Mettre à jour le slider de l'UI aussi
                 if (strokeWidthSlider) strokeWidthSlider.value = defaultStrokeWidth;
             }
            // Si on rend le contour transparent, mettre l'épaisseur à 0 visuellement peut être cohérent
             if (color === 'transparent' || color === null) {
                 // Optionnel: Mettre strokeWidth à 0 ou le laisser ? Laisser peut être mieux si l'utilisateur remet une couleur.
                 // activeObject.set('strokeWidth', 0);
                 // if (strokeWidthSlider) strokeWidthSlider.value = 0;
             }
             fabricCanvas.renderAll();
             saveCanvasState(fabricCanvas);
        }
    }
}

function handleTransparencyChange(event) {
    if (!fabricCanvas) return;
    const opacity = parseFloat(event.target.value);
    const activeObject = fabricCanvas.getActiveObject();
    if (activeObject) {
        // Ne pas appliquer l'opacité si le remplissage est null (transparent)
        if (activeObject.fill !== null && activeObject.fill !== 'transparent') {
            activeObject.set('opacity', opacity);
            fabricCanvas.renderAll();
            saveCanvasState(fabricCanvas);
        }
    }
}


function handleStrokeWidthChange(event) {
    // ... (fonction inchangée, mais la logique de sauvegarde est déjà correcte) ...
    if (!fabricCanvas) return;
    const width = parseInt(event.target.value, 10);
    const activeObject = fabricCanvas.getActiveObject();
    let stateChanged = false; // Pour suivre si une sauvegarde est nécessaire

    if (activeObject) {
         if (activeObject.stroke && activeObject.stroke !== 'transparent') {
            activeObject.set('strokeWidth', width);
            // fabricCanvas.renderAll(); // Fait plus bas
            stateChanged = true;
         }
    }

    if (fabricCanvas.isDrawingMode) {
        fabricCanvas.freeDrawingBrush.width = width || 1;
        stateChanged = true; // Le changement du pinceau justifie une sauvegarde
    }

    if (stateChanged) {
        fabricCanvas.renderAll();
        saveCanvasState(fabricCanvas);
   }
}


// --- Fonctions pour mettre à jour l'UI des pickers (appelées depuis main.js) ---

/**
 * Met à jour l'UI du sélecteur de remplissage.
 * @param {string | null} fillColor - La couleur de remplissage (hex, rgba, etc.) ou null.
 * @param {number | null} opacity - L'opacité (0-1) ou null.
 */
export function updateFillPickerUI(fillColor, opacity) {
    if (!fillColorPreviewIcon || !fillTransparencySlider || !fillColorPalette || !fillNoColorButton) return;

    const isFillTransparent = (fillColor === null || fillColor === 'transparent');
    const validColor = isFillTransparent ? 'transparent' : fillColor;
    const validOpacity = (opacity === null || opacity === undefined) ? 1 : opacity;

    // Mettre à jour l'aperçu : utiliser une icône spéciale si transparent ?
    // Pour l'instant, on met juste le fond transparent.
    // On pourrait ajouter une classe CSS pour afficher une icône "pas de couleur".
    fillColorPreviewIcon.style.backgroundColor = validColor;
    fillColorPreviewIcon.classList.toggle('no-color-preview', isFillTransparent); // Ajout d'une classe pour style CSS optionnel

    fillTransparencySlider.value = validOpacity;
    // Désactiver le slider si pas de couleur
    fillTransparencySlider.disabled = isFillTransparent;

    // Gérer la sélection dans la palette et le bouton "Aucune Couleur"
    fillColorPalette.querySelectorAll('.color-cell').forEach(cell => {
        cell.classList.toggle('selected', !isFillTransparent && cell.dataset.color?.toLowerCase() === validColor?.toLowerCase());
    });
    fillNoColorButton.classList.toggle('active', isFillTransparent); // Marquer le bouton "Aucune couleur" comme actif
}

/**
 * Met à jour l'UI du sélecteur de contour.
 * @param {string | null} strokeColor - La couleur de contour ou null.
 * @param {number | null} strokeWidth - L'épaisseur du contour ou null.
 */
export function updateStrokePickerUI(strokeColor, strokeWidth) {
    // ... (fonction inchangée, mais on pourrait ajouter une logique similaire pour un bouton "Aucun contour") ...
    if (!strokeColorPreviewIcon || !strokeWidthSlider || !strokeColorPalette) return;

    const isStrokeTransparent = (strokeColor === null || strokeColor === 'transparent');
    const validColor = isStrokeTransparent ? 'transparent' : strokeColor;
    const validWidth = (strokeWidth === null || strokeWidth === undefined) ? 0 : strokeWidth;

    strokeColorPreviewIcon.style.backgroundColor = validColor;
    strokeColorPreviewIcon.classList.toggle('no-color-preview', isStrokeTransparent); // Style CSS optionnel

    strokeWidthSlider.value = validWidth;
    // On pourrait désactiver le slider d'épaisseur si pas de couleur de contour
    // strokeWidthSlider.disabled = isStrokeTransparent;

    strokeColorPalette.querySelectorAll('.color-cell').forEach(cell => {
        cell.classList.toggle('selected', !isStrokeTransparent && cell.dataset.color?.toLowerCase() === validColor?.toLowerCase());
    });
    // Si on avait un bouton "Aucun contour", on le mettrait à jour ici.
}
