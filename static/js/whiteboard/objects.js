// objects.js
import { deleteObject, cloneObject, renderIcon, deleteImg, cloneImg } from './controls.js'; // Import renderIcon
import { saveCanvasState } from './state.js';

export function addRectangle(canvas) {
    const rect = new fabric.Rect({
        left: 100,
        top: 100,
        fill: 'yellow',
        width: 200,
        height: 100,
        objectCaching: false,
        stroke: 'lightgreen',
        strokeWidth: 4,
    });
    rect.controls.deleteControl = new fabric.Control({
        x: 0.5,   // Top-right corner
        y: -0.5,  // Top-right corner
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas), // Pass canvas here
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });

    rect.controls.duplicateControl = new fabric.Control({
        x: -0.5, // Top-left corner
        y: -0.5, // Top-left corner
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas), // Pass canvas here
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });

    canvas.add(rect);
    canvas.setActiveObject(rect);
    saveCanvasState(canvas); // Pass canvas here
}

export function addText(canvas) {
    const text = new fabric.Textbox('Texte', {
        left: 100,
        top: 100,
        fill: 'black',
        fontSize: 20,
        width: 150,
        editable: true,
        // Activation du redimensionnement et de la rotation
        hasControls: true,
        hasRotatingPoint: true,
        lockScalingFlip: true,
    });
    // Add the delete control to the text object
    text.controls.deleteControl = new fabric.Control({
        x: 0.5,   // Top-right corner
        y: -0.5,  // Top-right corner
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas), // Pass canvas here
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });
    text.controls.duplicateControl = new fabric.Control({
        x: -0.5, // Top-left corner
        y: -0.5, // Top-left corner
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas), // Pass canvas here
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });
    canvas.add(text);
    saveCanvasState(canvas); // Pass canvas here
}

export function deleteActiveObject(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.remove(activeObject);
        saveCanvasState(canvas);
    }
}

export function changeObjectColor(canvas, color) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        activeObject.set('fill', color);
        canvas.renderAll();
        saveCanvasState(canvas);
    }
}
