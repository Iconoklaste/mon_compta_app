import { initializeCanvas } from './canvas.js';
import { addTriangle, addRectangle, addText, deleteActiveObject, sendToBack, bringToFront, sendBackward, bringForward, addCircle, addHexagon } from './objects.js';
import { initializeUI, updateFontSizeSelector, updateFontFamilySelector, loadData } from './ui.js';
import { undo, redo } from './state.js';

// Define your color sets
const mainColors = [
    "#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF",
    "#4B0082", "#9400D3", "#800000", "#808000", "#008000",
    "#000080", "#800080", "#008080", "#C0C0C0", "#808080",
    "#FFFFFF", "#000000", "#FFA500", "#00FFFF", "#FF00FF",
    "#FFC0CB", "#ADD8E6", "#90EE90", "#F0E68C", "#E6E6FA",
    "#D3D3D3", "#A9A9A9", "#778899", "#B0C4DE", "#696969",
    "#F0F8FF", "#FAEBD7", "#008B8B", "#00CED1", "#4682B4",
    "#00008B", "#191970", "#8B008B", "#8B4513", "#2F4F4F",
    "#228B22", "#006400", "#BDB76B", "#556B2F", "#8FBC8F",
    "#6B8E23", "#DAA520", "#D2691E", "#CD853F", "#DEB887"
];

const strokeColors = ['#000000', '#808080', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF']; // Example stroke colors

document.addEventListener('DOMContentLoaded', () => {
    const canvas = initializeCanvas();
    const projetId = window.projetId;

    initializeUI(canvas, projetId);

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
    const colorPreviewButton = document.getElementById('color-dropdown-button');
    const colorPreviewIcon = colorPreviewButton.querySelector('.color-preview-icon');
    const colorDropdownMenu = document.querySelector('.color-dropdown-menu');
    const transparencySlider = document.getElementById('transparency-slider');
    const strokeColorDropdownMenu = document.getElementById('stroke-color-dropdown-menu');
    const strokeColorPreviewButton = document.getElementById('stroke-color-preview-button');
    const strokeColorPreviewIcon = strokeColorPreviewButton.querySelector('.color-preview-icon');
    const strokeWidthSlider = document.getElementById('stroke-width-slider');
    const colorPalette = document.getElementById('color-palette');
    const strokeColorGrid = document.getElementById('stroke-color-grid');

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
        colorDropdownMenu.classList.remove('show');
        if (strokeColorDropdownMenu) {
            strokeColorDropdownMenu.classList.remove('show');
        }
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
        updateFontSizeSelector(canvas);
        updateFontFamilySelector(canvas);
        if (event.selected && event.selected.length > 0) {
            const selectedObject = event.selected[0];
            updatePaletteFromObject(selectedObject);
            updateStrokePaletteFromObject(selectedObject);
        }
    });

    canvas.on('selection:updated', (event) => {
        console.log("selection:updated event fired");
        updateFontSizeSelector(canvas);
        updateFontFamilySelector(canvas);
        if (event.selected && event.selected.length > 0) {
            const selectedObject = event.selected[0];
            updatePaletteFromObject(selectedObject);
            updateStrokePaletteFromObject(selectedObject);
        }
    });

    canvas.on('selection:cleared', () => {
        updateFontSizeSelector(canvas);
        updateFontFamilySelector(canvas);
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

    // Function to create the main color palette
    function createMainColorPalette(container, colors) {
        colors.forEach(color => {
            const colorCell = document.createElement('div');
            colorCell.classList.add('color-cell');
            colorCell.style.backgroundColor = color;
            colorCell.dataset.color = color;
            container.appendChild(colorCell);

            colorCell.addEventListener('click', () => {
                applyColorToSelectedObject(color);
                updateColorPreview(color);
                // Remove the 'selected' class from all color cells in this palette
                container.querySelectorAll('.color-cell').forEach(cell => {
                    cell.classList.remove('selected');
                });
                // Add the 'selected' class to the clicked color cell
                colorCell.classList.add('selected');
            });
        });
    }

    // Function to create the stroke color palette
    function createStrokeColorPalette(container, colors) {
        colors.forEach(color => {
            const colorCell = document.createElement('div');
            colorCell.classList.add('color-cell');
            colorCell.style.backgroundColor = color;
            colorCell.dataset.color = color;
            container.appendChild(colorCell);

            colorCell.addEventListener('click', () => {
                applyStrokeColorToSelectedObject(color);
                updateStrokeColorPreview(color);
                // Remove the 'selected' class from all color cells in this palette
                container.querySelectorAll('.color-cell').forEach(cell => {
                    cell.classList.remove('selected');
                });
                // Add the 'selected' class to the clicked color cell
                colorCell.classList.add('selected');
            });
        });
    }

    // Create the main color palette
    createMainColorPalette(colorPalette, mainColors);

    // Create the stroke color palette
    createStrokeColorPalette(strokeColorGrid, strokeColors);

    // Function to update the color preview
    function updateColorPreview(color) {
        colorPreviewIcon.style.backgroundColor = color;
    }

    // Function to update the stroke color preview
    function updateStrokeColorPreview(color) {
        strokeColorPreviewIcon.style.backgroundColor = color;
    }

    // Event listener for transparency slider
    document.getElementById('transparency-slider').addEventListener('input', (event) => {
        const transparency = parseFloat(event.target.value);
        applyTransparencyToSelectedObject(transparency);
    });

    // Function to apply color to the selected object
    function applyColorToSelectedObject(color) {
        const activeObject = canvas.getActiveObject();
        if (activeObject) {
            activeObject.set('fill', color);
            canvas.renderAll();
        }
    }

    // Function to apply transparency to the selected object
    function applyTransparencyToSelectedObject(transparency) {
        const activeObject = canvas.getActiveObject();
        if (activeObject) {
            activeObject.set('opacity', transparency);
            canvas.renderAll();
        }
    }

    // Function to update the palette with the selected object's color and transparency
    function updatePaletteFromObject(selectedObject) {
        console.log("updatePaletteFromObject called");
        console.log("Selected Object Type:", selectedObject.type);
        if (selectedObject && selectedObject.fill) {
            const objectColor = selectedObject.fill;
            const objectOpacity = selectedObject.opacity;

            // Update the color preview
            updateColorPreview(objectColor);

            // Update the selected color in the palette
            const colorCells = document.querySelectorAll('#color-palette .color-cell');
            colorCells.forEach(cell => {
                cell.classList.remove('selected');
                if (cell.dataset.color === objectColor) {
                    cell.classList.add('selected');
                }
            });

            // Update the transparency slider
            transparencySlider.value = objectOpacity;

            // Log the color and alpha to the console
            console.log("Selected Object Color:", objectColor);
            console.log("Selected Object Alpha (Opacity):", objectOpacity);
        }
    }

    // Global variables for stroke color and width
    let currentStrokeColor = 'black';
    let currentStrokeWidth = 1;

    // Function to apply stroke color to the selected object
    function applyStrokeColorToSelectedObject(color) {
        const selectedObject = canvas.getActiveObject();
        if (selectedObject) {
            selectedObject.set('stroke', color);
            canvas.renderAll();
        }
    }

    // Function to apply stroke width to the selected object
    function applyStrokeWidthToSelectedObject(width) {
        const selectedObject = canvas.getActiveObject();
        if (selectedObject) {
            selectedObject.set('strokeWidth', width);
            canvas.renderAll();
        }
    }

    // Function to update the stroke color palette from the selected object
    function updateStrokePaletteFromObject(selectedObject) {
        if (selectedObject) {
            const strokeColor = selectedObject.get('stroke');
            const strokeWidth = selectedObject.get('strokeWidth');

            // Update the stroke color preview
            strokeColorPreviewIcon.style.backgroundColor = strokeColor;
            currentStrokeColor = strokeColor;

            // Update the selected color in the palette
            const colorCells = document.querySelectorAll('#stroke-color-grid .color-cell');
            colorCells.forEach(cell => {
                cell.classList.remove('selected');
                if (cell.style.backgroundColor === strokeColor) {
                    cell.classList.add('selected');
                }
            });

            // Update the stroke width slider
            strokeWidthSlider.value = strokeWidth;
            currentStrokeWidth = strokeWidth;
        }
    }

    // Function to handle stroke width change
    function handleStrokeWidthChange(event) {
        const width = parseInt(event.target.value);
        applyStrokeWidthToSelectedObject(width);
        currentStrokeWidth = width;
    }

    // Event listener for stroke width slider
    strokeWidthSlider.addEventListener('input', handleStrokeWidthChange);

    // Add event listener to the color dropdown button
    colorPreviewButton.addEventListener('click', (event) => {
        event.stopPropagation(); // Prevent the click from propagating to the document
        //colorDropdownMenu.classList.toggle('show');
        const dropdown = new bootstrap.Dropdown(colorPreviewButton);
        dropdown.toggle();
        strokeColorDropdownMenu.classList.remove('show'); // Ensure the other dropdown is closed
    });

    // Close the dropdown when clicking outside of it
    document.addEventListener('click', (event) => {
        if (!colorPreviewButton.contains(event.target) && !colorDropdownMenu.contains(event.target)) {
            colorDropdownMenu.classList.remove('show');
        }
    });

    // Add event listener to the stroke color dropdown button
    strokeColorPreviewButton.addEventListener('click', (event) => {
        event.stopPropagation(); // Prevent the click from propagating to the document
        //strokeColorDropdownMenu.classList.toggle('show');
        const dropdown = new bootstrap.Dropdown(strokeColorPreviewButton);
        dropdown.toggle();
        colorDropdownMenu.classList.remove('show'); // Ensure the other dropdown is closed
    });

    // Close the dropdown when clicking outside of it
    document.addEventListener('click', (event) => {
        if (!strokeColorPreviewButton.contains(event.target) && !strokeColorDropdownMenu.contains(event.target)) {
            strokeColorDropdownMenu.classList.remove('show');
        }
    });
});
