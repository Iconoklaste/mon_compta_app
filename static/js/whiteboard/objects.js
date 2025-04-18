// static/js/whiteboard/objects.js
// import { addCustomControls } from './controls.js'; // Utilise la fonction centralisée
import { saveCanvasState } from './state.js';

// --- Fonction interne pour créer des polygones réguliers ---
function createRegularPolygon(centerX, centerY, sides, radius, angle = 0, options = {}) {
    const points = [];
    const angleStep = (Math.PI * 2) / sides;
    const startAngle = (angle * Math.PI / 180); // Convertir l'angle initial en radians

    for (let i = 0; i < sides; i++) {
        points.push({
            x: centerX + radius * Math.cos(startAngle + i * angleStep),
            y: centerY + radius * Math.sin(startAngle + i * angleStep)
        });
    }
    return new fabric.Polygon(points, {
        originX: 'center', // Centre est souvent mieux pour les polygones
        originY: 'center',
        left: centerX,
        top: centerY,
        ...options // Fusionner les options fournies
    });
}


/**
 * Gère la logique de dessin interactif d'une forme (Rect, Circle, Triangle, Hexagon).
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 * @param {'rectangle' | 'circle' | 'triangle' | 'hexagon'} shapeType - Le type de forme.
 * @param {function(): void} onCompleteCallback - Callback à exécuter après l'ajout réussi.
 */
function addShape(canvas, shapeType, onCompleteCallback) {
    let isMouseDown = false;
    let isDragging = false;
    let origX, origY;
    let shape = null;
    let shapeAdded = false;
    const minDragDistance = 5; // Distance minimale pour considérer un ajout

    // Assurer que le flag interne est défini (utilisé par mode-manager cleanup)
    canvas.isDrawingShape = true;
    // Le curseur et la sélection sont déjà gérés par setMode('shape')

    const handleMouseDown = (options) => {
        // Ignorer si on clique sur un objet existant
        if (options.target) return;

        isMouseDown = true;
        isDragging = false;
        shapeAdded = false;
        const pointer = canvas.getPointer(options.e);
        origX = pointer.x;
        origY = pointer.y;

        // --- DÉBUT DE LA MODIFICATION ---

        // 1. Récupérer les valeurs actuelles des pickers et sliders
        let currentFillRaw = document.getElementById('fill-color-preview-icon')?.style.backgroundColor;
        let currentStrokeRaw = document.getElementById('stroke-color-preview-icon')?.style.backgroundColor;
        let currentStrokeWidthRaw = parseInt(document.getElementById('stroke-width-slider')?.value, 10);
        let currentOpacityRaw = parseFloat(document.getElementById('fill-transparency-slider')?.value);

        // 2. Définir les valeurs par défaut
        const defaultColor = 'black';
        const defaultStrokeWidth = 1;
        const defaultOpacity = 1;

        // 3. Valider les valeurs récupérées et appliquer les défauts si nécessaire
        const fillColor = (!currentFillRaw || currentFillRaw === 'transparent' || currentFillRaw === 'rgba(0, 0, 0, 0)')
                          ? defaultColor
                          : currentFillRaw;

        const strokeColor = (!currentStrokeRaw || currentStrokeRaw === 'transparent' || currentStrokeRaw === 'rgba(0, 0, 0, 0)')
                            ? defaultColor // Mettre noir par défaut aussi pour le contour
                            : currentStrokeRaw;

        // Si une couleur de contour est définie (même noir par défaut) et que l'épaisseur est <= 0 ou NaN, mettre 1.
        const strokeWidth = (strokeColor !== 'transparent' && strokeColor !== null && (isNaN(currentStrokeWidthRaw) || currentStrokeWidthRaw <= 0))
                            ? defaultStrokeWidth
                            : (currentStrokeWidthRaw || 0); // Sinon, utiliser la valeur ou 0 si invalide/null

        const fillOpacity = (isNaN(currentOpacityRaw) || currentOpacityRaw < 0 || currentOpacityRaw > 1)
                            ? defaultOpacity
                            : currentOpacityRaw;

        // 4. Utiliser les valeurs validées dans commonOptions
        const commonOptions = {
            left: origX,
            top: origY,
            originX: 'left',
            originY: 'top',
            fill: fillColor,         // Utilise la couleur validée
            stroke: strokeColor,     // Utilise la couleur validée
            strokeWidth: strokeWidth, // Utilise l'épaisseur validée
            opacity: fillOpacity,    // Applique l'opacité validée
            selectable: false,       // Non sélectionnable pendant le dessin
            evented: false,          // Ne déclenche pas d'événements pendant le dessin
        };

        // --- FIN DE LA MODIFICATION ---
        
        switch (shapeType) {
            case 'triangle':
                shape = new fabric.Triangle({ ...commonOptions, width: 0, height: 0 });
                break;
            case 'rectangle':
                shape = new fabric.Rect({ ...commonOptions, width: 0, height: 0 });
                break;
            case 'circle':
                // Pour le cercle, l'origine est gérée différemment pendant le dessin
                shape = new fabric.Circle({
                    ...commonOptions,
                    left: origX, // Sera ajusté dans mouse:move
                    top: origY,  // Sera ajusté dans mouse:move
                    radius: 0,
                    originX: 'center', // L'origine est au centre
                    originY: 'center'
                });
                break;
            case 'hexagon':
                // Créer un polygone avec rayon 0 initialement
                shape = createRegularPolygon(origX, origY, 6, 0, 30, { // 30 degrés pour pointer vers le haut
                     ...commonOptions,
                     // L'origine est déjà gérée par createRegularPolygon
                 });
                break;
        }

        if (shape) {
            canvas.add(shape); // Ajouter immédiatement pour le voir pendant le drag
            shapeAdded = true; // Marquer comme ajouté (sera retiré si drag trop court)
            canvas.requestRenderAll();
        }
    };

    const handleMouseMove = (options) => {
        if (!isMouseDown || !shape) return;

        const pointer = canvas.getPointer(options.e);
        const width = pointer.x - origX;
        const height = pointer.y - origY;
        const distanceDragged = Math.sqrt(width * width + height * height);

        if (!isDragging && distanceDragged > minDragDistance) {
            isDragging = true;
        }

        if (!isDragging) return; // Ne pas redessiner si on n'a pas assez bougé

        // Ajuster la forme en fonction du type et de la direction
        if (shapeType === 'circle') {
            const radius = Math.sqrt(width * width + height * height) / 2;
            // Le centre du cercle est le milieu entre le point de départ et le point actuel
            const centerX = origX + width / 2;
            const centerY = origY + height / 2;
            shape.set({
                left: centerX,
                top: centerY,
                radius: radius,
            });
        } else if (shapeType === 'hexagon') {
             const radius = Math.sqrt(width * width + height * height) / 2;
             const centerX = origX + width / 2;
             const centerY = origY + height / 2;
             // Recréer les points du polygone
             const newPoints = createRegularPolygon(centerX, centerY, 6, radius, 30).points;
             shape.set({
                 points: newPoints,
                 left: centerX, // Mettre à jour la position du centre
                 top: centerY,
             });
             shape.setCoords(); // Important pour recalculer la boîte englobante
        } else { // Rectangle, Triangle
            shape.set({
                left: width > 0 ? origX : pointer.x,
                top: height > 0 ? origY : pointer.y,
                width: Math.abs(width),
                height: Math.abs(height),
            });
        }

        canvas.requestRenderAll();
    };

    const handleMouseUp = (options) => {
        if (!isMouseDown) return; // Éviter double exécution
        isMouseDown = false;
        canvas.isDrawingShape = false; // Fin du mode dessin de forme interne

        if (shape && shapeAdded) {
            if (!isDragging) {
                // Si pas de drag significatif, retirer la forme
                canvas.remove(shape);
                shape = null;
                canvas.requestRenderAll();
            } else {
                // Finaliser la forme
                shape.set({
                    selectable: true, // Rendre sélectionnable
                    evented: true     // Rendre interactif
                });
                shape.setCoords(); // Assurer que les coordonnées sont à jour

                // Ajouter les contrôles personnalisés
                // addCustomControls(shape, canvas);

                canvas.setActiveObject(shape); // Sélectionner la nouvelle forme
                saveCanvasState(canvas);    // Sauvegarder l'état
                canvas.requestRenderAll();
                onCompleteCallback();       // Exécuter le callback (typiquement setMode('select'))
            }
        }

        // Nettoyer les listeners spécifiques à cette instance d'ajout de forme
        removeListeners();
        // Le mode global sera géré par onCompleteCallback via le modeManager
    };

    // Ajouter les listeners spécifiques au dessin de forme
    canvas.on('mouse:down', handleMouseDown);
    canvas.on('mouse:move', handleMouseMove);
    canvas.on('mouse:up', handleMouseUp);

    // Fonction pour supprimer ces listeners spécifiques
    const removeListeners = () => {
        canvas.off('mouse:down', handleMouseDown);
        canvas.off('mouse:move', handleMouseMove);
        canvas.off('mouse:up', handleMouseUp);
        // console.log("Shape drawing listeners removed.");
    };

    // Exposer la fonction de nettoyage sur le canvas pour le modeManager
    canvas.removeShapeListeners = removeListeners;
}

// --- Fonctions d'export pour chaque forme ---

export function addTriangle(canvas, onCompleteCallback) {
    if (canvas.removeShapeListeners) canvas.removeShapeListeners(); // Nettoyer les anciens listeners
    addShape(canvas, 'triangle', onCompleteCallback);
}

export function addRectangle(canvas, onCompleteCallback) {
    if (canvas.removeShapeListeners) canvas.removeShapeListeners();
    addShape(canvas, 'rectangle', onCompleteCallback);
}

export function addCircle(canvas, onCompleteCallback) {
    if (canvas.removeShapeListeners) canvas.removeShapeListeners();
    addShape(canvas, 'circle', onCompleteCallback);
}

export function addHexagon(canvas, onCompleteCallback) {
    if (canvas.removeShapeListeners) canvas.removeShapeListeners();
    addShape(canvas, 'hexagon', onCompleteCallback);
}

/**
 * Ajoute un objet Textbox au centre du canvas.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 * @param {function(): void} onCompleteCallback - Callback à exécuter après l'ajout.
 */
export function addText(canvas, onCompleteCallback) {
    // Nettoyer les listeners de forme potentiels (même si on est en mode 'text')
    if (canvas.removeShapeListeners) {
        canvas.removeShapeListeners();
    }
    canvas.isDrawingShape = false; // Assurer que ce flag est bien à false

    // --- MODIFICATION ICI ---
    // 1. Récupérer la couleur de remplissage brute depuis l'UI
    // let currentFillRaw = document.getElementById('fill-color-preview-icon')?.style.backgroundColor;
    const fillColor = 'black'; // Couleur par défaut si transparent



    // 3. Récupérer les autres styles (police, taille)
    const fontSize = parseInt(document.getElementById('font-size-selector')?.value, 10) || 24;
    const fontFamily = document.getElementById('font-family-selector')?.value || 'Arial';
    // --- FIN DE LA MODIFICATION ---

    // Créer l'objet texte
    const text = new fabric.Textbox('Texte', {
        left: canvas.getCenter().left, // Utiliser getCenter pour la position initiale
        top: canvas.getCenter().top,
        fill: fillColor,
        fontSize: fontSize,
        fontFamily: fontFamily,
        width: 200,
        textAlign: 'left',
        originX: 'center',
        originY: 'center',
        splitByGrapheme: true, // Meilleure gestion des caractères complexes
        // stroke: ..., // Ajouter le contour si nécessaire depuis les pickers
        // strokeWidth: ...,
    });

    // Ajouter les contrôles personnalisés
     // addCustomControls(text, canvas);

    canvas.add(text);
    canvas.setActiveObject(text);
    text.enterEditing(); // Entrer en mode édition immédiatement
    text.selectAll();    // Sélectionner tout le texte initial

    saveCanvasState(canvas);
    canvas.requestRenderAll();

    // Exécuter le callback immédiatement après l'ajout
    onCompleteCallback(); // Typiquement setMode('select')
}



// Fonction pour changer la couleur (peut être appelée par color-picker)
// Note: color-picker.js a déjà sa propre logique pour appliquer les couleurs
// Cette fonction pourrait être redondante ou servir à un autre usage.
export function changeObjectColor(canvas, color) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        // Gérer les groupes et les sélections multiples
        if (activeObject.type === 'activeSelection') {
            activeObject.forEachObject(obj => {
                // Appliquer sélectivement (ex: ne pas changer le fill d'une image)
                if (obj.set) obj.set('fill', color);
            });
        } else {
             // Appliquer sélectivement
             if (activeObject.set) activeObject.set('fill', color);
        }
        canvas.renderAll();
        saveCanvasState(canvas);
    }
}


// --- Fonctions Z-Order (inchangées) ---
export function sendToBack(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.sendToBack(activeObject);
        // canvas.discardActiveObject(); // Optionnel: désélectionner pour voir le changement
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}

export function bringToFront(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        canvas.bringToFront(activeObject);
        // canvas.discardActiveObject();
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}

export function sendBackward(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        // Gérer la sélection multiple
        if (activeObject.type === 'activeSelection') {
             // Envoyer tout le groupe vers l'arrière peut être complexe,
             // Envoyer chaque objet individuellement pourrait changer leur ordre relatif.
             // Solution simple: envoyer le groupe entier.
             canvas.sendBackwards(activeObject);
        } else {
            canvas.sendBackwards(activeObject);
        }
        // canvas.discardActiveObject();
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}

export function bringForward(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
         if (activeObject.type === 'activeSelection') {
             canvas.bringForward(activeObject);
         } else {
            canvas.bringForward(activeObject);
         }
        // canvas.discardActiveObject();
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }
}
