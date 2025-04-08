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

function addShape(canvas, shapeType, activatePanMode) {
    let isDragging = false;
    let origX, origY;
    let shape;
    let minDragDistance = 5;
    let shapeAdded = false;
    let isMouseDown = false;

    canvas.selection = false;
    canvas.defaultCursor = 'crosshair';
    canvas.isDrawingShape = true;

    const handleMouseDown = (options) => {
        if (options.target) return;
        isMouseDown = true;
        isDragging = false;
        const pointer = canvas.getPointer(options.e);
        origX = pointer.x;
        origY = pointer.y;
        shapeAdded = false;

        switch (shapeType) {
            case 'triangle':
                shape = new fabric.Triangle({
                    left: origX,
                    top: origY,
                    width: 0,
                    height: 0,
                    fill: 'blue',
                    originX: 'left',
                    originY: 'top',
                });
                break;
            case 'rectangle':
                shape = new fabric.Rect({
                    left: origX,
                    top: origY,
                    width: 0,
                    height: 0,
                    fill: 'yellow',
                    originX: 'left',
                    originY: 'top',
                });
                break;
            case 'circle':
                shape = new fabric.Circle({
                    left: origX,
                    top: origY,
                    radius: 0,
                    fill: 'red',
                    originX: 'left',
                    originY: 'top',
                });
                break;
            case 'hexagon':
                shape = createRegularPolygon(origX, origY, 6, 0, 30, {
                    fill: 'blue',
                    originX: 'left',
                    originY: 'top',
                });
                break;
        }

        if (shape) {
            shape.controls.deleteControl = new fabric.Control({
                x: 0.5,
                y: -0.5,
                offsetY: -16,
                offsetX: 16,
                cursorStyle: 'pointer',
                mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas),
                render: renderIcon(deleteImg),
                cornerSize: 24,
            });

            shape.controls.duplicateControl = new fabric.Control({
                x: -0.5,
                y: -0.5,
                offsetY: -16,
                offsetX: -16,
                cursorStyle: 'pointer',
                mouseUpHandler: (eventData, transform) => cloneObject(eventData, transform, canvas),
                render: renderIcon(cloneImg),
                cornerSize: 24,
            });
        }
    };

    const handleMouseMove = (options) => {
        if (!isMouseDown) return;
        canvas.selection = false;
        const pointer = canvas.getPointer(options.e);
        const width = Math.abs(pointer.x - origX);
        const height = Math.abs(pointer.y - origY);
        const distanceDragged = Math.sqrt(width * width + height * height);

        if (distanceDragged > 0) {
            isDragging = true;
        }

        if (shapeType === 'circle') {
            shape.set({ radius: Math.max(width, height) / 2 });
        } else if (shapeType === 'hexagon') {
            shape.set({
                points: createRegularPolygon(origX, origY, 6, Math.max(width, height) / 2, 30).points,
            });
        } else {
            shape.set({ width: width, height: height });
        }

        if (pointer.x < origX) {
            shape.set({ left: pointer.x });
        }
        if (pointer.y < origY) {
            shape.set({ top: pointer.y });
        }
        if (distanceDragged < minDragDistance) {
            if (shapeAdded) {
                canvas.remove(shape);
                shapeAdded = false;
            }
        } else {
            if (!shapeAdded) {
                canvas.add(shape);
                shapeAdded = true;
            }
        }
        canvas.renderAll();
    };

    const handleMouseUp = (options) => {
        isMouseDown = false;
        if (!isDragging) {
            if (shape) {
                canvas.remove(shape);
            }
        } else {
            if (shape && shapeAdded) {
                canvas.setActiveObject(shape);
                saveCanvasState(canvas);
                activatePanMode();
                canvas.requestRenderAll()
            } else {
                if (shape) {
                    canvas.remove(shape);
                }
            }
        }
        isDragging = false;
        canvas.isDrawingShape = false;
        canvas.defaultCursor = 'default';
        canvas.removeShapeListeners();
    };

    canvas.on('mouse:down', handleMouseDown);
    canvas.on('mouse:move', handleMouseMove);
    canvas.on('mouse:up', handleMouseUp);
    const removeListeners = () => {
        canvas.off('mouse:down', handleMouseDown);
        canvas.off('mouse:move', handleMouseMove);
        canvas.off('mouse:up', handleMouseUp);
    };
    canvas.removeShapeListeners = removeListeners;
}

export function addTriangle(canvas, activatePanMode) {
    if (canvas.removeShapeListeners) {
        canvas.removeShapeListeners();
    }
    addShape(canvas, 'triangle', activatePanMode);
}

export function addRectangle(canvas, activatePanMode) {
    if (canvas.removeShapeListeners) {
        canvas.removeShapeListeners();
    }
    addShape(canvas, 'rectangle', activatePanMode);
}

export function addCircle(canvas, activatePanMode) {
    if (canvas.removeShapeListeners) {
        canvas.removeShapeListeners();
    }
    addShape(canvas, 'circle', activatePanMode);
}

export function addHexagon(canvas, activatePanMode) {
    if (canvas.removeShapeListeners) {
        canvas.removeShapeListeners();
    }
    addShape(canvas, 'hexagon', activatePanMode);
}

export function addText(canvas, activatePanMode) {
    if (canvas.removeShapeListeners) {
        canvas.removeShapeListeners();
    }
    const text = new fabric.Textbox('Texte', {
        left: canvas.getWidth() / 2,
        top: canvas.getHeight() / 2,
        fill: 'black',
        fontSize: 20,
        width: 200,
        textAlign: 'left',
        originX: 'center',
        originY: 'center',
        splitByGrapheme: true,
    });

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

    canvas.add(text);
    canvas.setActiveObject(text);
    saveCanvasState(canvas);
    activatePanMode();
    canvas.removeShapeListeners();
    canvas.requestRenderAll()
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
