// objects.js
import { deleteObject, cloneObject, renderIcon, deleteImg, cloneImg } from './controls.js';
import { saveCanvasState } from './state.js';

// Helper function to create a regular polygon
function createRegularPolygon(centerX, centerY, sides, radius, angle = 0, options = {}) {
    const points = [];
    for (let i = 0; i < sides; i++) {
        const rad = (angle + (i * (360 / sides))) * Math.PI / 180;
        points.push({
            x: centerX + radius * Math.cos(rad),
            y: centerY + radius * Math.sin(rad)
        });
    }
    return new fabric.Polygon(points, options);
}

export function addRectangle(canvas) {
    const rect = new fabric.Rect({
        left: canvas.getWidth() / 2,
        top: canvas.getHeight() / 2,
        fill: 'yellow',
        width: 200,
        height: 100,
        objectCaching: false,
        stroke: null,
        strokeWidth: 0,
        originX: 'center',
        originY: 'center',
    });
    rect.controls.deleteControl = new fabric.Control({
        x: 0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas),
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });

    rect.controls.duplicateControl = new fabric.Control({
        x: -0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas),
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });

    canvas.add(rect);
    canvas.setActiveObject(rect);
    saveCanvasState(canvas);
}

export function addText(canvas) {
    const rect = new fabric.Rect({
        left: canvas.getWidth() / 2,
        top: canvas.getHeight() / 2,
        fill: 'yellow',
        width: 200,
        height: 100,
        objectCaching: false,
        stroke: null,
        strokeWidth: 0,
        originX: 'center',
        originY: 'center',
    });

    const text = new fabric.Textbox('Texte', {
        left: rect.left,
        top: rect.top,
        fill: 'black',
        fontSize: 20,
        width: rect.width,
        textAlign: 'center',
        originX: 'center',
        originY: 'center',
        splitByGrapheme: true,
    });

    // Add the delete control to the text object
    text.controls.deleteControl = new fabric.Control({
        x: 0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas),
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });
    text.controls.duplicateControl = new fabric.Control({
        x: -0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas),
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });

    // Function to update text position and size
    function updateTextPositionAndSize() {
        text.set({
            left: rect.left,
            top: rect.top,
            width: rect.width,
        });
        text.setCoords();
    }

    // Event listener for scaling the rectangle
    rect.on('scaling', () => {
        updateTextPositionAndSize();
    });

    // Event listener for moving the rectangle
    rect.on('moving', () => {
        updateTextPositionAndSize();
    });

    // Add the rectangle and text to a group
    const group = new fabric.Group([rect, text], {
        left: rect.left,
        top: rect.top,
        originX: 'center',
        originY: 'center',
    });

    // Add the delete control to the group
    group.controls.deleteControl = new fabric.Control({
        x: 0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas),
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });
    group.controls.duplicateControl = new fabric.Control({
        x: -0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas),
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });

    canvas.add(group);
    canvas.setActiveObject(group);
    saveCanvasState(canvas);
}

export function addCircle(canvas) {
    const circle = new fabric.Circle({
        left: canvas.getWidth() / 2,
        top: canvas.getHeight() / 2,
        fill: 'red',
        radius: 50,
        objectCaching: false,
        stroke: null,
        strokeWidth: 0,
        originX: 'center',
        originY: 'center',
    });
    circle.controls.deleteControl = new fabric.Control({
        x: 0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas),
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });

    circle.controls.duplicateControl = new fabric.Control({
        x: -0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas),
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });

    canvas.add(circle);
    canvas.setActiveObject(circle);
    saveCanvasState(canvas);
}

export function addHexagon(canvas) {
    const hexagon = createRegularPolygon(canvas.getWidth() / 2, canvas.getHeight() / 2, 6, 50, 30, {
        fill: 'blue',
        objectCaching: false,
        stroke: null,
        strokeWidth: 0,
        originX: 'center',
        originY: 'center',
    });

    hexagon.controls.deleteControl = new fabric.Control({
        x: 0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: 16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas),
        render: renderIcon(deleteImg),
        cornerSize: 24,
    });

    hexagon.controls.duplicateControl = new fabric.Control({
        x: -0.5,
        y: -0.5,
        offsetY: -16,
        offsetX: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas),
        render: renderIcon(cloneImg),
        cornerSize: 24,
    });

    canvas.add(hexagon);
    canvas.setActiveObject(hexagon);
    saveCanvasState(canvas);
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
        if (activeObject.type === 'group') {
            activeObject.forEachObject(obj => {
                if (obj.type === 'rect') {
                    obj.set('fill', color);
                }
            });
        } else {
            activeObject.set('fill', color);
        }
        canvas.renderAll();
        saveCanvasState(canvas);
    }
}

// New functions for Z-Order
export function sendToBack(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.sendToBack(activeObject);
        canvas.discardActiveObject();
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}

export function bringToFront(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.bringToFront(activeObject);
        canvas.discardActiveObject();
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}

export function sendBackward(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.sendBackwards(activeObject);
        canvas.discardActiveObject();
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}

export function bringForward(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.bringForward(activeObject);
        canvas.discardActiveObject();
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}
