// ui.js
import { changeObjectColor } from './objects.js';
import { saveWhiteboard, loadCanvas } from './state.js';
import { zoomIn, zoomOut } from './canvas.js';
import { saveCanvasState } from './state.js';

export function initializeUI(canvas, projetId) {
    const fontSizeSelector = document.getElementById('font-size-selector');
    const fontFamilySelector = document.getElementById('font-family-selector');

/*     // Initialize vanilla-picker
    const parent = document.getElementById('color-picker-container');
    const openPickerButton = document.getElementById('open-color-picker');
    const picker = new Picker({
        parent: parent,
        popup: 'bottom',
        color: 'rgb(255, 0, 0)',
        alpha: true,
        editor: true,
        editorFormat: 'hex',
        onChange: function(color) {
            changeObjectColor(canvas, color.rgbaString);
        },
    }); */



    fontSizeSelector.addEventListener('change', () => {
        const selectedFontSize = parseInt(fontSizeSelector.value, 10);
        const activeObject = canvas.getActiveObject();
        const target = getTargetTextbox(activeObject);
        if (target) {
            if (target.selectionStart !== target.selectionEnd) {
                target.setSelectionStyles({ fontSize: selectedFontSize }, target.selectionStart, target.selectionEnd);
            } else {
                target.set('fontSize', selectedFontSize);
            }
            canvas.renderAll();
            saveCanvasState(canvas);
        }
    });

    fontFamilySelector.addEventListener('change', async () => {
        const selectedFontFamily = fontFamilySelector.value;
        const activeObject = canvas.getActiveObject();
        const target = getTargetTextbox(activeObject);
        if (target) {
            // Check if the font is loaded
            if (!document.fonts.check(`12px ${selectedFontFamily}`)) {
                // If not loaded, wait for it to load
                await document.fonts.load(`12px ${selectedFontFamily}`);
            }
            if (target.selectionStart !== target.selectionEnd) {
                target.setSelectionStyles({ fontFamily: selectedFontFamily }, target.selectionStart, target.selectionEnd);
            } else {
                target.set('fontFamily', selectedFontFamily);
            }
            canvas.renderAll();
            saveCanvasState(canvas);
        }
    });

    document.getElementById('zoom-in').addEventListener('click', () => {
        zoomIn(canvas);
    });

    document.getElementById('zoom-out').addEventListener('click', () => {
        zoomOut(canvas);
    });

    document.getElementById('saveButton').addEventListener('click', () => {
        saveWhiteboard(canvas, projetId);
    });
}

function getTargetTextbox(activeObject) {
    if (!activeObject) return null;
    if (activeObject.type === 'textbox') {
        return activeObject;
    } else if (activeObject.type === 'group') {
        return activeObject.getObjects().find(obj => obj.type === 'textbox');
    }
    return null;
}

export function updateFontSizeSelector(canvas) {
    const activeObject = canvas.getActiveObject();
    const target = getTargetTextbox(activeObject);
    if (target) {
        document.getElementById('font-size-selector').value = target.fontSize;
    } else {
        document.getElementById('font-size-selector').value = null;
    }
}

export async function updateFontFamilySelector(canvas) {
    const activeObject = canvas.getActiveObject();
    const target = getTargetTextbox(activeObject);
    if (target) {
        const fontFamily = target.fontFamily;
        // Check if the font is loaded
        if (!document.fonts.check(`12px ${fontFamily}`)) {
            // If not loaded, wait for it to load
            await document.fonts.load(`12px ${fontFamily}`);
        }
        document.getElementById('font-family-selector').value = fontFamily;
    } else {
        document.getElementById('font-family-selector').value = null;
    }
}

export function updateZoomIndicator(canvas) {
    const zoomPercentage = Math.round(canvas.getZoom() * 100);
    document.getElementById('zoom-indicator').textContent = `Zoom: ${zoomPercentage}%`;
}

export function loadData(canvas, projetId) {
    fetch(`/load/${projetId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.whiteboard_data) {
                loadCanvas(canvas, data.whiteboard_data);
                // Update the font selector after loading the canvas
                updateFontFamilySelector(canvas);
            } else {
                console.log('No data found for this project.');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}
