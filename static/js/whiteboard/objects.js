// objects.js
import { addDuplicateControl, deleteObject, cloneObject, renderIcon, deleteImg, cloneImg } from './controls.js'; // Import renderIcon
import { saveCanvasState } from './state.js';

export function addRectangle(canvas) {
    const rect = new fabric.Rect({
        left: 100,
        top: 50,
        fill: 'yellow',
        width: 200,
        height: 100,
        objectCaching: false,
        stroke: 'lightgreen',
        strokeWidth: 4,
    });
    rect.controls.deleteControl = new fabric.Control({
        x: 0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: deleteObject,
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });

    rect.controls.duplicateControl = new fabric.Control({
        x: -0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: cloneObject,
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });

    canvas.add(rect);
    canvas.setActiveObject(rect);
    saveCanvasState(canvas); // Pass canvas here
}

export function addText(canvas) {
    const text = new fabric.Textbox('Texte', {
        left: 50,
        top: 50,
        fill: 'black',
        fontSize: 20,
        width: 150,
        editable: true,
        // Activation du redimensionnement et de la rotation
        hasControls: true,
        hasRotatingPoint: true,
        lockScalingFlip: true,
    });
    addDuplicateControl(text);
    canvas.add(text);
    saveCanvasState(canvas); // Pass canvas here
}

export function deleteActiveObject(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.remove(activeObject);
    }
}

export function changeObjectColor(canvas, color) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        activeObject.set('fill', color);
        canvas.renderAll();
    }
}
