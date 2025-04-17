import { initializeCanvas } from './canvas.js';
import { addTriangle, addRectangle, addText, deleteActiveObject, sendToBack, bringToFront, sendBackward, bringForward, addCircle, addHexagon } from './objects.js';
import { initializeUI, updateFontSizeSelector, updateFontFamilySelector, loadData } from './ui.js';
import { undo, redo } from './state.js';
import { initializeColorPickers, updateFillPickerUI, updateStrokePickerUI } from './color-picker.js';



document.addEventListener('DOMContentLoaded', () => {
    const canvas = initializeCanvas();
    const projetId = window.projetId;

    initializeUI(canvas, projetId);
    initializeColorPickers(canvas);

    // Event listener for keydown (Ctrl+Z/Ctrl+Y)
    document.addEventListener('keydown', (event) => {
        if (event.ctrlKey || event.metaKey) {
            if (event.key === 'z') {
                undo(canvas);
            } else if (event.key === 'y') {
                redo(canvas);
            }
        }
    });

    // Function to deactivate free-draw mode
    function deactivateFreeDraw() {
        canvas.isDrawingMode = false;
        freeDrawButton.style.backgroundColor = '';
        freeDrawButtonIcon.style.fill = '#000000';
        canvas.defaultCursor = 'default';
    }

    // Get references to the buttons
    const addRectButton = document.getElementById('add-rect');
    const addCircleButton = document.getElementById('add-circle');
    const addTriangleButton = document.getElementById('add-triangle');
    const addHexagonButton = document.getElementById('add-hexagon');
    const addTextButton = document.getElementById('add-text');
    const deleteButton = document.getElementById('delete');
    const sendToBackButton = document.getElementById('send-to-back');
    const bringToFrontButton = document.getElementById('bring-to-front');
    const sendBackwardButton = document.getElementById('send-backward');
    const bringForwardButton = document.getElementById('bring-forward');
    const boldButton = document.getElementById('bold-button');
    const italicButton = document.getElementById('italic-button');
    const lineWidthSelector = document.getElementById('font-size-selector');
    const selectionButton = document.getElementById('selection-button');
    const selectionButtonIcon = selectionButton.querySelector('.text-icon');
    const panButton = document.getElementById('pan-button');
    const panButtonIcon = panButton.querySelector('.text-icon');
    const freeDrawButton = document.getElementById('free-draw-button');
    const freeDrawButtonIcon = freeDrawButton.querySelector('.text-icon');




    // Function to activate selection mode
    function activateSelectionMode() {
        deactivateAllModes();
        canvas.toggleSelectionMode(true);
        canvas.togglePanningMode(false);
        selectionButton.style.backgroundColor = '#333';
        selectionButtonIcon.style.fill = '#FFFFFF';
        selectionButtonIcon.style.stroke = '#FFFFFF';
    }

    // Function to activate pan mode
    function activatePanMode() {
        deactivateAllModes();
        canvas.toggleSelectionMode(false);
        canvas.togglePanningMode(true);
        panButton.style.backgroundColor = '#333';
        panButtonIcon.style.fill = '#FFFFFF';
    }

    // Function to deactivate all modes
    function deactivateAllModes() {
        deactivateFreeDraw();
        canvas.toggleSelectionMode(false);
        canvas.togglePanningMode(false);
        panButton.style.backgroundColor = '';
        panButtonIcon.style.fill = '#000000';
        selectionButton.style.backgroundColor = '';
        selectionButtonIcon.style.fill = '#000000';
        if (canvas.removeShapeListeners) {
            canvas.removeShapeListeners();
        }
        canvas.isDrawingShape = false;
    }

    // Set initial mode to pan
    activatePanMode();

    // Add event listeners for selection and pan buttons
    selectionButton.addEventListener('click', activateSelectionMode);
    panButton.addEventListener('click', activatePanMode);

    // Shape creation functions
    function handleShapeButtonClick(addShapeFunction) {
        deactivateAllModes();
        addShapeFunction(canvas, activatePanMode);
    }

    // Add event listeners for shape buttons
    addRectButton.addEventListener('click', () => handleShapeButtonClick(addRectangle));
    addCircleButton.addEventListener('click', () => handleShapeButtonClick(addCircle));
    addTriangleButton.addEventListener('click', () => handleShapeButtonClick(addTriangle));
    addHexagonButton.addEventListener('click', () => handleShapeButtonClick(addHexagon));
    addTextButton.addEventListener('click', () => handleShapeButtonClick(addText));

    // Supprimer un objet
    deleteButton.addEventListener('click', () => {
        deactivateAllModes();
        deleteActiveObject(canvas);
    });

    // Drawing mode toggle
    let isDrawing = false;

    // Set initial icon color to black
    freeDrawButtonIcon.style.fill = '#000000';

    freeDrawButton.addEventListener('click', () => {
        deactivateAllModes();
        isDrawing = !isDrawing;
        canvas.isDrawingMode = isDrawing;
        freeDrawButton.style.backgroundColor = isDrawing ? '#333' : '';
        freeDrawButtonIcon.style.fill = isDrawing ? '#FFFFFF' : '#000000';
        canvas.defaultCursor = isDrawing ? 'crosshair' : 'default';
        if (isDrawing) {
            canvas.freeDrawingBrush.color = currentColor;
            canvas.freeDrawingBrush.width = currentLineWidth;
        }
    });


    // Line width selector
    lineWidthSelector.addEventListener('change', () => {
        currentLineWidth = parseInt(lineWidthSelector.value);
        canvas.freeDrawingBrush.width = currentLineWidth;
        deactivateAllModes();
    });

    // Z-Order Controls
    document.getElementById('send-to-back').addEventListener('click', () => {
        deactivateAllModes();
        sendToBack(canvas);
    });
    document.getElementById('bring-to-front').addEventListener('click', () => {
        deactivateAllModes();
        bringToFront(canvas);
    });
    document.getElementById('send-backward').addEventListener('click', () => {
        deactivateAllModes();
        sendBackward(canvas);
    });
    document.getElementById('bring-forward').addEventListener('click', () => {
        deactivateAllModes();
        bringForward(canvas);
    });

    canvas.on('object:selected', (options) => {
        deactivateAllModes();
        options.target.moveTo(canvas.getObjects().indexOf(options.target));
    });

    canvas.on('selection:created', (event) => {
        console.log("selection:created event fired");
        updateFontSizeSelector(canvas); // Gardez ceci si pertinent
        updateFontFamilySelector(canvas); // Gardez ceci si pertinent
        if (event.selected && event.selected.length > 0) {
            const selectedObject = event.selected[0];
            // Appeler les fonctions de mise à jour de l'UI du color-picker
            const fill = selectedObject.fill || null; // Obtenir la couleur de remplissage
            const opacity = selectedObject.opacity === undefined ? 1 : selectedObject.opacity; // Obtenir l'opacité
            const stroke = selectedObject.stroke || null; // Obtenir la couleur de contour
            const strokeWidth = selectedObject.strokeWidth === undefined ? 0 : selectedObject.strokeWidth; // Obtenir l'épaisseur
    
            updateFillPickerUI(fill, opacity);
            updateStrokePickerUI(stroke, strokeWidth);
        } else {
             // Optionnel : Réinitialiser les pickers si rien n'est sélectionné
             updateFillPickerUI(null, 1); // Couleur par défaut ou null
             updateStrokePickerUI(null, 0); // Couleur par défaut ou null
        }
    });

    canvas.on('selection:updated', (event) => {
        console.log("selection:updated event fired");
        updateFontSizeSelector(canvas); // Gardez ceci
        updateFontFamilySelector(canvas); // Gardez ceci
        if (event.selected && event.selected.length > 0) {
            const selectedObject = event.selected[0];
             // Appeler les fonctions de mise à jour de l'UI du color-picker
            const fill = selectedObject.fill || null;
            const opacity = selectedObject.opacity === undefined ? 1 : selectedObject.opacity;
            const stroke = selectedObject.stroke || null;
            const strokeWidth = selectedObject.strokeWidth === undefined ? 0 : selectedObject.strokeWidth;
    
            updateFillPickerUI(fill, opacity);
            updateStrokePickerUI(stroke, strokeWidth);
        } else {
             // Optionnel : Réinitialiser les pickers
             updateFillPickerUI(null, 1);
             updateStrokePickerUI(null, 0);
        }
    });

    canvas.on('selection:cleared', () => {
        updateFontSizeSelector(canvas); // Gardez ceci
        updateFontFamilySelector(canvas); // Gardez ceci
        // Réinitialiser les pickers de couleur lorsque la sélection est effacée
        updateFillPickerUI(null, 1); // Ou une couleur/opacité par défaut
        updateStrokePickerUI(null, 0); // Ou une couleur/épaisseur par défaut
    });

    loadData(canvas, projetId);

    // Add event listeners to the buttons
    boldButton.addEventListener('click', () => {
        deactivateAllModes();
        toggleBold(canvas);
    });

    italicButton.addEventListener('click', () => {
        deactivateAllModes();
        toggleItalic(canvas);
    });

    // Function to toggle bold
    function toggleBold(canvas) {
        const activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'textbox') {
            const isBold = activeObject.fontWeight === 'bold';
            activeObject.set('fontWeight', isBold ? 'normal' : 'bold');
            boldButton.classList.toggle('active', !isBold);
            canvas.renderAll();
        }
    }

    // Function to toggle italic
    function toggleItalic(canvas) {
        const activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'textbox') {
            const isItalic = activeObject.fontStyle === 'italic';
            activeObject.set('fontStyle', isItalic ? 'normal' : 'italic');
            italicButton.classList.toggle('active', !isItalic);
            canvas.renderAll();
        }
    }
});
