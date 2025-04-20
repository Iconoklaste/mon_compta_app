// static/js/whiteboard/controls.js
import { saveCanvasState } from './state.js';

/**
 * Supprime l'objet actif (ou les objets d'un groupe) du canvas.
 * Destinée à être appelée depuis la barre d'outils ou un autre bouton/action.
 * @param {fabric.Object} target - L'objet à verrouiller/déverrouiller.
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


/**
 * Verrouille ou déverrouille l'objet cible.
 * Modifie les propriétés de l'objet pour empêcher/autoriser les modifications.
 * @param {fabric.Object} target - L'objet à verrouiller/déverrouiller.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
export function toggleObjectLock(target, canvas) {
    if (!target || !canvas) {
        console.warn("Tentative de verrouillage sans cible ou sans canvas.");
        return;
    }

    // Inverse l'état de verrouillage (utilise une propriété personnalisée)
    const currentlyLocked = target.isLocked === true;
    const newLockedState = !currentlyLocked;

    target.set('isLocked', newLockedState);

    // Applique les propriétés Fabric correspondantes
    target.set({
        lockMovementX: newLockedState,
        lockMovementY: newLockedState,
        lockRotation: newLockedState,
        lockScalingX: newLockedState,
        lockScalingY: newLockedState,
        lockSkewingX: newLockedState,
        lockSkewingY: newLockedState,
        lockUniScaling: newLockedState, // Verrouille aussi la mise à l'échelle uniforme
        hasControls: !newLockedState,   // Cache les contrôles si verrouillé
        hasBorders: !newLockedState,    // Cache les bordures si verrouillé
        selectable: !newLockedState,    // Rend l'objet non sélectionnable si verrouillé (attention, peut empêcher de le déverrouiller facilement via clic !)
                                        // Alternative: Laisser selectable=true mais bloquer les actions via les locks.*
                                        // Pour cet exemple, on le laisse sélectionnable pour pouvoir le déverrouiller via la toolbar.
        // selectable: true, // Laisser sélectionnable pour pouvoir cliquer et afficher la toolbar
    });

    // Si on veut le rendre vraiment non-sélectionnable quand il est verrouillé:
    // target.set('selectable', !newLockedState);
    // Mais il faudra un autre moyen pour le déverrouiller (ex: un bouton global, clic droit?)

    console.log(`Objet ${newLockedState ? 'verrouillé' : 'déverrouillé'}:`, target);

    canvas.requestRenderAll(); // Met à jour l'affichage (cache/affiche contrôles/bordures)
    saveCanvasState(canvas);   // Sauvegarde l'état pour l'undo/redo et la persistance
}

/**
 * Groupe les objets actuellement sélectionnés (ActiveSelection) sur le canvas.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
export function groupObjects(canvas) {
    const activeObject = canvas.getActiveObject();

    // Vérifie s'il y a une sélection active et si c'est bien une sélection multiple
    if (!activeObject || activeObject.type !== 'activeSelection') {
        console.log("Group: Aucune sélection multiple active.");
        return;
    }

    // Convertit la sélection active en groupe
    const group = activeObject.toGroup();

    // Fabric.js gère la suppression des objets originaux et l'ajout du groupe.
    // Il désélectionne aussi l'ancienne ActiveSelection.

    // Optionnel: Sélectionner le nouveau groupe créé
    canvas.setActiveObject(group);

    console.log("Objets groupés:", group);
    canvas.requestRenderAll();
    saveCanvasState(canvas); // Sauvegarder l'état après groupement
}

/**
 * Dégroupe l'objet de groupe actuellement sélectionné.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
export function ungroupObjects(canvas) {
    const activeObject = canvas.getActiveObject();

    // Vérifie s'il y a une sélection active et si c'est bien un groupe
    if (!activeObject || activeObject.type !== 'group') {
        console.log("Ungroup: Aucun groupe sélectionné.");
        return;
    }

    // Convertit le groupe en sélection active (les objets sont ajoutés au canvas)
    const activeSelection = activeObject.toActiveSelection();

    // Fabric.js gère la suppression du groupe et la création/sélection de l'ActiveSelection.

    console.log("Groupe dégroupé. Nouvelle sélection:", activeSelection);
    canvas.requestRenderAll();
    saveCanvasState(canvas); // Sauvegarder l'état après dégroupement
}