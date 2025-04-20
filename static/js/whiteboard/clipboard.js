// static/js/whiteboard/clipboard.js
import { saveCanvasState } from './state.js';
// --- SUPPRIMER CET IMPORT ---
// import { addCustomControls } from './controls.js';

/**
 * Gère le collage d'images depuis le presse-papiers sur le canvas Fabric.
 * @param {ClipboardEvent} event L'événement de collage.
 * @param {fabric.Canvas} canvas L'instance du canvas Fabric.
 */
export function handlePaste(event, canvas) {
    // ... (début de la fonction inchangé) ...

    const items = (event.clipboardData || event.originalEvent.clipboardData)?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
        const item = items[i];

        if (item.kind === 'file' && item.type.startsWith('image/')) {
            event.preventDefault();
            const blob = item.getAsFile();
            if (!blob) continue;
            const objectURL = URL.createObjectURL(blob);

            fabric.Image.fromURL(objectURL, (img) => {
                if (!img) {
                    URL.revokeObjectURL(objectURL);
                    console.error("Failed to load image from clipboard blob.");
                    return;
                }
                console.log("Image loaded from clipboard:", img);

                // --- Positionnement et Redimensionnement (inchangé) ---
                const canvasCenter = canvas.getCenter();
                const maxDim = Math.min(canvas.width * 0.8, canvas.height * 0.8, 500);
                if (img.width > maxDim || img.height > maxDim) {
                    const scaleFactor = Math.min(maxDim / img.width, maxDim / img.height);
                    img.scale(scaleFactor);
                }
                img.set({
                    left: canvasCenter.left,
                    top: canvasCenter.top,
                    originX: 'center',
                    originY: 'center',
                });
                // --- Fin Positionnement et Redimensionnement ---

                // --- SUPPRIMER CETTE LIGNE ---
                // addCustomControls(img, canvas);

                canvas.add(img);
                canvas.setActiveObject(img);
                canvas.requestRenderAll();
                saveCanvasState(canvas);
                URL.revokeObjectURL(objectURL);
            }, { crossOrigin: 'anonymous' });
            break;
        }
    }
}
