// static/js/whiteboard/canvas.js
import { saveCanvasState } from './state.js';
import { updateZoomIndicator } from './ui.js';
import { getCurrentMode } from './mode-manager.js'; // Importer pour vérifier le mode actuel

export function initializeCanvas() {
    const canvasContainer = document.getElementById('canvas-container'); // Assurez-vous d'avoir un conteneur
    if (!canvasContainer) {
        console.error("Conteneur de canvas 'canvas-container' non trouvé !");
        return null; // Ou gérer l'erreur autrement
    }
    const canvasElement = document.getElementById('canvas');
     if (!canvasElement) {
        console.error("Élément canvas 'canvas' non trouvé !");
        return null;
    }
    const canvas = new fabric.Canvas(canvasElement);


    // --- Gestion Redimensionnement ---
    function setCanvasDimensions() {
        const navbar = document.querySelector('.navbar');
        const navbarHeight = navbar ? parseFloat(getComputedStyle(navbar).height) : 0;
        let sidebarWidth = 0;
        const sidebar = document.querySelector('.sidebar');
        if (sidebar && getComputedStyle(sidebar).display !== 'none') {
            sidebarWidth = parseFloat(getComputedStyle(sidebar).width);
        }
        const mainContent = document.querySelector('.main-content') || canvasContainer.parentElement; // Fallback au parent
        const contentStyle = mainContent ? getComputedStyle(mainContent) : null;
        const contentPaddingLeft = contentStyle ? parseFloat(contentStyle.paddingLeft) : 0;
        const contentPaddingRight = contentStyle ? parseFloat(contentStyle.paddingRight) : 0;
        const contentPaddingTop = contentStyle ? parseFloat(contentStyle.paddingTop) : 0;
        const contentPaddingBottom = contentStyle ? parseFloat(contentStyle.paddingBottom) : 0;

        // Utiliser la taille du conteneur si disponible, sinon la fenêtre
        const containerWidth = canvasContainer.offsetWidth;
        const containerHeight = canvasContainer.offsetHeight;

        // Calcul basé sur le conteneur (plus fiable si le conteneur a des dimensions définies)
        // Ou fallback sur window si le conteneur n'a pas de taille explicite (ex: 100%)
        const availableWidth = containerWidth || (window.innerWidth - sidebarWidth - contentPaddingLeft - contentPaddingRight);
        const availableHeight = containerHeight || (window.innerHeight - navbarHeight - contentPaddingTop - contentPaddingBottom);

        canvas.setWidth(Math.max(0, availableWidth));
        canvas.setHeight(Math.max(0, availableHeight));
        canvas.calcOffset(); // Recalculer l'offset du canvas
        canvas.renderAll();
    }

    setCanvasDimensions();
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(setCanvasDimensions, 150);
    });
    // Observer les changements de taille du conteneur si nécessaire (plus robuste)
    if (typeof ResizeObserver !== 'undefined') {
        const resizeObserver = new ResizeObserver(() => {
             clearTimeout(resizeTimeout);
             resizeTimeout = setTimeout(setCanvasDimensions, 50); // Délai plus court pour ResizeObserver
        });
        resizeObserver.observe(canvasContainer);
    }


    // --- Gestion Panning & Sélection ---
    let isPanning = false; // Flag spécifique pour le pan de l'arrière-plan
    let lastPosX, lastPosY;

    canvas.on('mouse:down', function(options) {
        const mode = getCurrentMode();
        const target = options.target; // L'objet cliqué (ou null si fond)
        const e = options.e;

        if (mode === 'pan') {
            // --- LOGIQUE SPÉCIFIQUE AU MODE PAN ---
            if (!target) {
                // 1. Clic sur le FOND en mode PAN: Démarrer le panning du canvas
                isPanning = true;
                canvas.selection = false; // Assurer que la sélection est désactivée
                lastPosX = e.clientX;
                lastPosY = e.clientY;
                canvas.setCursor('grabbing'); // Curseur indiquant le déplacement
                canvas.requestRenderAll();
            } else {
                // 2. Clic sur un OBJET en mode PAN: NE RIEN FAIRE (empêcher la sélection/déplacement)
                isPanning = false; // Pas de panning de fond
                // On ne change pas canvas.selection (il est déjà false grâce au mode-manager)
                // On peut garder le curseur 'grab' pour indiquer qu'on est toujours en mode pan
                canvas.setCursor('grab');
                // Important: En ne faisant rien ici, on empêche Fabric de gérer
                // l'événement pour la sélection ou le déplacement de l'objet 'target'.
            }
        } else if (mode === 'select') {
            // --- LOGIQUE DU MODE SELECT ---
            // Laisser Fabric gérer nativement la sélection et le déplacement des objets.
            // canvas.selection est déjà 'true' (défini par mode-manager).
            isPanning = false; // Assurer que le flag de panning de fond est désactivé.
        } else {
            // --- AUTRES MODES (Draw, Shape, Text) ---
            // La sélection est normalement désactivée par mode-manager.
            // Les listeners spécifiques à ces modes (ex: dessin de forme) gèrent le clic.
            isPanning = false;
        }
    });

    canvas.on('mouse:move', function(options) {
        // Si on est en train de panner l'arrière-plan
        if (isPanning) {
            const e = options.e;
            const vpt = canvas.viewportTransform;
            if (vpt) {
                vpt[4] += e.clientX - lastPosX;
                vpt[5] += e.clientY - lastPosY;
                canvas.requestRenderAll(); // Utiliser requestRenderAll pour la performance
                lastPosX = e.clientX;
                lastPosY = e.clientY;
            }
        }
        // Le déplacement d'objet est géré nativement par Fabric.js quand canvas.selection = true
    });

    canvas.on('mouse:up', function(options) {
        // Si on terminait un pan de l'arrière-plan
        if (isPanning) {
            isPanning = false;
            const mode = getCurrentMode();
            // Rétablir le curseur approprié pour le mode pan
            if (mode === 'pan') {
                 canvas.setCursor('grab');
            }
            // La sélection reste désactivée si on était en pan de fond,
            // mais sera réactivée si on change de mode via setMode
            canvas.requestRenderAll();
        }
        // Si on a déplacé un objet, le curseur devrait être géré par les événements de l'objet ou Fabric
        // S'assurer que la sélection est réactivée si on n'est plus en pan (au cas où)
        // Note: Le modeManager gère déjà l'état de canvas.selection lors du changement de mode.
        // if (!isPanning && getCurrentMode() !== 'draw' && getCurrentMode() !== 'shape' && getCurrentMode() !== 'text') {
        //     canvas.selection = true;
        // }
    });

    // --- Gestion Zoom ---
    canvas.on('mouse:wheel', function(opt) {
        const delta = opt.e.deltaY;
        let zoom = canvas.getZoom();
        const zoomFactor = 0.99; // Ajusté pour un zoom plus doux
        const minZoom = 0.05;
        const maxZoom = 30;
        const point = { x: opt.e.offsetX, y: opt.e.offsetY };

         // Diminuez la valeur '100' pour augmenter la vitesse.
        // Essayez par exemple 80, 60, ou 50 pour un zoom plus rapide.
        // Augmentez-la pour ralentir le zoom.
        const speedDivisor = 10; // <-- MODIFIEZ CETTE VALEUR (initialement 100)
        zoom *= zoomFactor ** (delta / speedDivisor); // Normaliser delta pour un zoom plus cohérent

        zoom *= zoomFactor ** (delta / 100); // Normaliser delta pour un zoom plus cohérent
        if (zoom > maxZoom) zoom = maxZoom;
        if (zoom < minZoom) zoom = minZoom;

        canvas.zoomToPoint(point, zoom);
        updateZoomIndicator(canvas); // Mettre à jour l'indicateur
        opt.e.preventDefault();
        opt.e.stopPropagation();
    });

    // --- Sauvegarde sur modification ---
    // Utiliser un debounce léger pour éviter les sauvegardes excessives lors de déplacements rapides
    let saveTimeout;
    const debouncedSave = () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => saveCanvasState(canvas), 300); // 300ms delay
    };

    canvas.on('object:modified', debouncedSave);
    canvas.on('object:added', () => saveCanvasState(canvas)); // Sauvegarde immédiate à l'ajout
    canvas.on('object:removed', () => saveCanvasState(canvas)); // Sauvegarde immédiate à la suppression
    // Sauvegarde après dessin libre (path:created)
    canvas.on('path:created', debouncedSave);


    // --- Fonctions de contrôle exposées (si nécessaire) ---

    /**
     * Active ou désactive le mode de panning de l'arrière-plan.
     * Appelé par le modeManager.
     * @param {boolean} enable - True pour activer, false pour désactiver.
     */
    canvas.togglePanningMode = function(enable) {
        // Cette fonction ne change que le comportement du pan de fond.
        // Le modeManager gère le curseur et canvas.selection.
        // On pourrait stocker l'état ici si nécessaire, mais isPanning le fait déjà.
        if (!enable && isPanning) {
            // Si on désactive pendant un pan en cours (rare, mais possible)
            isPanning = false;
            // Le curseur sera réinitialisé par le modeManager
        }
        // console.log(`Background Panning ${enable ? 'Enabled' : 'Disabled'}`);
    };

    // La fonction toggleSelectionMode est supprimée car gérée par le modeManager.

    // Sauvegarder l'état initial (après chargement potentiel)
    // saveCanvasState(canvas); // Déplacé dans loadData pour être après le chargement



    return canvas;
}

// --- Fonctions Zoom (exportées) ---
export function zoomIn(canvas) {
    let zoom = canvas.getZoom();
    const zoomStepFactor = 1.2; // Augmenté pour un pas plus visible
    const maxZoom = 30;
    zoom *= zoomStepFactor;
    if (zoom > maxZoom) zoom = maxZoom;
    canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
    updateZoomIndicator(canvas);
}

export function zoomOut(canvas) {
    let zoom = canvas.getZoom();
    const zoomStepFactor = 1 / 1.2;
    const minZoom = 0.05;
    zoom *= zoomStepFactor;
    if (zoom < minZoom) zoom = minZoom;
    canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
    updateZoomIndicator(canvas);
}
