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
let fillColorPickerButton, fillColorPreviewIcon, fillColorPalette, fillTransparencySlider;
let strokeColorPickerButton, strokeColorPreviewIcon, strokeColorPalette, strokeWidthSlider;
let fillDropdownInstance, strokeDropdownInstance; // Instances Bootstrap Dropdown

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

    strokeColorPickerButton = document.getElementById('stroke-color-picker-button');
    strokeColorPreviewIcon = document.getElementById('stroke-color-preview-icon');
    strokeColorPalette = document.getElementById('stroke-color-palette');
    strokeWidthSlider = document.getElementById('stroke-width-slider');

    if (!fillColorPickerButton || !strokeColorPickerButton) {
        console.error("Impossible de trouver les éléments DOM des sélecteurs de couleur.");
        return;
    }

    // Créer les palettes
    createColorPalette(fillColorPalette, mainColors, 'fill');
    createColorPalette(strokeColorPalette, strokeColors, 'stroke');

    // Ajouter les écouteurs pour les sliders
    fillTransparencySlider.addEventListener('input', handleTransparencyChange);
    strokeWidthSlider.addEventListener('input', handleStrokeWidthChange);

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
    container.innerHTML = ''; // Vider au cas où
    colors.forEach(color => {
        const colorCell = document.createElement('div');
        colorCell.classList.add('color-cell');
        colorCell.style.backgroundColor = color;
        colorCell.dataset.color = color; // Stocke la couleur pour la retrouver facilement

        colorCell.addEventListener('click', () => {
            if (type === 'fill') {
                applyFillColor(color);
                updateFillPickerUI(color, parseFloat(fillTransparencySlider.value)); // Met à jour l'UI interne
            } else {
                applyStrokeColor(color);
                updateStrokePickerUI(color, parseInt(strokeWidthSlider.value, 10)); // Met à jour l'UI interne
            }
            // Gérer la classe 'selected'
            container.querySelectorAll('.color-cell').forEach(cell => cell.classList.remove('selected'));
            colorCell.classList.add('selected');
        });
        container.appendChild(colorCell);
    });
}

// --- Fonctions pour appliquer les changements à l'objet Fabric ---

function applyFillColor(color) {
    if (!fabricCanvas) return;
    const activeObject = fabricCanvas.getActiveObject();
    if (activeObject) {
        activeObject.set('fill', color);
        fabricCanvas.renderAll();
        saveCanvasState(fabricCanvas); // Sauvegarde l'état
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
        activeObject.set('opacity', opacity);
        fabricCanvas.renderAll();
        saveCanvasState(fabricCanvas);
    }
    // Mettre à jour l'aperçu (optionnel, car updateFillPickerUI le fera lors de la sélection)
    // updateFillPickerUI(activeObject?.fill, opacity);
}

function handleStrokeWidthChange(event) {
    if (!fabricCanvas) return;
    const width = parseInt(event.target.value, 10);
    const activeObject = fabricCanvas.getActiveObject();
    if (activeObject) {
         // Ne pas appliquer d'épaisseur si la couleur de contour n'est pas définie (ou est transparente)
         if (activeObject.stroke && activeObject.stroke !== 'transparent') {
            activeObject.set('strokeWidth', width);
            fabricCanvas.renderAll();
            saveCanvasState(fabricCanvas);
         }
    }
    // Mettre à jour l'aperçu (optionnel)
    // updateStrokePickerUI(activeObject?.stroke, width);
}


// --- Fonctions pour mettre à jour l'UI des pickers (appelées depuis main.js) ---

/**
 * Met à jour l'UI du sélecteur de remplissage.
 * @param {string | null} fillColor - La couleur de remplissage (hex, rgba, etc.) ou null.
 * @param {number | null} opacity - L'opacité (0-1) ou null.
 */
export function updateFillPickerUI(fillColor, opacity) {
    if (!fillColorPreviewIcon || !fillTransparencySlider || !fillColorPalette) return;

    const validColor = fillColor || 'transparent'; // Utilise transparent si null/undefined
    const validOpacity = (opacity === null || opacity === undefined) ? 1 : opacity;

    fillColorPreviewIcon.style.backgroundColor = validColor;
    fillTransparencySlider.value = validOpacity;

    // Mettre à jour la cellule sélectionnée
    fillColorPalette.querySelectorAll('.color-cell').forEach(cell => {
        // Comparaison simple pour les couleurs hex de la palette
        // Pour une comparaison robuste (rgba, noms), une lib de couleur serait mieux
        cell.classList.toggle('selected', cell.dataset.color?.toLowerCase() === validColor?.toLowerCase());
    });
}

/**
 * Met à jour l'UI du sélecteur de contour.
 * @param {string | null} strokeColor - La couleur de contour ou null.
 * @param {number | null} strokeWidth - L'épaisseur du contour ou null.
 */
export function updateStrokePickerUI(strokeColor, strokeWidth) {
    if (!strokeColorPreviewIcon || !strokeWidthSlider || !strokeColorPalette) return;

    const validColor = strokeColor || 'transparent';
    const validWidth = (strokeWidth === null || strokeWidth === undefined) ? 0 : strokeWidth;

    strokeColorPreviewIcon.style.backgroundColor = validColor;
    strokeWidthSlider.value = validWidth;

    // Mettre à jour la cellule sélectionnée
    strokeColorPalette.querySelectorAll('.color-cell').forEach(cell => {
        cell.classList.toggle('selected', cell.dataset.color?.toLowerCase() === validColor?.toLowerCase());
    });
}
