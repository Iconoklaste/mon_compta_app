// state.js
import { updateZoomIndicator } from './ui.js';
import { addDuplicateControl, deleteObject, cloneObject, renderIcon, deleteImg, cloneImg } from './controls.js';

let undoStack = [];
let redoStack = [];

export function saveCanvasState(canvas) { // Add canvas as argument
    undoStack.push(JSON.stringify(canvas.toJSON(['deleteControl', 'duplicateControl']))); // Add the controls to the toJSON method
    redoStack = [];
}

function addControlsToObject(obj, canvas) {
    if (obj.type === 'textbox') {
        // Add the duplicate control to the text object
        addDuplicateControl(obj, canvas);
        // Add the delete control to the text object
        obj.controls.deleteControl = new fabric.Control({
            x: 0.5,   // Top-right corner
            y: -0.5,  // Top-right corner
            offsetY: -16,
            offsetX: 16,
            cursorStyle: 'pointer',
            mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas), // Pass canvas here
            render: renderIcon(deleteImg),
            cornerSize: 24,
        });
    }
    if (obj.type === 'rect') {
        // Add the delete and duplicate controls to the rect object
        obj.controls.deleteControl = new fabric.Control({
            x: 0.5,   // Top-right corner
            y: -0.5,  // Top-right corner
            offsetY: -16,
            offsetX: 16,
            cursorStyle: 'pointer',
            mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas), // Pass canvas here
            render: renderIcon(deleteImg),
            cornerSize: 24,
        });
        obj.controls.duplicateControl = new fabric.Control({
            x: -0.5, // Top-left corner
            y: -0.5, // Top-left corner
            offsetY: -16,
            offsetX: -16,
            cursorStyle: 'pointer',
            mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas), // Pass canvas here
            render: renderIcon(cloneImg),
            cornerSize: 24,
        });
    }
}

export function undo(canvas) {
    if (undoStack.length > 1) {
        redoStack.push(undoStack.pop());
        canvas.loadFromJSON(undoStack[undoStack.length - 1], function() { // Add a callback function
            canvas.getObjects().forEach(function(obj) {
                addControlsToObject(obj, canvas);
            });
            canvas.renderAll();
        });
    }
}

export function redo(canvas) {
    if (redoStack.length > 0) {
        undoStack.push(redoStack.pop());
        canvas.loadFromJSON(undoStack[undoStack.length - 1], function() { // Add a callback function
            canvas.getObjects().forEach(function(obj) {
                addControlsToObject(obj, canvas);
            });
            canvas.renderAll();
        });
    }
}

export function loadCanvas(canvas, data) {
    canvas.loadFromJSON(data, function() { // Add a callback function
        canvas.getObjects().forEach(function(obj) {
            addControlsToObject(obj, canvas);
        });
        canvas.renderAll();
        saveCanvasState(canvas); // Pass canvas here
    });
}

export function saveWhiteboard(canvas, projetId) {
    const canvasData = canvas.toJSON(['deleteControl', 'duplicateControl']); // Add the controls to the toJSON method
    const csrfToken = document.getElementById('csrfToken').value;
    
    fetch(`/save_whiteboard/${projetId}`, { // change the route here
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
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
