// static/js/whiteboard/toolbar.js
import { saveCanvasState } from './state.js';
import { deleteActiveObject } from './controls.js'; // <-- Importe depuis controls.js
import { sendToBack, bringToFront, sendBackward, bringForward } from './objects.js'; // Garde les autres depuis objects.js
import { fillDropdownInstance, strokeDropdownInstance } from './color-picker.js';

let toolbarElement;
let canvasInstance;
let currentTarget = null; // L'objet Fabric actuellement ciblé par la barre d'outils

// Références aux éléments de la barre d'outils
let duplicateButton, deleteButton, bringForwardButton, sendBackwardButton;
let textSection, fontFamilySelect, fontSizeInput, boldButton, italicButton;
let shapeSection; // Ajoutez d'autres sections si nécessaire
let openFillPickerButton, fillPreviewSwatch;
let openStrokePickerButton, strokePreviewSwatch;

/**
 * Initialise la barre d'outils et attache les écouteurs aux boutons.
 * @param {fabric.Canvas} canvas
 */
export function initializeToolbar(canvas) {
    console.log("[Toolbar] Initializing...");
    canvasInstance = canvas;
    toolbarElement = document.getElementById('object-toolbar');
    console.log("[Toolbar] Toolbar element found:", toolbarElement);

    if (!toolbarElement) {
        console.error("L'élément HTML de la barre d'outils (id='object-toolbar') est introuvable.");
        return;
    }

    // Récupérer les boutons/sections
    duplicateButton = document.getElementById('toolbar-duplicate');
    deleteButton = document.getElementById('toolbar-delete');
    console.log("[Toolbar] Delete button found:", deleteButton);
    bringForwardButton = document.getElementById('toolbar-bring-forward');
    sendBackwardButton = document.getElementById('toolbar-send-backward');
    // ... récupérer bringToFront, sendToBack ...

    textSection = toolbarElement.querySelector('.toolbar-text');
    fontFamilySelect = document.getElementById('toolbar-font-family');
    fontSizeInput = document.getElementById('toolbar-font-size');
    boldButton = document.getElementById('toolbar-bold');
    italicButton = document.getElementById('toolbar-italic');

    shapeSection = toolbarElement.querySelector('.toolbar-shape');
    openFillPickerButton = document.getElementById('toolbar-open-fill-picker');
    fillPreviewSwatch = document.getElementById('toolbar-fill-preview');
    openStrokePickerButton = document.getElementById('toolbar-open-stroke-picker');
    strokePreviewSwatch = document.getElementById('toolbar-stroke-preview');

    // Ajouter les écouteurs aux boutons de la barre d'outils
    deleteButton?.addEventListener('click', handleDelete);
    duplicateButton?.addEventListener('click', handleDuplicate);
    bringForwardButton?.addEventListener('click', () => bringForward(canvasInstance));
    sendBackwardButton?.addEventListener('click', () => sendBackward(canvasInstance));
    // ... ajouter listeners pour bringToFront, sendToBack ...

    // Listeners spécifiques au texte
    fontFamilySelect?.addEventListener('change', handleFontFamilyChange);
    fontSizeInput?.addEventListener('change', handleFontSizeChange);
    fontSizeInput?.addEventListener('input', handleFontSizeChange); // Pour mise à jour en temps réel
    boldButton?.addEventListener('click', handleBold);
    italicButton?.addEventListener('click', handleItalic);

    // --- AJOUT : Écouteurs pour les boutons de couleur ---
    openFillPickerButton?.addEventListener('click', (event) => {
        event.stopPropagation(); // Empêche le clic de se propager (utile pour la fermeture)
        if (!fillDropdownInstance) return;
        const buttonElement = event.currentTarget; // Le bouton cliqué dans la toolbar

        // Fermer l'autre dropdown d'abord
        strokeDropdownInstance?.hide();

        // Mettre à jour la référence pour Popper.js (utilisé par Bootstrap)
        // avant d'afficher/basculer
        fillDropdownInstance._config.reference = buttonElement;
        fillDropdownInstance.update(); // Demander à Popper de recalculer la position

        // Afficher/Masquer le dropdown
        fillDropdownInstance.toggle();
    })

    openStrokePickerButton?.addEventListener('click', (event) => {
        event.stopPropagation(); // Empêche le clic de se propager
        if (!strokeDropdownInstance) return;
        const buttonElement = event.currentTarget; // Le bouton cliqué dans la toolbar

        // Fermer l'autre dropdown d'abord
        fillDropdownInstance?.hide();

        // Mettre à jour la référence pour Popper.js
        strokeDropdownInstance._config.reference = buttonElement;
        strokeDropdownInstance.update(); // Recalculer la position

        // Afficher/Masquer le dropdown
        strokeDropdownInstance.toggle();
    });

    canvasInstance.on('mouse:down', handleCanvasMouseDown);
    console.log("[Toolbar] handleCanvasMouseDown listener attached to canvas.");

    // --- AJOUT : Écouteur sur le document pour fermer les dropdowns ---
    // Si on clique en dehors de la toolbar ET en dehors d'un dropdown ouvert
    document.addEventListener('click', handleDocumentClickForDropdowns, true); // Phase de capture

    console.log("[Toolbar] Initialization finished.");
}

/**
 * Gère le clic sur le bouton Supprimer.
 */
function handleDelete() {
    if (currentTarget && canvasInstance) {
        // Utilise la fonction existante si elle fait ce qu'il faut
        deleteActiveObject(canvasInstance); // Assure que l'objet actif est bien celui ciblé
        hideToolbar(); // Cacher après suppression
    }
}

/**
 * Gère le clic sur le bouton Dupliquer.
 */
function handleDuplicate() {
    if (!currentTarget || !canvasInstance) return;

    currentTarget.clone((cloned) => {
        cloned.set({
            left: cloned.left + 20,
            top: cloned.top + 20,
            evented: true,
        });
        canvasInstance.add(cloned);
        canvasInstance.requestRenderAll();
        saveCanvasState(canvasInstance);
    });
}

// --- Fonctions de gestion du texte ---
// ... (handleFontFamilyChange, handleFontSizeChange, handleBold, handleItalic, applyTextStyle inchangés) ...
async function handleFontFamilyChange(event) {
    if (!currentTarget || currentTarget.type !== 'textbox') return;
    const newFont = event.target.value;
    try {
        if (!document.fonts.check(`12px ${newFont}`)) {
            await document.fonts.load(`12px ${newFont}`);
        }
        applyTextStyle({ fontFamily: newFont });
    } catch (error) {
        console.error(`Erreur chargement police ${newFont}:`, error);
    }
}

function handleFontSizeChange(event) {
    if (!currentTarget || currentTarget.type !== 'textbox') return;
    const newSize = parseInt(event.target.value, 10);
    if (!isNaN(newSize) && newSize > 0) {
        applyTextStyle({ fontSize: newSize });
    }
}

function handleBold() {
    if (!currentTarget || currentTarget.type !== 'textbox') return;
    const isBold = currentTarget.fontWeight === 'bold';
    applyTextStyle({ fontWeight: isBold ? 'normal' : 'bold' });
    boldButton?.classList.toggle('active', !isBold);
}

function handleItalic() {
    if (!currentTarget || currentTarget.type !== 'textbox') return;
    const isItalic = currentTarget.fontStyle === 'italic';
    applyTextStyle({ fontStyle: isItalic ? 'normal' : 'italic' });
    italicButton?.classList.toggle('active', !isItalic);
}

function applyTextStyle(style) {
    if (!currentTarget || currentTarget.type !== 'textbox' || !canvasInstance) return;
    const target = currentTarget;

    if (target.selectionStart !== target.selectionEnd) {
        target.setSelectionStyles(style, target.selectionStart, target.selectionEnd);
    } else {
        target.set(style);
    }
    canvasInstance.requestRenderAll();
    saveCanvasState(canvasInstance);
}


// --- Affichage / Masquage / Positionnement ---

/**
 * Affiche et positionne la barre d'outils près de l'objet sélectionné.
 * @param {fabric.Object} target - L'objet sélectionné.
 */
export function showToolbar(target) {
    console.log("[Toolbar] showToolbar called for target:", target);
    if (!toolbarElement || !canvasInstance) {
        console.error("[Toolbar] showToolbar aborted: toolbarElement or canvasInstance missing.");
        return;
    }
    currentTarget = target; // Mémoriser la cible actuelle

    updateToolbarContent(target); // Mettre à jour le contenu AVANT d'afficher
    toolbarElement.style.display = 'flex'; // Afficher la barre d'outils
    updateToolbarPosition(target); // Positionner

    console.log("[Toolbar] Attaching object listeners (moving, scaling, etc.).");

    // Ajouter les écouteurs pour suivre l'objet
    canvasInstance.on('object:moving', handleObjectMove);
    canvasInstance.on('object:scaling', handleObjectMove);
    canvasInstance.on('object:rotating', handleObjectMove);
    canvasInstance.on('object:modified', handleObjectModified);
    canvasInstance.on('mouse:wheel', handleZoom);
}

/**
 * Cache la barre d'outils et détache les écouteurs.
 */
export function hideToolbar() {
    console.log("[Toolbar] hideToolbar called.");
    if (!toolbarElement || !canvasInstance) return;

    if (toolbarElement.style.display !== 'none') {
        toolbarElement.style.display = 'none';
        currentTarget = null;

        console.log("[Toolbar] Detaching object listeners.");
        canvasInstance.off('object:moving', handleObjectMove);
        canvasInstance.off('object:scaling', handleObjectMove);
        canvasInstance.off('object:rotating', handleObjectMove);
        canvasInstance.off('object:modified', handleObjectModified);
        canvasInstance.off('mouse:wheel', handleZoom);
    } else {
        console.log("[Toolbar] hideToolbar called, but already hidden.");
    }
}

/**
 * Met à jour la position de la barre d'outils en fonction de l'objet.
 * @param {fabric.Object} target - L'objet cible.
 */
function updateToolbarPosition(target) {
    // ... (code inchangé) ...
    if (!target || !toolbarElement || !canvasInstance) return;

    const canvasRect = canvasInstance.getElement().getBoundingClientRect();
    const zoom = canvasInstance.getZoom();
    const viewportMatrix = canvasInstance.viewportTransform;

    target.setCoords();
    const objCoords = target.oCoords;

    if (!objCoords) return;

    const objectPoint = new fabric.Point(objCoords.tr.x, objCoords.tr.y);
    const screenPoint = fabric.util.transformPoint(objectPoint, viewportMatrix);

    const toolbarHeight = toolbarElement.offsetHeight;
    const toolbarWidth = toolbarElement.offsetWidth;
    let top = screenPoint.y - toolbarHeight - 10;
    let left = screenPoint.x + 10;

    top = Math.max(5, top);
    left = Math.max(5, left);
    if (left + toolbarWidth > window.innerWidth - 10) {
        left = window.innerWidth - toolbarWidth - 10;
    }

    toolbarElement.style.left = `${left}px`;
    toolbarElement.style.top = `${top}px`;
}


/**
 * Met à jour le contenu de la barre d'outils en fonction du type d'objet.
 * @param {fabric.Object} target - L'objet cible.
 */
function updateToolbarContent(target) {

    if (!target || !toolbarElement) return; // Vérifier toolbarElement aussi

    // Cacher/afficher sections spécifiques (inchangé)
    textSection = toolbarElement.querySelector('.toolbar-text'); // Re-sélectionner au cas où
    shapeSection = toolbarElement.querySelector('.toolbar-shape');
    fillPreviewSwatch = document.getElementById('toolbar-fill-preview'); // Re-sélectionner
    strokePreviewSwatch = document.getElementById('toolbar-stroke-preview'); // Re-sélectionner

    if (!textSection || !shapeSection || !fillPreviewSwatch || !strokePreviewSwatch) {
        console.warn("[Toolbar] Missing sections or swatches in updateToolbarContent");
        return;
    }

    textSection.style.display = 'none';
    shapeSection.style.display = 'none';
    

    if (target.type === 'textbox') {
        textSection.style.display = 'flex';
        fontFamilySelect.value = target.fontFamily || 'Arial';
        fontSizeInput.value = target.fontSize || 20;
        boldButton?.classList.toggle('active', target.fontWeight === 'bold');
        italicButton?.classList.toggle('active', target.fontStyle === 'italic');
    } else if (target.type === 'rect' || target.type === 'circle' || target.type === 'triangle' || target.type === 'polygon' || target.type === 'image') {
        shapeSection.style.display = 'flex';
    }
    // Ajouter d'autres types si nécessaire (ex: 'path' pour le dessin libre)
    else if (target.type === 'path') {
         shapeSection.style.display = 'flex'; // Les tracés ont souvent un contour
    }

    // Mettre à jour les aperçus de couleur (si la section shape est visible)
    if (shapeSection.style.display === 'flex') {
        // Remplissage
        const fill = target.fill || null;
        const isFillTransparent = (fill === null || fill === 'transparent' || fill === '');
        fillPreviewSwatch.style.backgroundColor = isFillTransparent ? 'transparent' : fill;
        fillPreviewSwatch.classList.toggle('no-color-preview', isFillTransparent);

        // Contour
        const stroke = target.stroke || null;
        const strokeWidth = target.strokeWidth || 0;
        // Considérer le contour comme transparent s'il n'y a pas de couleur OU si l'épaisseur est nulle
        const isStrokeTransparent = (stroke === null || stroke === 'transparent' || stroke === '' || strokeWidth <= 0);
        strokePreviewSwatch.style.backgroundColor = isStrokeTransparent ? 'transparent' : stroke;
        strokePreviewSwatch.classList.toggle('no-color-preview', isStrokeTransparent);
    }
}

// --- Gestionnaires d'événements Fabric pour maintenir la barre d'outils ---

function handleObjectMove(options) {
    if (options.target === currentTarget) {
        updateToolbarPosition(options.target);
    }
}

function handleObjectModified(options) {
     if (options.target === currentTarget) {
        updateToolbarContent(options.target);
        updateToolbarPosition(options.target);
    }
}

function handleZoom() {
    if (currentTarget) {
        updateToolbarPosition(currentTarget);
    }
}

function handleCanvasMouseDown(options) {
    const target = options.target;
    const isClickOnToolbar = toolbarElement && toolbarElement.contains(options.e.target);
    // Vérifier si le clic est DANS un dropdown de couleur ouvert
    const clickedDropdownMenu = options.e.target.closest('.dropdown-menu');
    const isClickInOpenColorDropdown = clickedDropdownMenu &&
                                       (clickedDropdownMenu.id === 'fill-color-dropdown-menu' || clickedDropdownMenu.id === 'stroke-color-dropdown-menu'); // Ajuste les ID si nécessaire


    console.log("[handleCanvasMouseDown] Fired. Target:", target, "Click on Toolbar:", isClickOnToolbar);

    if (target && !isClickOnToolbar && !isClickInOpenColorDropdown) {
        console.log("[handleCanvasMouseDown] Clicked ON an object. Calling showToolbar.");
        showToolbar(target);
        // Fermer les dropdowns couleur
        fillDropdownInstance?.hide();
        strokeDropdownInstance?.hide();
    } else if (!target && !isClickOnToolbar && !isClickInOpenColorDropdown) {
        console.log("[handleCanvasMouseDown] Clicked on BACKGROUND. Scheduling hideToolbar (50ms).");
        setTimeout(hideToolbar, 50);
        // Fermer les dropdowns couleur
        fillDropdownInstance?.hide();
        strokeDropdownInstance?.hide();
    }
}

// --- AJOUT : Fonction pour gérer les clics sur le document ---
function handleDocumentClickForDropdowns(event) {
    // Ne rien faire si la toolbar n'est pas visible
    if (!toolbarElement || toolbarElement.style.display === 'none') return;

    const clickedToolbarButton = event.target.closest('.toolbar-color-preview');
    const clickedDropdownMenu = event.target.closest('.dropdown-menu');

    // Si on clique en dehors d'un bouton d'ouverture de couleur ET en dehors d'un dropdown ouvert, on ferme les dropdowns
    if (!clickedToolbarButton && !clickedDropdownMenu) {
        fillDropdownInstance?.hide();
        strokeDropdownInstance?.hide();
    }
    // Si on clique sur un bouton d'ouverture, le listener du bouton gère le toggle.
    // Si on clique dans le dropdown, on laisse faire (pour sélectionner une couleur).
}