// static/js/whiteboard/ui.js
import { changeObjectColor, addRectangle, addCircle, addTriangle, addHexagon, addText } from './objects.js'; // Import shape/text functions
import { saveWhiteboard, loadCanvas } from './state.js';
import { zoomIn, zoomOut } from './canvas.js';
import { saveCanvasState } from './state.js';
import { getCurrentMode } from './mode-manager.js'; // Import pour vérifier le mode si nécessaire

// Références aux boutons de mode (déclarées en dehors pour être accessibles par updateModeButtonsUI)
let selectionButton, panButton, freeDrawButton;
let addRectButton, addCircleButton, addTriangleButton, addHexagonButton, addTextButton; // Ajout des boutons de forme/texte

/**
 * Initialise les éléments généraux de l'interface utilisateur.
 * @param {fabric.Canvas} canvas
 * @param {string} projetId
 */
export function initializeUI(canvas, projetId) {
    const fontSizeSelector = document.getElementById('font-size-selector');
    const fontFamilySelector = document.getElementById('font-family-selector');

    // --- Gestion Font Size ---
    fontSizeSelector.addEventListener('change', () => {
        const selectedFontSize = parseInt(fontSizeSelector.value, 10);
        const activeObject = canvas.getActiveObject();
        const target = getTargetTextbox(activeObject);
        if (target) {
            // Appliquer au texte sélectionné ou à tout le textbox
            if (target.selectionStart !== target.selectionEnd) {
                target.setSelectionStyles({ fontSize: selectedFontSize }, target.selectionStart, target.selectionEnd);
            } else {
                target.set('fontSize', selectedFontSize);
            }
            canvas.renderAll();
            saveCanvasState(canvas); // Sauvegarder après modification
        }
    });

    // --- Gestion Font Family ---
    fontFamilySelector.addEventListener('change', async () => {
        const selectedFontFamily = fontFamilySelector.value;
        const activeObject = canvas.getActiveObject();
        const target = getTargetTextbox(activeObject);
        if (target) {
            try {
                // Vérifier et charger la police si nécessaire
                if (!document.fonts.check(`12px ${selectedFontFamily}`)) {
                    await document.fonts.load(`12px ${selectedFontFamily}`);
                }
                // Appliquer au texte sélectionné ou à tout le textbox
                if (target.selectionStart !== target.selectionEnd) {
                    target.setSelectionStyles({ fontFamily: selectedFontFamily }, target.selectionStart, target.selectionEnd);
                } else {
                    target.set('fontFamily', selectedFontFamily);
                }
                canvas.renderAll();
                saveCanvasState(canvas); // Sauvegarder après modification
            } catch (error) {
                console.error(`Erreur lors du chargement de la police ${selectedFontFamily}:`, error);
                // Informer l'utilisateur ?
            }
        }
    });

    // --- Boutons Zoom & Sauvegarde ---
    document.getElementById('zoom-in')?.addEventListener('click', () => zoomIn(canvas));
    document.getElementById('zoom-out')?.addEventListener('click', () => zoomOut(canvas));
    document.getElementById('saveButton')?.addEventListener('click', () => saveWhiteboard(canvas, projetId));

    // --- Mise à jour initiale indicateur de zoom ---
    updateZoomIndicator(canvas);
}

/**
 * Initialise les boutons de contrôle de mode (Select, Pan, Draw, Shapes, Text).
 * @param {fabric.Canvas} canvas - Instance du canvas.
 * @param {function(import('./mode-manager.js').InteractionMode): void} setModeCallback - Fonction pour changer le mode via le modeManager.
 */
export function initializeModeButtons(canvas, setModeCallback) {
    selectionButton = document.getElementById('selection-button');
    panButton = document.getElementById('pan-button');
    freeDrawButton = document.getElementById('free-draw-button'); // Le bouton principal du dropdown

    addRectButton = document.getElementById('add-rect');
    addCircleButton = document.getElementById('add-circle');
    addTriangleButton = document.getElementById('add-triangle');
    addHexagonButton = document.getElementById('add-hexagon');
    addTextButton = document.getElementById('add-text');

    if (!selectionButton || !panButton || !freeDrawButton || !addRectButton || !addCircleButton || !addTriangleButton || !addHexagonButton || !addTextButton) {
        console.error("Impossible de trouver tous les boutons de mode ou d'ajout.");
        return;
    }

    // --- Fonction utilitaire pour retarder le changement de mode ---
    const delayedSetMode = (mode) => {
        // Utiliser un délai minimal (0ms fonctionne souvent, mais 1ms est plus sûr)
        // Cela pousse l'exécution au prochain "tick" de la boucle d'événements.
        setTimeout(() => {
            setModeCallback(mode);
        }, 1); // Délai de 1 milliseconde
    };
    // --- Fin fonction utilitaire ---

    // --- Écouteurs pour les modes principaux ---
    selectionButton.addEventListener('click', () => delayedSetMode('select')); // <-- MODIFIÉ
    panButton.addEventListener('click', () => delayedSetMode('pan'));         // <-- MODIFIÉ
    // Note: Le clic sur freeDrawButton ouvre le dropdown. Le mode 'draw' est activé
    // via brush-manager.js lors de la sélection d'un pinceau (à modifier aussi).

    // --- Callback pour revenir en mode sélection après ajout ---
    const returnToSelectMode = () => delayedSetMode('select'); // <-- MODIFIÉ (Utiliser le délai ici aussi)

    // --- Écouteurs pour l'ajout de formes/texte ---
    addRectButton.addEventListener('click', () => {
        delayedSetMode('shape'); // <-- MODIFIÉ
        addRectangle(canvas, returnToSelectMode);
    });
    addCircleButton.addEventListener('click', () => {
        delayedSetMode('shape'); // <-- MODIFIÉ
        addCircle(canvas, returnToSelectMode);
    });
    addTriangleButton.addEventListener('click', () => {
        delayedSetMode('shape'); // <-- MODIFIÉ
        addTriangle(canvas, returnToSelectMode);
    });
    addHexagonButton.addEventListener('click', () => {
        delayedSetMode('shape'); // <-- MODIFIÉ
        addHexagon(canvas, returnToSelectMode);
    });
    addTextButton.addEventListener('click', () => {
        delayedSetMode('text'); // <-- MODIFIÉ
        addText(canvas, returnToSelectMode);
    });
}
/**
 * Met à jour l'état visuel (classe .active) des boutons de mode principaux.
 * @param {import('./mode-manager.js').InteractionMode} activeMode - Le mode actuellement actif.
 */
export function updateModeButtonsUI(activeMode) {
    // Assurez-vous que les boutons ont été récupérés
    if (!selectionButton || !panButton || !freeDrawButton) {
        // console.warn("Tentative de mise à jour de l'UI des boutons avant initialisation.");
        // Tenter de les récupérer à nouveau peut être une solution de secours, mais idéalement l'ordre d'appel est correct.
        selectionButton = document.getElementById('selection-button');
        panButton = document.getElementById('pan-button');
        freeDrawButton = document.getElementById('free-draw-button');
        if (!selectionButton || !panButton || !freeDrawButton) return; // Sortir si toujours pas trouvés
    }

    // Utiliser classList.toggle pour une gestion propre
    selectionButton.classList.toggle('active', activeMode === 'select');
    panButton.classList.toggle('active', activeMode === 'pan');
    // Le bouton free-draw est actif si le mode est 'draw'
    freeDrawButton.classList.toggle('active', activeMode === 'draw');

    // Optionnel: Gérer l'état actif des boutons d'ajout de forme/texte s'ils doivent rester actifs pendant le dessin
    // addRectButton.classList.toggle('active', activeMode === 'shape'); // Probablement pas nécessaire car le mode 'shape' est transitoire
}


// --- Fonctions utilitaires existantes (inchangées ou légèrement modifiées) ---

function getTargetTextbox(activeObject) {
    if (!activeObject) return null;
    if (activeObject.type === 'textbox') {
        return activeObject;
    }
    // Gérer les groupes contenant un textbox (si nécessaire)
    if (activeObject.type === 'group') {
        // Chercher le premier textbox dans le groupe
        return activeObject.getObjects('textbox')[0] || null;
    }
    return null;
}

export function updateFontSizeSelector(canvas) {
    const fontSizeSelector = document.getElementById('font-size-selector');
    if (!fontSizeSelector) return;
    const activeObject = canvas.getActiveObject();
    const target = getTargetTextbox(activeObject);

    if (target) {
        // Gérer la sélection partielle : afficher la taille si elle est uniforme, sinon vide
        let currentSize = '';
        if (target.selectionStart !== target.selectionEnd) {
            const selectionStyles = target.getSelectionStyles(target.selectionStart, target.selectionEnd);
            // Vérifier si tous les styles de la sélection ont la même taille
            const allSameSize = selectionStyles.every(style => style.fontSize === selectionStyles[0].fontSize);
            if (allSameSize && selectionStyles.length > 0) {
                currentSize = selectionStyles[0].fontSize;
            }
        } else {
            currentSize = target.fontSize || ''; // Utiliser la taille globale de l'objet
        }
        fontSizeSelector.value = currentSize;
    } else {
        fontSizeSelector.value = ''; // Ou une valeur par défaut
    }
}

export async function updateFontFamilySelector(canvas) {
    const fontFamilySelector = document.getElementById('font-family-selector');
    if (!fontFamilySelector) return;
    const activeObject = canvas.getActiveObject();
    const target = getTargetTextbox(activeObject);

    if (target) {
        let currentFamily = '';
        // Gérer la sélection partielle
        if (target.selectionStart !== target.selectionEnd) {
            const selectionStyles = target.getSelectionStyles(target.selectionStart, target.selectionEnd);
            const allSameFamily = selectionStyles.every(style => style.fontFamily === selectionStyles[0].fontFamily);
            if (allSameFamily && selectionStyles.length > 0) {
                currentFamily = selectionStyles[0].fontFamily;
            }
        } else {
            currentFamily = target.fontFamily || '';
        }

        // Vérifier si la police est chargée avant de définir la valeur (évite les problèmes d'affichage)
        if (currentFamily && !document.fonts.check(`12px ${currentFamily}`)) {
            try {
                await document.fonts.load(`12px ${currentFamily}`);
            } catch (error) {
                console.warn(`Impossible de précharger la police ${currentFamily} pour le sélecteur.`);
            }
        }
        fontFamilySelector.value = currentFamily;

    } else {
        fontFamilySelector.value = ''; // Ou une valeur par défaut
    }
}

export function updateZoomIndicator(canvas) {
    const zoomIndicator = document.getElementById('zoom-indicator');
    if (zoomIndicator) {
        const zoomPercentage = Math.round(canvas.getZoom() * 100);
        zoomIndicator.textContent = `Zoom: ${zoomPercentage}%`;
    }
}

export function loadData(canvas, projetId) {
    fetch(`/load/${projetId}`)
        .then(response => {
            // ... (gestion des erreurs inchangée) ...
            if (!response.ok) {
                return response.json().catch(() => {
                    throw new Error(`Network response was not ok (${response.status})`);
                }).then(errData => {
                    throw new Error(errData.message || `Network response was not ok (${response.status})`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.whiteboard_data) {
                // ICI: On passe bien whiteboard_data à loadCanvas.
                // loadCanvas (dans state.js) gérera la nouvelle structure.
                loadCanvas(canvas, data.whiteboard_data);

                // Mettre à jour l'UI après le chargement (déjà présent)
                updateFontFamilySelector(canvas);
                updateFontSizeSelector(canvas);
                updateZoomIndicator(canvas); // Mettre à jour l'indicateur de zoom initial
            } else {
                console.log('No whiteboard data found for this project.');
                // Initialiser un canvas vide ou afficher un message
                // Appeler loadCanvas avec null pour initialiser un canvas vide
                // et laisser loadCanvas gérer l'initialisation des piles undo/redo.
                loadCanvas(canvas, null);
            }
        })
        .catch((error) => {
            console.error('Error loading whiteboard data:', error);
            alert(`Erreur lors du chargement du tableau blanc: ${error.message}`);
        });
}

