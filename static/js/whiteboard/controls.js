// controls.js
import { saveCanvasState } from './state.js';

// --- SVG Icons ---
const cloneIcon =
  "data:image/svg+xml,%3C%3Fxml version='1.0' encoding='iso-8859-1'%3F%3E%3Csvg version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' viewBox='0 0 55.699 55.699' width='100px' height='100px' xml:space='preserve'%3E%3Cpath style='fill:%23010002;' d='M51.51,18.001c-0.006-0.085-0.022-0.167-0.05-0.248c-0.012-0.034-0.02-0.067-0.035-0.1 c-0.049-0.106-0.109-0.206-0.194-0.291v-0.001l0,0c0,0-0.001-0.001-0.001-0.002L34.161,0.293c-0.086-0.087-0.188-0.148-0.295-0.197 c-0.027-0.013-0.057-0.02-0.086-0.03c-0.086-0.029-0.174-0.048-0.265-0.053C33.494,0.011,33.475,0,33.453,0H22.177 c-3.678,0-6.669,2.992-6.669,6.67v1.674h-4.663c-3.678,0-6.67,2.992-6.67,6.67V49.03c0,3.678,2.992,6.669,6.67,6.669h22.677 c3.677,0,6.669-2.991,6.669-6.669v-1.675h4.664c3.678,0,6.669-2.991,6.669-6.669V18.069C51.524,18.045,51.512,18.025,51.51,18.001z M34.454,3.414l13.655,13.655h-8.985c-2.575,0-4.67-2.095-4.67-4.67V3.414z M38.191,49.029c0,2.574-2.095,4.669-4.669,4.669H10.845 c-2.575,0-4.67-2.095-4.67-4.669V15.014c0-2.575,2.095-4.67,4.67-4.67h5.663h4.614v10.399c0,3.678,2.991,6.669,6.668,6.669h10.4 v18.942L38.191,49.029L38.191,49.029z M36.777,25.412h-8.986c-2.574,0-4.668-2.094-4.668-4.669v-8.985L36.777,25.412z M44.855,45.355h-4.664V26.412c0-0.023-0.012-0.044-0.014-0.067c-0.006-0.085-0.021-0.167-0.049-0.249 c-0.012-0.033-0.021-0.066-0.036-0.1c-0.048-0.105-0.109-0.205-0.194-0.29l0,0l0,0c0-0.001-0.001-0.002-0.001-0.002L22.829,8.637 c-0.087-0.086-0.188-0.147-0.295-0.196c-0.029-0.013-0.058-0.021-0.088-0.031c-0.086-0.03-0.172-0.048-0.263-0.053 c-0.021-0.002-0.04-0.013-0.062-0.013h-4.614V6.67c0-2.575,2.095-4.67,4.669-4.67h10.277v10.4c0,3.678,2.992,6.67,6.67,6.67h10.399 v21.616C49.524,43.26,47.429,45.355,44.855,45.355z'/%3E%3C/svg%3E%0A";
const deleteIcon =
  "data:image/svg+xml,%3C%3Fxml version='1.0' encoding='utf-8'%3F%3E%3C!DOCTYPE svg PUBLIC '-//W3C//DTD SVG 1.1//EN' 'http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd'%3E%3Csvg version='1.1' id='Ebene_1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' x='0px' y='0px' width='595.275px' height='595.275px' viewBox='200 215 230 470' xml:space='preserve'%3E%3Ccircle style='fill:%23F44336;' cx='299.76' cy='439.067' r='218.516'/%3E%3Cg%3E%3Crect x='267.162' y='307.978' transform='matrix(0.7071 -0.7071 0.7071 0.7071 -222.6202 340.6915)' style='fill:white;' width='65.545' height='262.18'/%3E%3Crect x='266.988' y='308.153' transform='matrix(0.7071 0.7071 -0.7071 0.7071 398.3889 -83.3116)' style='fill:white;' width='65.544' height='262.179'/%3E%3C/g%3E%3C/svg%3E";

// Création des éléments image pour les icônes
export const deleteImg = document.createElement('img');
deleteImg.src = deleteIcon;

export const cloneImg = document.createElement('img');
cloneImg.src = cloneIcon;

// --- Fonctions de Contrôle ---

/**
 * Ajoute un contrôle de duplication à un objet Fabric.js.
 * @param {fabric.Object} object - L'objet auquel ajouter le contrôle.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
export function addDuplicateControl(object, canvas) {
    // console.log("addDuplicateControl called for:", object); // Log de débogage (peut être supprimé)
    object.cornerStyle = 'circle'; // Style de coin standard
    object.cornerSize = 15;        // Taille de coin standard
    object.controls.duplicateControl = new fabric.Control({
        x: -0.5, // Position coin supérieur gauche
        y: -0.5, // Position coin supérieur gauche
        offsetX: -15, // Décalage pour positionner l'icône
        offsetY: -15, // Décalage pour positionner l'icône
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => duplicateObject(eventData, transform, canvas), // Utilise la fonction plus complète
        render: renderIcon(cloneImg), // Fonction pour dessiner l'icône
        cornerSize: 24 // Taille de la zone cliquable du contrôle
    });
}

/**
 * Duplique un objet Fabric.js, l'ajoute au canvas et le rend actif.
 * @param {Event} eventData - Données de l'événement souris.
 * @param {fabric.Transform} transform - Informations sur la transformation.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
function duplicateObject(eventData, transform, canvas) {
    // console.log("duplicateObject called"); // Log de débogage
    const target = transform.target;
    if (!target) return; // Sécurité

    target.clone((cloned) => {
        // console.log("duplicateObject cloned:", cloned); // Log de débogage
        cloned.set({
            left: cloned.left + 20, // Décalage pour la visibilité
            top: cloned.top + 20,   // Décalage pour la visibilité
            evented: true,         // Assure que l'objet cloné est interactif
        });

        // Ré-appliquer les contrôles personnalisés au clone
        // (Important car le clonage Fabric.js ne clone pas toujours les contrôles ajoutés manuellement)
        addCustomControls(cloned, canvas); // Utiliser une fonction centralisée

        canvas.add(cloned);
        canvas.setActiveObject(cloned); // Rendre le clone actif
        canvas.requestRenderAll();
        saveCanvasState(canvas); // Sauvegarder l'état après duplication
    }, ['deleteControl', 'duplicateControl']); // Inclure les contrôles personnalisés dans le clonage si possible
}

/**
 * Fonction utilitaire pour dessiner une icône dans un contrôle Fabric.js.
 * @param {HTMLImageElement} icon - L'élément image de l'icône.
 * @returns {Function} - La fonction de rendu pour le contrôle.
 */
export function renderIcon(icon) {
    // console.log("renderIcon called"); // Log de débogage
    return function (ctx, left, top, styleOverride, fabricObject) {
        // console.log("renderIcon inner function called"); // Log de débogage
        const size = this.cornerSize;
        if (!icon || !icon.complete || icon.naturalWidth === 0) {
             // Ne rien dessiner si l'icône n'est pas prête
             console.warn("Icon not ready for rendering:", icon.src);
             return;
        }
        ctx.save();
        ctx.translate(left, top);
        // Appliquer la rotation de l'objet pour que l'icône tourne avec
        ctx.rotate(fabric.util.degreesToRadians(fabricObject.angle || 0));
        ctx.drawImage(icon, -size / 2, -size / 2, size, size);
        ctx.restore();
    };
}

/**
 * Supprime l'objet cible (ou les objets d'un groupe) du canvas.
 * @param {Event} eventData - Données de l'événement souris.
 * @param {fabric.Transform} transform - Informations sur la transformation.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
export function deleteObject(eventData, transform, canvas) {
    // console.log("deleteObject called"); // Log de débogage
    const target = transform.target;
    if (!target) return; // Sécurité

    // Fabric.js gère la suppression des groupes et de leurs objets internes
    // Il suffit de supprimer l'objet actif (qui peut être un groupe)
    canvas.remove(target);

    canvas.discardActiveObject(); // Désélectionner après suppression
    canvas.requestRenderAll();
    saveCanvasState(canvas); // Sauvegarder l'état après suppression
}

/**
 * Ajoute les contrôles personnalisés (supprimer, dupliquer) à un objet.
 * Centralise la logique d'ajout de contrôles.
 * @param {fabric.Object} object - L'objet auquel ajouter les contrôles.
 * @param {fabric.Canvas} canvas - L'instance du canvas.
 */
export function addCustomControls(object, canvas) {
    object.cornerStyle = 'circle';
    object.cornerSize = 15; // Taille standard des coins

    // Contrôle Supprimer (coin supérieur droit)
    object.controls.deleteControl = new fabric.Control({
        x: 0.5,
        y: -0.5,
        offsetX: 16, // Ajusté pour être légèrement à l'extérieur
        offsetY: -16,
        cursorStyle: 'pointer',
        mouseUpHandler: (eventData, transform) => deleteObject(eventData, transform, canvas),
        render: renderIcon(deleteImg),
        cornerSize: 24 // Taille de la zone cliquable
    });

    // Contrôle Dupliquer (coin supérieur gauche) - Ajouter seulement si ce n'est pas déjà fait
    // Vérifier si le contrôle existe déjà peut éviter des erreurs si appelé plusieurs fois
    if (!object.controls.duplicateControl) {
        object.controls.duplicateControl = new fabric.Control({
            x: -0.5,
            y: -0.5,
            offsetX: -16,
            offsetY: -16,
            cursorStyle: 'pointer',
            mouseUpHandler: (eventData, transform) => duplicateObject(eventData, transform, canvas),
            render: renderIcon(cloneImg),
            cornerSize: 24
        });
    }
}


// La fonction cloneObject originale semble redondante ou incomplète par rapport à duplicateObject.
// Si elle n'est pas utilisée ailleurs, elle pourrait être supprimée.
// Si elle est utilisée, elle devrait probablement être rendue aussi complète que duplicateObject.
/*
export function cloneObject(_eventData, transform, canvas) {
    console.log("cloneObject called"); // Log de débogage
    const target = transform.target;
    if (!target) return;

    target.clone((cloned) => {
        console.log("cloneObject cloned:", cloned); // Log de débogage
        cloned.set({
            left: cloned.left + 10,
            top: cloned.top + 10,
            // evented: true, // Manquant ?
        });
        // Ré-appliquer les contrôles ?
        // addCustomControls(cloned, canvas); // Manquant ?

        // Copier les contrôles existants (peut être problématique si les références ne sont pas gérées correctement)
        // cloned.controls.deleteControl = target.controls.deleteControl;
        // cloned.controls.duplicateControl = target.controls.duplicateControl;

        canvas.add(cloned);
        // canvas.setActiveObject(cloned); // Manquant ?
        canvas.requestRenderAll();
        saveCanvasState(canvas);
    }, ['deleteControl', 'duplicateControl']); // Essayer d'inclure les contrôles
}
*/
