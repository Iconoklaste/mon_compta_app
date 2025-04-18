// static/js/whiteboard/clipboard.js
import { saveCanvasState } from './state.js';
import { addCustomControls } from './controls.js'; // Assure-toi que controls.js exporte bien cette fonction

/**
 * Gère le collage d'images depuis le presse-papiers sur le canvas Fabric.
 * @param {ClipboardEvent} event L'événement de collage.
 * @param {fabric.Canvas} canvas L'instance du canvas Fabric.
 */
export function handlePaste(event, canvas) {
    // Vérifier si un champ de saisie est actif pour ne pas interférer
    const activeElement = document.activeElement;
    const isInputFocused = activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.isContentEditable);

    if (isInputFocused) {
        console.log("Paste ignored: Input field is focused.");
        return; // Ne rien faire si on colle dans un input/textarea/contentEditable
    }

    const items = (event.clipboardData || event.originalEvent.clipboardData)?.items;
    if (!items) return;

    // Parcourir les éléments du presse-papiers
    for (let i = 0; i < items.length; i++) {
        const item = items[i];

        // Vérifier si c'est un fichier image
        if (item.kind === 'file' && item.type.startsWith('image/')) {
            event.preventDefault(); // Empêcher le comportement par défaut du navigateur

            const blob = item.getAsFile();
            if (!blob) continue;

            const objectURL = URL.createObjectURL(blob);

            // Charger l'image dans Fabric.js
            fabric.Image.fromURL(objectURL, (img) => {
                if (!img) {
                    URL.revokeObjectURL(objectURL);
                    console.error("Failed to load image from clipboard blob.");
                    return;
                }

                console.log("Image loaded from clipboard:", img);

                // --- Positionnement et Redimensionnement ---
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

                // Ajouter les contrôles personnalisés
                addCustomControls(img, canvas); // Appelle la fonction importée

                canvas.add(img);
                canvas.setActiveObject(img);
                canvas.requestRenderAll();
                saveCanvasState(canvas); // Sauvegarder l'état

                // Libérer l'URL de l'objet
                URL.revokeObjectURL(objectURL);

            }, { crossOrigin: 'anonymous' });

            // On ne traite que la première image trouvée
            break;
        }
    }
}
