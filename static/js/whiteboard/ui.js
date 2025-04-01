// ui.js
import { changeObjectColor } from './objects.js';
import { saveWhiteboard, loadCanvas } from './state.js';
import { zoomIn, zoomOut } from './canvas.js';
import { saveCanvasState } from './state.js';

export function initializeUI(canvas, projetId) {
    const colorPicker = document.getElementById('color-picker');
    const fontSizeSelector = document.getElementById('font-size-selector');
    const fontFamilySelector = document.getElementById('font-family-selector');

    colorPicker.addEventListener('change', () => {
        const selectedColor = colorPicker.value;
        changeObjectColor(canvas, selectedColor);
    });

    fontSizeSelector.addEventListener('change', () => {
        const selectedFontSize = parseInt(fontSizeSelector.value, 10);
        const activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'textbox') {
            if (activeObject.selectionStart !== activeObject.selectionEnd) {
                activeObject.setSelectionStyles({ fontSize: selectedFontSize }, activeObject.selectionStart, activeObject.selectionEnd);
            } else {
                activeObject.set('fontSize', selectedFontSize);
            }
            canvas.renderAll();
            saveCanvasState(canvas);
        }
    });

    fontFamilySelector.addEventListener('change', () => {
        const selectedFontFamily = fontFamilySelector.value;
        const activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'textbox') {
            if (activeObject.selectionStart !== activeObject.selectionEnd) {
                activeObject.setSelectionStyles({ fontFamily: selectedFontFamily }, activeObject.selectionStart, activeObject.selectionEnd);
            } else {
                activeObject.set('fontFamily', selectedFontFamily);
            }
            canvas.renderAll();
            saveCanvasState(canvas);
        }
    });

    fontSizeSelector.value = null;
    fontFamilySelector.value = null;

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

export function updateFontSizeSelector(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject && activeObject.type === 'textbox') {
        if (activeObject.selectionStart !== activeObject.selectionEnd) {
        } else {
            document.getElementById('font-size-selector').value = activeObject.fontSize;
        }
    } else {
        document.getElementById('font-size-selector').value = null;
    }
}

export function updateFontFamilySelector(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject && activeObject.type === 'textbox') {
        document.getElementById('font-family-selector').value = activeObject.fontFamily;
    } else {
        document.getElementById('font-family-selector').value = null;
    }
}

export function updateZoomIndicator(canvas) {
    const zoomPercentage = Math.round(canvas.getZoom() * 100);
    document.getElementById('zoom-indicator').textContent = `Zoom: ${zoomPercentage}%`;
}

export function loadData(canvas, projetId) {
    fetch(`/load/${projetId}`) // change the route here
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.whiteboard_data) { // change the data access here
                loadCanvas(canvas, data.whiteboard_data);
            } else {
                console.log('No data found for this project.');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}
