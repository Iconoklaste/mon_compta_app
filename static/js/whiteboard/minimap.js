// static/js/whiteboard/minimap.js

// --- TODO: MINIMAP PERFORMANCE ---
// Ce module est actuellement désactivé dans main.js en raison de scintillements.
// L'utilisation de toDataURL dans updateMinimap est la cause probable.
// Envisager d'utiliser ctx.drawImage(mainCanvas.getElement(), ...) comme alternative.
// Voir le TODO plus détaillé dans main.js.
// --- FIN TODO ---

let mainCanvas = null;
let minimapCanvas = null;
let minimapCtx = null;
let minimapContainer = null;
let scale = 1;
let minimapWidth = 0;
let minimapHeight = 0;

// Viewport rectangle details (in minimap coordinates RELATIVE TO THE FULL CANVAS CONTENT)
let viewportRectRelative = { x: 0, y: 0, width: 0, height: 0 };
// Viewport rectangle details (DRAWN coordinates on the minimap canvas)
let viewportRectDrawn = { x: 0, y: 0, width: 0, height: 0 };

// Offset used to draw the main canvas image onto the minimap
let drawOffsetX = 0;
let drawOffsetY = 0;

// Dragging state
let isDragging = false;
let dragOffsetX = 0; // Offset within the RED rectangle
let dragOffsetY = 0;

/**
 * Calculates the scale factor for the minimap.
 */
function calculateScale() {
    if (!mainCanvas || !minimapWidth) return 1;
    // Calculate scale based on width, maintain aspect ratio
    // Consider using Math.min if you want it to fit based on height too
    return minimapWidth / mainCanvas.getWidth();
}

/**
 * Calculates the relative viewport rectangle and the drawing offset.
 * Returns the calculated drawing offset.
 */
function calculateViewportAndOffset() {
    if (!mainCanvas) return { drawX: 0, drawY: 0 };

    const zoom = mainCanvas.getZoom();
    const vpt = mainCanvas.viewportTransform;
    const canvasWidth = mainCanvas.getWidth();
    const canvasHeight = mainCanvas.getHeight();

    // Dimensions of the visible area on the main canvas
    const viewWidth = canvasWidth / zoom;
    const viewHeight = canvasHeight / zoom;

    // Top-left corner of the visible area on the main canvas (absolute coords)
    const viewX = vpt[4] ? -vpt[4] / zoom : 0;
    const viewY = vpt[5] ? -vpt[5] / zoom : 0;

    // 1. Calculate viewport relative to the full canvas content (scaled)
    viewportRectRelative.x = viewX * scale;
    viewportRectRelative.y = viewY * scale;
    viewportRectRelative.width = viewWidth * scale;
    viewportRectRelative.height = viewHeight * scale;

    // 2. Calculate the center of this relative viewport rectangle
    const rectCenterX = viewportRectRelative.x + viewportRectRelative.width / 2;
    const rectCenterY = viewportRectRelative.y + viewportRectRelative.height / 2;

    // 3. Calculate the center of the minimap canvas
    const minimapCenterX = minimapWidth / 2;
    const minimapCenterY = minimapHeight / 2;

    // 4. Calculate the offset needed to center the viewport rectangle
    // This offset is where the top-left (0,0) of the main canvas image
    // should be drawn on the minimap canvas.
    drawOffsetX = minimapCenterX - rectCenterX;
    drawOffsetY = minimapCenterY - rectCenterY;

    // 5. Calculate the actual drawing coordinates for the viewport rectangle
    viewportRectDrawn.x = viewportRectRelative.x + drawOffsetX;
    viewportRectDrawn.y = viewportRectRelative.y + drawOffsetY;
    viewportRectDrawn.width = viewportRectRelative.width; // Width/Height don't change
    viewportRectDrawn.height = viewportRectRelative.height;

    return { drawX: drawOffsetX, drawY: drawOffsetY };
}


/**
 * Draws the viewport rectangle on the minimap at its DRAWN position.
 */
function drawMinimapViewportRectangle() {
    if (!minimapCtx) return;

    // Draw the rectangle at its calculated drawn coordinates
    minimapCtx.strokeStyle = 'red';
    // Adjust line width based on scale to keep it visually consistent
    // Use Math.max to prevent excessively thin lines at high zoom
    minimapCtx.lineWidth = Math.max(0.5, 1 / scale);
    minimapCtx.strokeRect(
        viewportRectDrawn.x,
        viewportRectDrawn.y,
        viewportRectDrawn.width,
        viewportRectDrawn.height
    );
}

/**
 * Updates the minimap content by drawing a scaled version of the main canvas,
 * applying an offset to center the viewport.
 */
export function updateMinimap() {
    if (!mainCanvas || !minimapCtx || !minimapCanvas) return;

    scale = calculateScale(); // Recalculate scale

    // Calculate the viewport and the necessary drawing offset BEFORE drawing
    const { drawX, drawY } = calculateViewportAndOffset();

    // Clear the minimap
    minimapCtx.clearRect(0, 0, minimapWidth, minimapHeight);

    // Generate data URL (consider quality/performance trade-offs)
    const dataURLOptions = {
        format: 'png',
        quality: 0.6,
        // multiplier: scale // Using multiplier might be faster but check quality
    };
    const dataURL = mainCanvas.toDataURL(dataURLOptions);

    const img = new Image();
    img.onload = () => {
        // Clear again before drawing image (in case of async delay)
        minimapCtx.clearRect(0, 0, minimapWidth, minimapHeight);

        // Calculate image dimensions based on scale
        const imgWidth = mainCanvas.getWidth() * scale;
        const imgHeight = mainCanvas.getHeight() * scale;

        // --- MODIFICATION: Draw the scaled image using the calculated offset ---
        minimapCtx.drawImage(img, drawX, drawY, imgWidth, imgHeight);

        // Draw the viewport rectangle on top at its calculated DRAWN position
        drawMinimapViewportRectangle();
    };
    img.onerror = (err) => {
        console.error("Error loading minimap image:", err);
    };
    img.src = dataURL;
}


// --- Interaction Handling ---

function handleMouseDown(e) {
    const rect = minimapCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Check if click is inside the DRAWN viewport rectangle
    if (
        mouseX >= viewportRectDrawn.x &&
        mouseX <= viewportRectDrawn.x + viewportRectDrawn.width &&
        mouseY >= viewportRectDrawn.y &&
        mouseY <= viewportRectDrawn.y + viewportRectDrawn.height
    ) {
        isDragging = true;
        // Calculate offset relative to the DRAWN rectangle's top-left corner
        dragOffsetX = mouseX - viewportRectDrawn.x;
        dragOffsetY = mouseY - viewportRectDrawn.y;
        minimapCanvas.style.cursor = 'grabbing';
        e.preventDefault(); // Prevent text selection during drag
    } else {
         isDragging = false; // Ensure dragging stops if clicking outside
    }
}

function handleMouseMove(e) {
    if (!isDragging || !mainCanvas) return;

    const rect = minimapCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // 1. Calculate the desired top-left corner of the DRAWN rectangle on the minimap
    const targetDrawnX = mouseX - dragOffsetX;
    const targetDrawnY = mouseY - dragOffsetY;

    // 2. Convert this DRAWN position back to the RELATIVE position
    //    (relative to the full canvas content) by subtracting the current drawing offset.
    const targetRelativeX = targetDrawnX - drawOffsetX;
    const targetRelativeY = targetDrawnY - drawOffsetY;

    // 3. Convert this RELATIVE minimap position back to the main canvas's absolute coordinates
    const targetCanvasX = targetRelativeX / scale;
    const targetCanvasY = targetRelativeY / scale;

    // 4. Pan the main canvas so that this point becomes the top-left corner
    //    Use viewportTransform directly for potentially smoother updates during drag
    const newVpt = mainCanvas.viewportTransform.slice(); // Create a copy
    newVpt[4] = -targetCanvasX * mainCanvas.getZoom();
    newVpt[5] = -targetCanvasY * mainCanvas.getZoom();
    mainCanvas.setViewportTransform(newVpt);

    // Note: setViewportTransform triggers 'after:render', which calls the debounced updateMinimap.
    // For potentially smoother dragging feedback, we could manually call parts of the update here,
    // but let's rely on the debounced update first.
    // OPTIONAL: Force immediate redraw of minimap rectangle for smoother feedback
    // calculateViewportAndOffset(); // Recalculate positions based on new main canvas state
    // minimapCtx.clearRect(0, 0, minimapWidth, minimapHeight); // Quick clear
    // minimapCtx.drawImage(...); // Redraw background (might be slow)
    // drawMinimapViewportRectangle(); // Redraw rectangle immediately
}

function handleMouseUpOrLeave(e) {
    if (isDragging) {
        isDragging = false;
        minimapCanvas.style.cursor = 'grab';
        // Ensure a final update after dragging stops
        updateMinimap();
    }
}

/**
 * Initializes the minimap.
 * @param {fabric.Canvas} canvasInstance The main Fabric.js canvas instance.
 */
export function initMinimap(canvasInstance) {
    mainCanvas = canvasInstance;
    minimapContainer = document.getElementById('minimap-container');
    minimapCanvas = document.getElementById('minimap-canvas');

    if (!minimapContainer || !minimapCanvas || !mainCanvas) {
        console.error("Minimap elements or main canvas not found!");
        return;
    }

    minimapCtx = minimapCanvas.getContext('2d');

    // Set minimap canvas dimensions based on container size
    minimapWidth = minimapContainer.clientWidth;
    minimapHeight = minimapContainer.clientHeight;
    minimapCanvas.width = minimapWidth;
    minimapCanvas.height = minimapHeight;

    scale = calculateScale();

    // Add event listeners for dragging the viewport
    minimapCanvas.addEventListener('mousedown', handleMouseDown);
    // Listen on window/document for mousemove/mouseup to handle dragging outside the minimap
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUpOrLeave);
    // Keep mouseleave on the canvas itself to reset cursor if mouse leaves while NOT dragging
    minimapCanvas.addEventListener('mouseleave', (e) => {
        if (!isDragging) {
            minimapCanvas.style.cursor = 'grab';
        }
    });

    console.log("Minimap initialized.");

    // Initial draw
    updateMinimap();
}
