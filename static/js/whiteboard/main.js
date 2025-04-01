// main.js
import { initializeCanvas } from './canvas.js';
import { addRectangle, addText, deleteActiveObject, sendToBack, bringToFront, sendBackward, bringForward } from './objects.js'; // Corrected import
import { initializeUI, updateFontSizeSelector, updateFontFamilySelector, loadData } from './ui.js';
import { undo, redo } from './state.js';

document.addEventListener('DOMContentLoaded', () => {
    const canvas = initializeCanvas();
    const projetId = window.projetId; // Get projetId from the global variable
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

    // Ajouter un rectangle
    document.getElementById('add-rect').addEventListener('click', () => {
        addRectangle(canvas);
    });

    // Ajouter du texte
    document.getElementById('add-text').addEventListener('click', () => {
        addText(canvas);
    });

    // Supprimer un objet
    document.getElementById('delete').addEventListener('click', () => {
        deleteActiveObject(canvas);
    });

    // Z-Order Controls
    document.getElementById('send-to-back').addEventListener('click', () => {
        sendToBack(canvas);
    });
    document.getElementById('bring-to-front').addEventListener('click', () => {
        bringToFront(canvas);
    });
    document.getElementById('send-backward').addEventListener('click', () => {
        sendBackward(canvas);
    });
    document.getElementById('bring-forward').addEventListener('click', () => {
        bringForward(canvas);
    });

    canvas.on('selection:created', () => {
        updateFontSizeSelector(canvas);
        updateFontFamilySelector(canvas);
    });
    canvas.on('selection:updated', () => {
        updateFontSizeSelector(canvas);
        updateFontFamilySelector(canvas);
    });
    canvas.on('selection:cleared', () => {
        updateFontSizeSelector(canvas);
        updateFontFamilySelector(canvas);
    });

    loadData(canvas, projetId); // Call loadData without initialData
});
