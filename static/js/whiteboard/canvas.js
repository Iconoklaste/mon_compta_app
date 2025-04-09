// canvas.js
import { saveCanvasState } from './state.js';
import { updateZoomIndicator } from './ui.js'; // Import updateZoomIndicator

export function initializeCanvas() {
    const canvas = new fabric.Canvas('canvas');

    // Function to calculate and set canvas dimensions
    function setCanvasDimensions() {
        // Get the navbar height dynamically
        const navbar = document.querySelector('.navbar');
        const navbarHeight = navbar ? parseFloat(getComputedStyle(navbar).height) : 0;

        // Get the sidebar width dynamically ONLY IF IT'S DISPLAYED
        let sidebarWidth = 0; // Default to 0
        const sidebar = document.querySelector('.sidebar');
        if (sidebar && getComputedStyle(sidebar).display !== 'none') { // <-- Vérifie si display n'est pas 'none'
            sidebarWidth = parseFloat(getComputedStyle(sidebar).width);
        }

        // Consider potential padding/margin on the main content area
        const mainContent = document.querySelector('.main-content');
        const contentStyle = mainContent ? getComputedStyle(mainContent) : null;
        const contentPaddingLeft = contentStyle ? parseFloat(contentStyle.paddingLeft) : 0;
        const contentPaddingRight = contentStyle ? parseFloat(contentStyle.paddingRight) : 0;
        const contentPaddingTop = contentStyle ? parseFloat(contentStyle.paddingTop) : 0;
        const contentPaddingBottom = contentStyle ? parseFloat(contentStyle.paddingBottom) : 0;

        // Calculate available width and height more precisely
        const availableWidth = window.innerWidth - sidebarWidth - contentPaddingLeft - contentPaddingRight; // sidebarWidth sera 0 si la sidebar est cachée
        const availableHeight = window.innerHeight - navbarHeight - contentPaddingTop - contentPaddingBottom;

        // Set canvas dimensions, ensuring they are not negative
        canvas.setWidth(Math.max(0, availableWidth));
        canvas.setHeight(Math.max(0, availableHeight));
        canvas.calcOffset();
        canvas.renderAll();
    }

    // Set initial canvas dimensions
    setCanvasDimensions();

    // Debounce resize event listener for performance
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(setCanvasDimensions, 150); // Adjust delay as needed (e.g., 150ms)
    });

    // Variables pour la gestion du déplacement du canvas
    let isDraggingCanvas = false;
    let isPanningMode = false; // Flag for panning mode

    // Gestion du déplacement du canvas (Panning)
    canvas.on('mouse:down', function(options) {
        // Ignore if in drawing mode, shape creation, or if clicking on an object when not in panning mode
        if (canvas.isDrawingMode || canvas.isDrawingShape || (options.target && !isPanningMode)) {
            canvas.selection = !isPanningMode; // Allow selection if not panning and clicking object
            isDraggingCanvas = false;
            return;
        }

        if (isPanningMode) {
            canvas.selection = false; // Disable selection during pan
            isDraggingCanvas = true;
            // canvas.isDragging = true; // Fabric's internal flag (might not be needed)
            canvas.lastPosX = options.e.clientX;
            canvas.lastPosY = options.e.clientY;
            canvas.setCursor('grabbing'); // Change cursor during pan drag
        } else {
            // If not panning mode and clicking on empty space, allow default selection behavior
            canvas.selection = true;
            isDraggingCanvas = false;
        }
    });

    canvas.on('mouse:move', function(options) {
        // Ignore if in drawing mode or shape creation
        if (canvas.isDrawingMode || canvas.isDrawingShape) {
            return;
        }
        // Perform panning if dragging is active
        if (isDraggingCanvas) {
            const e = options.e;
            const vpt = canvas.viewportTransform;
            if (vpt) { // Ensure viewportTransform exists
                vpt[4] += e.clientX - canvas.lastPosX;
                vpt[5] += e.clientY - canvas.lastPosY;
                canvas.requestRenderAll(); // More efficient than renderAll()
                canvas.lastPosX = e.clientX;
                canvas.lastPosY = e.clientY;
            }
        }
    });

    canvas.on('mouse:up', function(options) {
        if (isDraggingCanvas) {
            // Reset cursor only if panning was active
             canvas.setCursor(isPanningMode ? 'grab' : 'default');
        }
        // Reset dragging flags
        // canvas.isDragging = false; // Fabric's internal flag (might not be needed)
        isDraggingCanvas = false;
        // Re-enable selection if not in panning mode
        if (!isPanningMode) {
            canvas.selection = true;
        }
    });

    // Gestion du zoom
    canvas.on('mouse:wheel', function(opt) {
        const delta = opt.e.deltaY;
        let zoom = canvas.getZoom();
        const zoomFactor = 0.999; // Consistent zoom factor
        const minZoom = 0.01;
        const maxZoom = 20;
        const point = { x: opt.e.offsetX, y: opt.e.offsetY };

        zoom *= zoomFactor ** delta;
        if (zoom > maxZoom) zoom = maxZoom;
        if (zoom < minZoom) zoom = minZoom;

        canvas.zoomToPoint(point, zoom);
        opt.e.preventDefault();
        opt.e.stopPropagation();
        updateZoomIndicator(canvas); // Pass canvas here
    });

    // Save state after any modification
    // Consider debouncing or throttling these if they fire too rapidly
    canvas.on('object:modified', () => saveCanvasState(canvas));
    canvas.on('object:added', () => saveCanvasState(canvas));
    canvas.on('object:removed', () => saveCanvasState(canvas));

    // Save the initial state
    saveCanvasState(canvas);

    // Add functions to toggle modes
    canvas.togglePanningMode = function(enable) {
        isPanningMode = enable;
        canvas.defaultCursor = enable ? 'grab' : 'default';
        canvas.selection = !enable; // Disable selection when panning is enabled
        // Ensure cursor updates immediately if canvas is idle
        if (!isDraggingCanvas) {
             canvas.setCursor(canvas.defaultCursor);
        }
    };
    canvas.toggleSelectionMode = function(enable) {
        // This function might be redundant if panning mode controls selection
        // Keeping it simple: Selection is implicitly enabled when panning is disabled
        isPanningMode = !enable; // If selection mode implies disabling pan mode
        canvas.selection = enable;
        canvas.defaultCursor = 'default';
        if (!isDraggingCanvas) {
             canvas.setCursor(canvas.defaultCursor);
        }
        // Ensure panning mode is correctly disabled if selection is enabled
        if (enable) {
            canvas.togglePanningMode(false);
        }
    };

    return canvas;
}

// Zoom functions using consistent factors and zooming towards center
export function zoomIn(canvas) {
    let zoom = canvas.getZoom();
    const zoomStepFactor = 1.1; // Use a factor for consistent steps
    const maxZoom = 20;
    zoom *= zoomStepFactor;
    if (zoom > maxZoom) zoom = maxZoom;
    // Zoom towards the center of the current view
    canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
    updateZoomIndicator(canvas);
}

export function zoomOut(canvas) {
    let zoom = canvas.getZoom();
    const zoomStepFactor = 1 / 1.1; // Inverse factor for zooming out
    const minZoom = 0.01;
    zoom *= zoomStepFactor;
    if (zoom < minZoom) zoom = minZoom;
    // Zoom towards the center of the current view
    canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
    updateZoomIndicator(canvas);
}
