
        // Initialisation du canvas Fabric.js
        const canvas = new fabric.Canvas('canvas');
        const colorPicker = document.getElementById('color-picker');

        // Définir la taille du canvas à la taille de la fenêtre
        canvas.setWidth(window.innerWidth);
        canvas.setHeight(window.innerHeight);



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
            updateZoomIndicator();
        });

        function updateZoomIndicator() {
            const zoomPercentage = Math.round(canvas.getZoom() * 100);
            document.getElementById('zoom-indicator').textContent = `Zoom: ${zoomPercentage}%`;
        }
        updateZoomIndicator();

        // Ajouter un rectangle
        document.getElementById('add-rect').addEventListener('click', () => {
            const rect = new fabric.Rect({
                left: 50,
                top: 50,
                fill: 'blue',
                width: 100,
                height: 100,
                cornerSize: 10,
                transparentCorners: false,
                // Activation du redimensionnement et de la rotation
                hasControls: true,
                hasRotatingPoint: true,
                lockScalingFlip: true,
            });
            canvas.add(rect);
        });

        // Ajouter du texte
        document.getElementById('add-text').addEventListener('click', () => {
            const text = new fabric.Textbox('Texte', {
                left: 50,
                top: 50,
                fill: 'black',
                fontSize: 20,
                width: 150,
                editable: true,
                // Activation du redimensionnement et de la rotation
                hasControls: true,
                hasRotatingPoint: true,
                lockScalingFlip: true,
            });
            canvas.add(text);
        });

        // Zoom In
        document.getElementById('zoom-in').addEventListener('click', () => {
            let zoom = canvas.getZoom();
            zoom *= 1.1;
            if (zoom > 20) zoom = 20;
            canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
            updateZoomIndicator();
        });

        // Zoom Out
        document.getElementById('zoom-out').addEventListener('click', () => {
            let zoom = canvas.getZoom();
            zoom *= 0.9;
            if (zoom < 0.01) zoom = 0.01;
            canvas.zoomToPoint({ x: canvas.width / 2, y: canvas.height / 2 }, zoom);
            updateZoomIndicator();
        });

        // Sauvegarder
        document.getElementById('saveButton').addEventListener('click', () => { // Line 118
            const state = canvas.toJSON();
            fetch(`/save_whiteboard/${window.projetId}`, { // Line 120: Use the global variable
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(state)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
                alert('Whiteboard sauvegardé !');
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('Erreur lors de la sauvegarde du whiteboard.');
            });
        });

        // Restaurer (exemple, à adapter)
        function loadCanvas(data) {
            canvas.loadFromJSON(data, canvas.renderAll.bind(canvas));
        }

        // Exemple de chargement (à adapter)
        fetch(`/load/${projetId}`)
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    console.log(data.message);
                    if (initialData) {
                        loadCanvas(initialData);
                    }
                } else {
                    loadCanvas(data);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });

        // Supprimer un objet
        document.getElementById('delete').addEventListener('click', () => {
            const activeObject = canvas.getActiveObject();
            if (activeObject) {
                canvas.remove(activeObject);
            }
        });

        colorPicker.addEventListener('change', () => {
            const selectedColor = colorPicker.value;
            const activeObject = canvas.getActiveObject();
            if (activeObject) {
                activeObject.set('fill', selectedColor);
                canvas.renderAll();
            }
        });
