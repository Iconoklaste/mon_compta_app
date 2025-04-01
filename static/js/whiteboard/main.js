// main.js
import { initializeCanvas } from './canvas.js';
import { addRectangle, addText, deleteActiveObject } from './objects.js';
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
