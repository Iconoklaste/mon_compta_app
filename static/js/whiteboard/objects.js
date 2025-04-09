// objects.js
// Importe addCustomControls au lieu de duplicateObject
import { addCustomControls, deleteObject, renderIcon, deleteImg, cloneImg } from './controls.js';
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
                    fill: 'blue', // Default color, can be changed
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
                    fill: 'yellow', // Default color
                    originX: 'left',
                    originY: 'top',
                });
                break;
            case 'circle':
                shape = new fabric.Circle({
                    left: origX,
                    top: origY,
                    radius: 0,
                    fill: 'red', // Default color
                    originX: 'left',
                    originY: 'top',
                });
                break;
            case 'hexagon':
                shape = createRegularPolygon(origX, origY, 6, 0, 30, {
                    fill: 'green', // Default color
                    originX: 'center', // Center origin might be better for polygons
                    originY: 'center',
                });
                // Adjust initial position for center origin
                shape.set({ left: origX, top: origY });
                break;
        }

        // --- Utilisation de addCustomControls ---
        if (shape) {
            // Appelle la fonction centralisée pour ajouter les contrôles
            addCustomControls(shape, canvas);
        }
        // --- Fin Utilisation de addCustomControls ---
    };

    const handleMouseMove = (options) => {
        if (!isMouseDown || !shape) return; // Vérifie aussi que shape existe
        canvas.selection = false;
        const pointer = canvas.getPointer(options.e);
        const width = Math.abs(pointer.x - origX);
        const height = Math.abs(pointer.y - origY);
        const distanceDragged = Math.sqrt(width * width + height * height);

        if (distanceDragged > 0) {
            isDragging = true;
        }

        // Adjust shape properties based on type and drag direction
        let newLeft = origX;
        let newTop = origY;
        let newWidth = width;
        let newHeight = height;

        if (pointer.x < origX) {
            newLeft = pointer.x;
        }
        if (pointer.y < origY) {
            newTop = pointer.y;
        }

        if (shapeType === 'circle') {
            const radius = Math.max(width, height) / 2;
            // Adjust position for circle origin (center)
            shape.set({
                left: origX, // Keep origin X
                top: origY,  // Keep origin Y
                radius: radius,
                originX: 'center',
                originY: 'center'
            });
             // Recalculate position based on radius and drag direction
             shape.set({
                 left: origX + (pointer.x < origX ? -radius : radius),
                 top: origY + (pointer.y < origY ? -radius : radius)
             });


        } else if (shapeType === 'hexagon') {
             const radius = Math.max(width, height) / 2;
             shape.set({
                 points: createRegularPolygon(origX, origY, 6, radius, 30).points,
                 left: origX, // Keep center origin
                 top: origY,  // Keep center origin
                 originX: 'center',
                 originY: 'center'
             });
             // Force recalculation of dimensions and position
             shape.setCoords();

        } else { // Rectangle, Triangle
            shape.set({
                left: newLeft,
                top: newTop,
                width: newWidth,
                height: newHeight,
                originX: 'left',
                originY: 'top'
            });
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
                canvas.remove(shape); // Remove if not dragged significantly
            }
        } else {
            if (shape && shapeAdded) {
                // Ensure final properties are set correctly before activating
                shape.setCoords(); // Recalculate coordinates and dimensions
                canvas.setActiveObject(shape);
                saveCanvasState(canvas);
                activatePanMode(); // Switch back to pan mode after adding
                canvas.requestRenderAll();
            } else {
                // If dragging started but shape wasn't added (e.g., too small)
                if (shape) {
                    canvas.remove(shape);
                }
            }
        }
        isDragging = false;
        canvas.isDrawingShape = false; // Reset drawing flag
        canvas.defaultCursor = 'default'; // Reset cursor
        canvas.removeShapeListeners(); // Clean up listeners
    };

    // Add listeners for shape drawing
    canvas.on('mouse:down', handleMouseDown);
    canvas.on('mouse:move', handleMouseMove);
    canvas.on('mouse:up', handleMouseUp);

    // Function to remove these specific listeners
    const removeListeners = () => {
        canvas.off('mouse:down', handleMouseDown);
        canvas.off('mouse:move', handleMouseMove);
        canvas.off('mouse:up', handleMouseUp);
    };
    canvas.removeShapeListeners = removeListeners; // Attach cleanup function to canvas
}

// --- Fonctions d'export pour chaque forme ---

export function addTriangle(canvas, activatePanMode) {
    if (canvas.removeShapeListeners) {
        canvas.removeShapeListeners(); // Clean up previous listeners if any
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
        canvas.removeShapeListeners(); // Clean up shape listeners before adding text
    }
    canvas.isDrawingShape = false; // Ensure shape drawing mode is off
    canvas.defaultCursor = 'default'; // Reset cursor

    const text = new fabric.Textbox('Texte', {
        left: canvas.getWidth() / 2,
        top: canvas.getHeight() / 2,
        fill: 'black', // Default color
        fontSize: 20,
        width: 200, // Initial width
        textAlign: 'left',
        originX: 'center',
        originY: 'center',
        splitByGrapheme: true, // Better handling of complex characters
    });

    // --- Utilisation de addCustomControls ---
    // Appelle la fonction centralisée pour ajouter les contrôles
    addCustomControls(text, canvas);
    // --- Fin Utilisation de addCustomControls ---

    canvas.add(text);
    canvas.setActiveObject(text);
    saveCanvasState(canvas);
    activatePanMode(); // Switch back to pan mode
    // canvas.removeShapeListeners(); // Not needed here as text doesn't use shape listeners
    canvas.requestRenderAll();
}

// --- Autres fonctions ---

export function deleteActiveObject(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.remove(activeObject);
        canvas.discardActiveObject(); // Deselect after removing
        saveCanvasState(canvas);
        canvas.requestRenderAll();
    }
}

export function changeObjectColor(canvas, color) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        // Handle groups specifically if needed (e.g., change fill of all rects in group)
        if (activeObject.type === 'group') {
            activeObject.forEachObject(obj => {
                // Apply color more selectively if needed
                obj.set('fill', color);
            });
        } else {
            activeObject.set('fill', color);
        }
        canvas.renderAll();
        saveCanvasState(canvas);
    }
}

// --- Fonctions Z-Order ---
// (Ces fonctions semblent correctes)
export function sendToBack(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.sendToBack(activeObject);
        canvas.discardActiveObject(); // Deselect to see the change clearly
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
