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

        // Get the sidebar width dynamically
        const sidebar = document.querySelector('.sidebar');
        const sidebarWidth = sidebar ? parseFloat(getComputedStyle(sidebar).width) : 0;

        const contentPadding = 0; // Padding of the content
        const availableWidth = window.innerWidth - contentPadding * 2;
        const availableHeight = window.innerHeight - navbarHeight - contentPadding * 2;

        canvas.setWidth(availableWidth);
        canvas.setHeight(availableHeight);
    }

    // Set initial canvas dimensions
    setCanvasDimensions();

    // Add a resize event listener to update canvas dimensions
    window.addEventListener('resize', setCanvasDimensions);

    // Variables pour la gestion du déplacement du canvas
    let isDraggingCanvas = false;

    // Gestion du déplacement du canvas
    canvas.on('mouse:down', function(options) {
        if (options.target) {
            // Si on clique sur un objet, on ne déplace pas le canvas
            canvas.selection = true;
            isDraggingCanvas = false;
        } else {
            canvas.selection = false;
            isDraggingCanvas = true;
            canvas.isDragging = true;
            canvas.lastPosX = options.e.clientX;
            canvas.lastPosY = options.e.clientY;
        }
    });

    canvas.on('mouse:move', function(options) {
        if (isDraggingCanvas && canvas.isDragging) {
            const e = options.e;
            const vpt = canvas.viewportTransform;
            vpt[4] += e.clientX - canvas.lastPosX;
            vpt[5] += e.clientY - canvas.lastPosY;
            canvas.requestRenderAll();
            canvas.lastPosX = e.clientX;
            canvas.lastPosY = e.clientY;
        }
    });

    canvas.on('mouse:up', function(options) {
        canvas.isDragging = false;
        isDraggingCanvas = false;
        canvas.selection = true;
    });

    // Gestion du zoom
    canvas.on('mouse:wheel', function(opt) {
        var delta = opt.e.deltaY;
        var zoom = canvas.getZoom();
        zoom *= 0.999 ** delta;
        if (zoom > 20) zoom = 20;
        if (zoom < 0.01) zoom = 0.01;
        canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
        opt.e.preventDefault();
        opt.e.stopPropagation();
        updateZoomIndicator(canvas); // Pass canvas here
    });

    // Save state after any modification
    canvas.on('object:modified', () => saveCanvasState(canvas)); // Pass canvas here
    canvas.on('object:added', () => saveCanvasState(canvas)); // Pass canvas here
    canvas.on('object:removed', () => saveCanvasState(canvas)); // Pass canvas here

    return canvas;
}

export function zoomIn(canvas) {
    let zoom = canvas.getZoom();
    zoom *= 1.1;
    if (zoom > 20) zoom = 20;
    canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
    updateZoomIndicator(canvas); // Pass canvas here
}

export function zoomOut(canvas) {
    let zoom = canvas.getZoom();
    zoom *= 0.9;
    if (zoom < 0.01) zoom = 0.01;
    canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
    updateZoomIndicator(canvas); // Pass canvas here
}
