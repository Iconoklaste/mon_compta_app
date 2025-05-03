// Mettez ceci dans un fichier JS chargé dans base.html (après le DOM)
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mainContent = document.querySelector('.main-content'); // Ajout pour overlay optionnel
    const navbar = document.querySelector('.navbar'); // Ajout pour overlay optionnel

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', function(event) {
            event.preventDefault();
            sidebar.classList.toggle('show');
            // Optionnel : Ajouter une classe au body pour un overlay ou ajustements
            document.body.classList.toggle('sidebar-shown');
        });
    }

    // Optionnel : Fermer la sidebar si on clique en dehors sur mobile/tablette
     document.addEventListener('click', function(event) {
        const target = event.target;
        // Si la sidebar est visible et qu'on clique en dehors d'elle ET pas sur le bouton toggle
        if (sidebar && sidebar.classList.contains('show') && !sidebar.contains(target) && target !== sidebarToggle && !sidebarToggle.contains(target)) {
             sidebar.classList.remove('show');
             document.body.classList.remove('sidebar-shown'); // Enlever la classe body aussi
        }
    });
});