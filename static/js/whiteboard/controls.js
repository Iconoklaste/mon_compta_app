// static/js/whiteboard/controls.js
import { saveCanvasState } from './state.js';

/**
 * Supprime l'objet actif (ou les objets d'un groupe) du canvas.
 * Destinée à être appelée depuis la barre d'outils ou un autre bouton/action.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 * @returns {boolean} - True si un objet a été supprimé, false sinon.
 */
export function deleteActiveObject(canvas) {
    const activeObject = canvas.getActiveObject();
    if (activeObject) {
        // Fabric.js gère la suppression des groupes et de leurs objets internes
        canvas.remove(activeObject);
        canvas.discardActiveObject(); // Désélectionner après suppression
        canvas.requestRenderAll();
        saveCanvasState(canvas); // Sauvegarder l'état après suppression
        console.log("Objet actif supprimé via controls.js.");
        return true; // Indiquer que la suppression a eu lieu
    }
    console.log("Aucun objet actif à supprimer.");
    return false; // Indiquer qu'aucun objet n'a été supprimé
}

/**
 * Duplique l'objet cible, l'ajoute au canvas avec un décalage.
 * Destinée à être appelée depuis la barre d'outils.
 * @param {fabric.Object} target - L'objet à dupliquer (généralement l'objet actif).
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
export function duplicateObject(target, canvas) {
    if (!target || !canvas) {
        console.warn("Tentative de duplication sans cible ou sans canvas.");
        return;
    }

    target.clone((cloned) => {
        cloned.set({
            left: cloned.left + 20, // Décalage pour la visibilité
            top: cloned.top + 20,   // Décalage pour la visibilité
            evented: true,         // Assure que l'objet cloné est interactif
            // IMPORTANT: Pas besoin d'ajouter les anciens contrôles Fabric ici
        });

        // Note: Pas besoin d'appeler addCustomControls car on utilise la toolbar HTML

        canvas.add(cloned);
        // Optionnel: Sélectionner le clone ? Peut être perturbant pour l'utilisateur.
        // canvas.setActiveObject(cloned);
        canvas.requestRenderAll();
        saveCanvasState(canvas); // Sauvegarder l'état après duplication
        console.log("Objet dupliqué via controls.js:", cloned);
    }); // Pas besoin de spécifier les anciens contrôles dans les propriétés à cloner
}

// --- Les éléments suivants sont supprimés car gérés par la toolbar HTML ---
// - SVG Icons (cloneIcon, deleteIcon)
// - Image elements (deleteImg, cloneImg)
// - renderIcon (fonction de rendu pour les contrôles Fabric)
// - addDuplicateControl (ajout du contrôle Fabric spécifique)
// - addCustomControls (ajout des deux contrôles Fabric)
// - Les fonctions deleteObject/duplicateObject originales liées aux événements Fabric sont remplacées par celles-ci.
