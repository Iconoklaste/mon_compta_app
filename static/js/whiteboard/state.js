// state.js
import { updateZoomIndicator } from './ui.js';

let undoStack = [];
let redoStack = [];

export function saveCanvasState(canvas) { // Add canvas as argument
    undoStack.push(JSON.stringify(canvas.toJSON()));
    redoStack = [];
}

export function undo(canvas) {
    if (undoStack.length > 1) {
        redoStack.push(undoStack.pop());
        canvas.loadFromJSON(undoStack[undoStack.length - 1], canvas.renderAll.bind(canvas));
    }
}

export function redo(canvas) {
    if (redoStack.length > 0) {
        undoStack.push(redoStack.pop());
        canvas.loadFromJSON(undoStack[undoStack.length - 1], canvas.renderAll.bind(canvas));
    }
}

export function loadCanvas(canvas, data) {
    canvas.loadFromJSON(data, canvas.renderAll.bind(canvas));
    saveCanvasState(canvas); // Pass canvas here
}

export function saveWhiteboard(canvas, projetId) {
    const canvasData = canvas.toJSON();
    fetch(`/save_whiteboard/${projetId}`, { // change the route here
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(canvasData),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
