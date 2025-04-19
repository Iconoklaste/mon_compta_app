/**
 * fabric.brushes - A collection of brushes for fabric.js (version 4 and up).
 *
 * Made by Arjan Haverkamp, https://www.webgear.nl
 * Copyright 2021-2024 Arjan Haverkamp
 * MIT Licensed
 * @version 1.0.2 - 2024-XX-XX (Corrected viewport transform issue and fabric.Point usage)
 * @url https://github.com/av01d/fabric-brushes
 *
 * Inspiration sources:
 * - https://github.com/tennisonchan/fabric-brush
 * - https://mrdoob.com/projects/harmony/
 * - http://perfectionkills.com/exploring-canvas-drawing-techniques/
 */

(function(fabric) {

/**
 * Trim a canvas. Returns the left-top coordinate where trimming began.
 * @param {HTMLCanvasElement} canvas A canvas element to trim. This element will be trimmed (reference).
 * @returns {Object} Left-top coordinate of trimmed area. Example: {x:65, y:104}
 * @see: https://stackoverflow.com/a/22267731/3360038
 */
fabric.util.trimCanvas = function(canvas) {
	var ctx = canvas.getContext('2d'),
		w = canvas.width,
		h = canvas.height,
		pix = {x:[], y:[]}, n,
		imageData = ctx.getImageData(0,0,w,h),
		fn = function(a,b) { return a-b };

	for (var y = 0; y < h; y++) {
		for (var x = 0; x < w; x++) {
			if (imageData.data[((y * w + x) * 4)+3] > 0) {
				pix.x.push(x);
				pix.y.push(y);
			}
		}
	}
	pix.x.sort(fn);
	pix.y.sort(fn);
	n = pix.x.length-1;

	// Handle cases where the trimmed area might be 0 width or height
	w = (pix.x.length > 0) ? pix.x[n] - pix.x[0] + 1 : 0; // +1 to include the last pixel
	h = (pix.y.length > 0) ? pix.y[n] - pix.y[0] + 1 : 0; // +1 to include the last pixel

	if (w <= 0 || h <= 0) {
		// If width or height is zero or negative, the canvas is effectively empty or a line
		canvas.width = 1; // Set to a minimal size to avoid errors
		canvas.height = 1;
		ctx.clearRect(0, 0, 1, 1); // Clear the 1x1 canvas
		return { x: 0, y: 0 }; // Return 0,0 as the origin
	}


	var cut = ctx.getImageData(pix.x[0], pix.y[0], w, h);

	canvas.width = w;
	canvas.height = h;
	ctx.putImageData(cut, 0, 0);

	return {x:pix.x[0], y:pix.y[0]};
}

/**
 * Extract r,g,b,a components from any valid color.
 * Returns {undefined} when color cannot be parsed.
 *
 * @param {string} color Any color string (named, hex, rgb, rgba)
 * @returns {(Array|undefined)} Example: [0,128,255,1]
 * @see https://gist.github.com/oriadam/396a4beaaad465ca921618f2f2444d49
 */
fabric.util.colorValues = function(color) {
	if (!color) { return; }
	if (color.toLowerCase() === 'transparent') { return [0, 0, 0, 0]; }
	if (color[0] === '#') {
		if (color.length < 7) {
			// convert #RGB and #RGBA to #RRGGBB and #RRGGBBAA
			color = '#' + color[1] + color[1] + color[2] + color[2] + color[3] + color[3] + (color.length > 4 ? color[4] + color[4] : '');
		}
		return [parseInt(color.substr(1, 2), 16),
			parseInt(color.substr(3, 2), 16),
			parseInt(color.substr(5, 2), 16),
			color.length > 7 ? parseInt(color.substr(7, 2), 16)/255 : 1];
	}
	if (color.indexOf('rgb') === -1) {
		// convert named colors
		var tempElem = document.body.appendChild(document.createElement('fictum')); // intentionally use unknown tag to lower chances of css rule override with !important
		var flag = 'rgb(1, 2, 3)'; // this flag tested on chrome 59, ff 53, ie9, ie10, ie11, edge 14
		tempElem.style.color = flag;
		if (tempElem.style.color !== flag) {
			// Fallback for environments where style manipulation might be restricted or fail
			// Attempt to use a temporary canvas for color parsing
			var ctx = document.createElement('canvas').getContext('2d');
			if (!ctx) return; // Canvas context not available
			ctx.fillStyle = color;
			var parsedColor = ctx.fillStyle;
			// Check if the browser could parse it (it might return black or transparent if not)
			if (parsedColor !== '#000000' && parsedColor !== 'rgba(0, 0, 0, 0)') {
				// If it looks like a valid parsed color (hex or rgb/a), try converting that
				document.body.removeChild(tempElem);
				return fabric.util.colorValues(parsedColor);
			}
			// If still failing, return undefined
			document.body.removeChild(tempElem);
			return;
		}
		tempElem.style.color = color;
		if (tempElem.style.color === flag || tempElem.style.color === '') {
			document.body.removeChild(tempElem);
			return; // color parse failed
		}
		color = getComputedStyle(tempElem).color;
		document.body.removeChild(tempElem);
	}
	if (color.indexOf('rgb') === 0)	{
		if (color.indexOf('rgba') === -1) {
			color += ',1'; // convert 'rgb(R,G,B)' to 'rgb(R,G,B)A' which looks awful but will pass the regxep below
		}
		var match = color.match(/[\.\d]+/g);
		if (match) {
			return match.map(function(a) { return +a; });
		}
		// Handle potential parsing errors if match is null
		return;
	}
}


fabric.Point.prototype.angleBetween = function(that) {
	return Math.atan2( this.x - that.x, this.y - that.y);
};

fabric.Point.prototype.normalize = function(thickness) {
	if (null === thickness || undefined === thickness) {
		thickness = 1;
	}

	var length = this.distanceFrom({ x: 0, y: 0 });

	if (length > 0) {
		this.x = this.x / length * thickness;
		this.y = this.y / length * thickness;
	}

	return this;
};

/**
 * Convert a brush drawing on the upperCanvas to an image on the fabric canvas.
 * This makes the drawing editable, it can be moved, rotated, scaled, skewed etc.
 */
fabric.BaseBrush.prototype.convertToImg = function() {
	console.log('[convertToImg] Start'); // Log début
	// Prevent conversion if no drawing occurred or canvas is disposed
	if (!this.canvas || !this.canvas.upperCanvasEl || !this._drawn) {
        console.log('[convertToImg] Aborted: No canvas, upperCanvas, or not drawn.');
		this.canvas && this.canvas.clearContext(this.canvas.contextTop);
		return;
	}

	var pixelRatio = this.canvas.getRetinaScaling();
    console.log('[convertToImg] PixelRatio:', pixelRatio);

	var canvasElement = this.canvas.upperCanvasEl;
    console.log('[convertToImg] Copying upperCanvasEl...');
	var c = fabric.util.copyCanvasElement(canvasElement);
    console.log('[convertToImg] Copied canvas dimensions:', c.width, 'x', c.height);

    console.log('[convertToImg] Trimming copied canvas...');
	var xy = fabric.util.trimCanvas(c);
    console.log('[convertToImg] Trimmed canvas dimensions:', c.width, 'x', c.height);
    console.log('[convertToImg] Trim result (xy):', xy);


	if (c.width <= 0 || c.height <= 0) {
        console.log('[convertToImg] Aborted: Trimmed canvas has zero dimension.');
		this.canvas.clearContext(this.canvas.contextTop);
		return;
	}

    // --- VERSION CORRIGÉE AVEC LOGS ---
    // 1. Calculate the top-left screen coordinate (relative to the canvas element)
    const screenPoint = new fabric.Point(xy.x / pixelRatio, xy.y / pixelRatio);
    console.log('[convertToImg] Calculated screenPoint (trimmed top-left / pixelRatio):', screenPoint);

    // 2. Get the inverse of the current viewport transform matrix.
    const invViewportTransform = fabric.util.invertTransform(this.canvas.viewportTransform);
    console.log('[convertToImg] Inverse Viewport Transform:', invViewportTransform);
    console.log('[convertToImg] Current Viewport Transform:', this.canvas.viewportTransform); // Log aussi le viewport actuel

    // 3. Transform the screen point into a point relative to the canvas's internal coordinate system.
    const canvasPoint = fabric.util.transformPoint(screenPoint, invViewportTransform);
    console.log('[convertToImg] Calculated canvasPoint (transformed screenPoint):', canvasPoint);
    // --- FIN VERSION CORRIGÉE AVEC LOGS ---

	var img = new fabric.Image(c);
	console.log('[convertToImg] fabric.Image created.');

	const imageProps = {
		left: canvasPoint.x, // <-- Utilise la coordonnée canvas corrigée
		top: canvasPoint.y,  // <-- Utilise la coordonnée canvas corrigée
		scaleX: 1 / pixelRatio,
		scaleY: 1 / pixelRatio,
		originX: 'left',
		originY: 'top',
        objectCaching: false // Garder pour éviter les problèmes de rendu pendant le pan
	};
	console.log('[convertToImg] Setting image properties:', imageProps);

	img.set(imageProps).setCoords();
	console.log('[convertToImg] Image properties set and coords calculated.');

	this.canvas.add(img);
	console.log('[convertToImg] Image added to canvas.');
	this.canvas.clearContext(this.canvas.contextTop); // Clear the upper canvas
	console.log('[convertToImg] contextTop cleared.');
	this._drawn = false; // Reset drawn flag
	console.log('[convertToImg] End');
	// Optional: Save state if needed
	if (typeof saveCanvasState === 'function') { saveCanvasState(this.canvas); }
}


fabric.util.getRandom = function(max, min) {
	min = min ? min : 0;
	return Math.random() * ((max ? max : 1) - min) + min;
};

fabric.util.clamp = function (n, max, min) {
	if (typeof min !== 'number') { min = 0; }
	return n > max ? max : n < min ? min : n;
};

// --- BaseBrush Modifications ---
// Add _lastScreenPointer to store untransformed coordinates for drawing on contextTop
fabric.BaseBrush.prototype._lastScreenPointer = null; // Will store a fabric.Point
fabric.BaseBrush.prototype._drawn = false; // Add a flag to track if anything was drawn

// Modify onMouseDown and onMouseMove to accept the options object
var originalOnMouseDown = fabric.BaseBrush.prototype.onMouseDown;
fabric.BaseBrush.prototype.onMouseDown = function(pointer, options) {
	// Call original if it exists and is different
	if (originalOnMouseDown && originalOnMouseDown !== this.onMouseDown) {
		originalOnMouseDown.call(this, pointer, options);
	}
	// Store the untransformed pointer coordinates AS A FABRIC.POINT
    const screenCoords = this.canvas.getPointer(options.e, true);
	this._lastScreenPointer = screenCoords ? new fabric.Point(screenCoords.x, screenCoords.y) : null;
	this._drawn = false; // Reset drawn flag at the start of a new stroke
};

var originalOnMouseMove = fabric.BaseBrush.prototype.onMouseMove;
fabric.BaseBrush.prototype.onMouseMove = function(pointer, options) {
    // Call original if it exists and is different
	if (originalOnMouseMove && originalOnMouseMove !== this.onMouseMove) {
		originalOnMouseMove.call(this, pointer, options);
	}
    // Update _drawn flag if moving
    if (this.canvas._isCurrentlyDrawing) {
        this._drawn = true;
    }
	// Store the untransformed pointer coordinates for the next move
    // This will be done within each brush's specific drawing logic after using the current screenPointer
};

var originalOnMouseUp = fabric.BaseBrush.prototype.onMouseUp;
fabric.BaseBrush.prototype.onMouseUp = function(options) {
    console.log('[BaseBrush.onMouseUp] Entered.'); // Log entrée

    const wasDrawn = this._drawn; // Stocker l'état de _drawn
    console.log('[BaseBrush.onMouseUp] _drawn state at entry:', wasDrawn);

    // Appeler l'original s'il existe (peut être nécessaire pour la logique interne de Fabric)
	if (originalOnMouseUp && originalOnMouseUp !== this.onMouseUp) {
        console.log('[BaseBrush.onMouseUp] Calling original onMouseUp.');
		originalOnMouseUp.call(this, options);
	}

    // --- CORRECTION DE L'ORDRE ---
    // Convertir en image SI quelque chose AVAIT été dessiné
    if (wasDrawn) {
        console.log('[BaseBrush.onMouseUp] wasDrawn is true. Calling convertToImg...');
        try {
            this.convertToImg(); // convertToImg a ses propres logs (et met _drawn=false à la fin)
            console.log('[BaseBrush.onMouseUp] convertToImg finished.');

            // Sauvegarder l'état APRÈS la conversion réussie
            if (typeof saveCanvasState === 'function') {
                console.log('[BaseBrush.onMouseUp] Calling saveCanvasState...');
                saveCanvasState(this.canvas);
                console.log('[BaseBrush.onMouseUp] saveCanvasState finished.');
            }
        } catch (error) {
             console.error('[BaseBrush.onMouseUp] Error during convertToImg or saveCanvasState:', error);
             // Nettoyer le canvas temporaire en cas d'erreur pendant la conversion
             if (this.canvas && this.canvas.contextTop) {
                 this.canvas.clearContext(this.canvas.contextTop);
             }
             // Assurer que _drawn est false même en cas d'erreur avant _reset
             this._drawn = false;
        }
    } else {
         console.log('[BaseBrush.onMouseUp] wasDrawn is false. Skipping convertToImg.');
         // Nettoyer le canvas temporaire si rien n'a été dessiné
         if (this.canvas && this.canvas.contextTop) {
             console.log('[BaseBrush.onMouseUp] Clearing contextTop because wasDrawn is false.');
             this.canvas.clearContext(this.canvas.contextTop);
         }
    }

    // Appeler _reset APRÈS la conversion (ou le nettoyage)
    // Note: convertToImg met déjà _drawn à false, mais _reset peut nettoyer d'autres choses.
    console.log('[BaseBrush.onMouseUp] Calling _reset...');
    this._reset(); // _reset a son propre log
    console.log('[BaseBrush.onMouseUp] _reset finished.');
    // --- FIN CORRECTION DE L'ORDRE ---

    console.log('[BaseBrush.onMouseUp] Exiting.');
};

// Le log dans _reset reste utile pour confirmer l'appel
if (!fabric.BaseBrush.prototype._reset) {
	fabric.BaseBrush.prototype._reset = function() {
        console.log('--- [BaseBrush._reset] Called ---');
		this._lastScreenPointer = null;
        this._drawn = false;
	};
} else {
    var originalReset = fabric.BaseBrush.prototype._reset;
    fabric.BaseBrush.prototype._reset = function() {
        console.log('--- [BaseBrush._reset] Called (via wrapper) ---');
        originalReset.call(this);
        this._lastScreenPointer = null;
        this._drawn = false; // Assurer que _drawn est bien mis à false
    };
}

// --- End BaseBrush Modifications ---


fabric.Stroke = fabric.util.createClass(fabric.Object,{
	color: null,
	inkAmount: null,
	lineWidth: null,

	_point: null, // Transformed canvas coordinates
	_lastPoint: null, // Transformed canvas coordinates
    _screenPoint: null, // Screen coordinates for drawing (fabric.Point)
    _lastScreenPoint: null, // Screen coordinates for drawing (fabric.Point)
	_currentLineWidth: null,

	// Pass screenPointer (expected to be a fabric.Point) for initial drawing position
	initialize: function(ctx, pointer, screenPointer, range, color, lineWidth, inkAmount) {
		var rx = fabric.util.getRandom(range),
			c = fabric.util.getRandom(Math.PI * 2),
			c0 = fabric.util.getRandom(Math.PI * 2),
			x0 = rx * Math.sin(c0),
			y0 = rx / 2 * Math.cos(c0),
			cos = Math.cos(c),
			sin = Math.sin(c);

		this.ctx = ctx;
		this.color = color;
		// Store both transformed and screen coordinates
		this._point = new fabric.Point(pointer.x + x0 * cos - y0 * sin, pointer.y + x0 * sin + y0 * cos);
        // screenPointer is expected to be a fabric.Point here
        this._screenPoint = new fabric.Point(screenPointer.x + x0 * cos - y0 * sin, screenPointer.y + x0 * sin + y0 * cos);
		this.lineWidth = lineWidth;
		this.inkAmount = inkAmount;
		this._currentLineWidth = lineWidth;
        this._lastScreenPoint = this._screenPoint.clone(); // Initialize last screen point

		ctx.lineCap = 'round';
	},

	// Update needs both transformed and screen points (fabric.Point instances)
	update: function(pointer, screenPointer, subtractPoint, distance) {
		this._lastPoint = fabric.util.object.clone(this._point);
        this._lastScreenPoint = this._screenPoint.clone(); // Update last screen point

		this._point = this._point.addEquals({ x: subtractPoint.x, y: subtractPoint.y });

        // screenPointer and this._lastScreenPoint are fabric.Point instances
        // Calculate the delta in screen coordinates
        const screenDelta = screenPointer.subtract(this._lastScreenPoint);
        // Apply the delta to the current screen point
        this._screenPoint = this._screenPoint.add(screenDelta); // Use add, not addEquals

		var n = this.inkAmount / (distance + 1),
			per = (n > 0.3 ? 0.2 : n < 0 ? 0 : n);
		this._currentLineWidth = this.lineWidth * per;
	},

	draw: function() {
		var ctx = this.ctx;
		ctx.save();
        // Use screen coordinates (fabric.Point instances) for drawing
		this.line(ctx, this._lastScreenPoint, this._screenPoint, this.color, this._currentLineWidth);
		ctx.restore();
	},

	line: function(ctx, point1, point2, color, lineWidth) {
        // Ensure points are valid before drawing
        if (!point1 || !point2) return;
		ctx.strokeStyle = color;
		ctx.lineWidth = lineWidth;
		ctx.beginPath();
		ctx.moveTo(point1.x, point1.y);
		ctx.lineTo(point2.x, point2.y);
		ctx.stroke();
	}
});

/**
 * CrayonBrush
 * Based on code by Tennison Chan.
 */
fabric.CrayonBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 0.6,
	width: 30,

	_baseWidth: 20,
	_inkAmount: 10,
	_latestStrokeLength: 0,
	_point: null, // Transformed point
    _screenPoint: null, // Screen point for drawing (fabric.Point)
    _lastScreenPoint: null, // Previous screen point for drawing (fabric.Point)
	_sep: 5,
	_size: 0,
	_latest: null, // Transformed point
	// _drawn: false, // Inherited from BaseBrush

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || canvas.contextTop.globalAlpha; // Use contextTop's alpha if set
		this._point = new fabric.Point(0, 0);
        this._screenPoint = new fabric.Point(0, 0); // Initialize as Point
	},

	// Accept options object
	onMouseDown: function(pointer, options) {
        // Call BaseBrush onMouseDown first to set _lastScreenPointer
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options);

		this.canvas.contextTop.globalAlpha = this.opacity;
		this._size = this.width / 2 + this._baseWidth;
		// this._drawn = false; // Handled by BaseBrush
		this.set(pointer, options); // Pass options to set

        // Initialize screen points as fabric.Point
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (screenCoords) {
            this._screenPoint = new fabric.Point(screenCoords.x, screenCoords.y);
            // Use _lastScreenPointer from BaseBrush as the initial last point
            this._lastScreenPoint = this._lastScreenPointer ? this._lastScreenPointer.clone() : this._screenPoint.clone();
        } else {
            // Fallback if getPointer fails (shouldn't happen with valid event)
            this._screenPoint = new fabric.Point(pointer.x, pointer.y);
            this._lastScreenPoint = this._screenPoint.clone();
        }
	},

	// Accept options object
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return; // Check if drawing

        // Store the *current* screen point before updating it
        const currentScreenCoords = this.canvas.getPointer(options.e, true);
        if (!currentScreenCoords) return; // Exit if we can't get pointer coords

        // Update the transformed point and calculate stroke length
		this.update(pointer, options); // This calls set, which updates this._point and this._screenPoint

        // Ensure _lastScreenPoint is a fabric.Point before drawing
        if (!this._lastScreenPoint) {
             this._lastScreenPoint = this._screenPoint ? this._screenPoint.clone() : new fabric.Point(currentScreenCoords.x, currentScreenCoords.y);
        }

        // Draw using the *new* _screenPoint and the *previous* _lastScreenPoint
		this.draw(this.canvas.contextTop, options);

        // Now update _lastScreenPoint for the *next* move event
        this._lastScreenPoint = this._screenPoint ? this._screenPoint.clone() : new fabric.Point(currentScreenCoords.x, currentScreenCoords.y); // Update with the point used in this move

        this._drawn = true; // Mark as drawn
	},

	onMouseUp: function(options) { // Accept options for consistency
		console.log('[CrayonBrush.onMouseUp] Entered.');
		// --- AJOUT IMPORTANT ---
        // Appeler la méthode onMouseUp du parent (BaseBrush)
        // C'est elle qui contient maintenant la logique pour appeler convertToImg et _reset
        fabric.BaseBrush.prototype.onMouseUp.call(this, options);
        // --- FIN DE L'AJOUT ---
		// convertToImg is now called by the modified BaseBrush.onMouseUp if _drawn is true
		this._latest = null;
		this._latestStrokeLength = 0;
		this.canvas.contextTop.globalAlpha = 1; // Reset alpha
        this._reset(); // Call base reset
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this); // Call parent reset
		this._latest = null;
		this._latestStrokeLength = 0;
        this._point = new fabric.Point(0, 0);
        this._screenPoint = null; // Reset screen points
        this._lastScreenPoint = null;
    },

	// Modify set to accept options and update screen point as fabric.Point
	set: function(p, options) {
		if (this._latest) {
			this._latest.setFromPoint(this._point);
		} else {
			this._latest = new fabric.Point(p.x, p.y);
		}
		fabric.Point.prototype.setFromPoint.call(this._point, p);

        // Update screen point if options are provided (i.e., during mouse events)
        if (options && options.e) {
            const screenCoords = this.canvas.getPointer(options.e, true);
            if (screenCoords) {
                this._screenPoint = new fabric.Point(screenCoords.x, screenCoords.y); // <-- Ensure it's a Point
            }
        }
	},

	// Modify update to accept options
	update: function(p, options) {
		this.set(p, options); // Pass options to set
		// Calculate distance based on transformed points for ink amount logic
        if (this._latest) { // Ensure _latest is not null
		    this._latestStrokeLength = this._point.subtract(this._latest).distanceFrom({ x: 0, y: 0 });
        } else {
            this._latestStrokeLength = 0;
        }
	},

	// Modify draw to use screen coordinates (already fabric.Point instances)
	draw: function(ctx, options) {
        // Ensure both points are valid fabric.Point instances
        if (!this._lastScreenPoint || !this._screenPoint) return;

        var i, j, pScreen, r, c, x, y, w, h, vScreen, s, stepNum, dotSize, dotNum, range;

        const currentScreenPoint = this._screenPoint; // Use the updated screen point (already a Point)

        // Calculate screen vector and distance for drawing steps
        // Both operands should now be fabric.Point instances
        vScreen = currentScreenPoint.subtract(this._lastScreenPoint); // <--- Error was here
        s = Math.ceil(this._size / 2);
        const screenDist = vScreen.distanceFrom({ x: 0, y: 0 });
        stepNum = Math.max(1, Math.floor(screenDist / s) + 1); // Ensure at least 1 step
        vScreen.normalize(s);

        // Use transformed distance for ink logic (as before)
        dotSize = this._sep * fabric.util.clamp(this._inkAmount / (this._latestStrokeLength || 1) * 3, 1, 0.5); // Avoid division by zero
        dotNum = Math.ceil(this._size * this._sep);
        range = this._size / 2;

        ctx.save();
        ctx.fillStyle = this.color;
        ctx.beginPath();
        for (i = 0; i < dotNum; i++) {
            for (j = 0; j < stepNum; j++) {
                // Calculate intermediate screen points for drawing
                // Use add and multiply which work with fabric.Point
                pScreen = this._lastScreenPoint.add(vScreen.multiply(j));
                r = fabric.util.getRandom(range);
                c = fabric.util.getRandom(Math.PI * 2);
                w = fabric.util.getRandom(dotSize, dotSize / 2);
                h = fabric.util.getRandom(dotSize, dotSize / 2);
                x = pScreen.x + r * Math.sin(c) - w / 2;
                y = pScreen.y + r * Math.cos(c) - h / 2;
                ctx.rect(x, y, w, h);
            }
        }
        ctx.fill();
        ctx.restore();
	},

	_render: function() {} // Keep empty as drawing is handled in onMouseMove

}); // End CrayonBrush

/**
 * FurBrush
 * Based on code by Mr. Doob.
 */
fabric.FurBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 1,

	_count: 0,
	_points: [], // Stores transformed points
    _screenPoints: [], // Stores screen points for drawing (fabric.Point instances)

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || 1;
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		this._points = [pointer];
        const screenCoords = this.canvas.getPointer(options.e, true);
        this._screenPoints = screenCoords ? [new fabric.Point(screenCoords.x, screenCoords.y)] : []; // Store initial screen point as Point
		this._count = 0;
        // this._drawn = false; // Handled by BaseBrush

		var ctx = this.canvas.contextTop,
			color = fabric.util.colorValues(this.color);

		ctx.strokeStyle = 'rgba(' + color[0] + ',' + color[1] + ',' + color[2] + ',' + (0.1 * this.opacity) + ')';
		ctx.lineWidth = this.width;
	},

	// Accept options
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return;

		this._points.push(pointer);
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (!screenCoords) return;
        const screenPointer = new fabric.Point(screenCoords.x, screenCoords.y); // Create Point
        this._screenPoints.push(screenPointer); // Store current screen point

		var i, dx, dy, d,
			ctx = this.canvas.contextTop,
            screenPoints = this._screenPoints, // Use screen points for drawing
            lastScreenPoint = screenPoints[screenPoints.length - 2]; // This is a fabric.Point

        if (!lastScreenPoint) return; // Need at least two points to draw

		ctx.beginPath();
		ctx.moveTo(lastScreenPoint.x, lastScreenPoint.y);
		ctx.lineTo(screenPointer.x, screenPointer.y);
		ctx.stroke();

		// Use screen points (fabric.Point instances) for drawing the "fur" lines
		for (i = 0; i < screenPoints.length; i++) {
            // Calculate distance based on screen points for visual effect
			dx = screenPoints[i].x - screenPoints[this._count].x;
			dy = screenPoints[i].y - screenPoints[this._count].y;
			d = dx * dx + dy * dy;

			if (d < 2000 && Math.random() > d / 2000)	{
				ctx.beginPath();
                // Draw lines relative to the current screen pointer
				ctx.moveTo(screenPointer.x + (dx * 0.5), screenPointer.y + (dy * 0.5));
				ctx.lineTo(screenPointer.x - (dx * 0.5), screenPointer.y - (dy * 0.5));
				ctx.stroke();
			}
		}

		this._count++;
        this._drawn = true;
        // No need to update _lastScreenPointer here as we use the array
	},

	onMouseUp: function(options) { // Accept options
		// convertToImg called by BaseBrush.onMouseUp
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._points = [];
        this._screenPoints = [];
        this._count = 0;
    },

	_render: function() {}
}); // End FurBrush

/**
 * InkBrush
 * Based on code by Tennison Chan.
 */
fabric.InkBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 30,

	_baseWidth: 20,
	_inkAmount: 7,
	_lastPoint: null, // Transformed (fabric.Point)
	_point: null,     // Transformed (fabric.Point)
    _lastScreenPoint: null, // Screen (fabric.Point)
    _screenPoint: null,     // Screen (fabric.Point)
	_range: 10,
	_strokes: null,
    // _drawn: false, // Inherited

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || canvas.contextTop.globalAlpha; // Use contextTop's alpha

		this._point = new fabric.Point();
        this._screenPoint = new fabric.Point();
	},

	// Accept options
	_render: function(pointer, options) {
		var len, i,
            // Use transformed points for logic
            point = this.setPointer(pointer, options), // Updates _point and _lastPoint (fabric.Point)
            subtractPoint, distance,
            // Get screen points for drawing
            screenPointer = this.setScreenPointer(options), // Updates _screenPoint and _lastScreenPoint (fabric.Point)
            stroke;

        if (!this._lastPoint || !this._lastScreenPoint) return; // Need previous points

        subtractPoint = point.subtract(this._lastPoint);
        distance = point.distanceFrom(this._lastPoint);

        if (!this._strokes) return; // Ensure strokes are initialized

		for (i = 0, len = this._strokes.length; i < len; i++) {
			stroke = this._strokes[i];
            // Pass both transformed and screen points (fabric.Point) to stroke update
			stroke.update(point, screenPointer, subtractPoint, distance);
			stroke.draw(); // Stroke.draw now uses screen points
		}

		if (distance > 30) { // Distance check based on transformed points is fine
			this.drawSplash(screenPointer, this._inkAmount); // Draw splash at screen location
		}
        this._drawn = true;
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		this.canvas.contextTop.globalAlpha = this.opacity;
		this._resetTip(pointer, options); // Pass options
        // this._drawn = false; // Handled by BaseBrush
	},

	// Accept options
	onMouseMove: function(pointer, options) {
		if (this.canvas._isCurrentlyDrawing) {
			this._render(pointer, options); // Pass options
		}
        // Update last screen pointer (done within setScreenPointer called by _render)
	},

	onMouseUp: function(options) { // Accept options
		// convertToImg called by BaseBrush.onMouseUp
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
		this.canvas.contextTop.globalAlpha = 1; // Reset alpha
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._strokes = null;
        this._point = new fabric.Point();
        this._lastPoint = null;
        this._screenPoint = new fabric.Point();
        this._lastScreenPoint = null;
    },

	// Draw splash at screen coordinates (screenPointer is fabric.Point)
	drawSplash: function(screenPointer, maxSize) {
		var c, r, i, point,
			ctx = this.canvas.contextTop,
			num = fabric.util.getRandom(12),
			range = maxSize * 10,
			color = this.color;

		ctx.save();
		for (i = 0; i < num; i++) {
			r = fabric.util.getRandom(range, 1);
			c = fabric.util.getRandom(Math.PI * 2);
            // Calculate splash point relative to screenPointer
			point = new fabric.Point(screenPointer.x + r * Math.sin(c), screenPointer.y + r * Math.cos(c));

			ctx.fillStyle = color;
			ctx.beginPath();
			ctx.arc(point.x, point.y, fabric.util.getRandom(maxSize) / 2, 0, Math.PI * 2, false);
			ctx.fill();
		}
		ctx.restore();
	},

	// Sets transformed points (returns fabric.Point)
	setPointer: function(pointer, options) {
		var point = new fabric.Point(pointer.x, pointer.y);
		this._lastPoint = this._point ? this._point.clone() : point.clone(); // Clone or initialize
		this._point = point;
		return point;
	},

    // Sets screen points (returns fabric.Point)
    setScreenPointer: function(options) {
        var screenCoords = this.canvas.getPointer(options.e, true);
        if (!screenCoords) {
             return this._screenPoint || new fabric.Point(0,0); // Return last known or default
        }
        var screenPoint = new fabric.Point(screenCoords.x, screenCoords.y); // Create Point
        this._lastScreenPoint = this._screenPoint ? this._screenPoint.clone() : screenPoint.clone(); // Clone or initialize
        this._screenPoint = screenPoint; // Store the new Point
        return screenPoint;
    },

	// Modify to accept options and pass screenPointer (fabric.Point) to Stroke
	_resetTip: function(pointer, options) {
		var point = this.setPointer(pointer, options); // Sets transformed points
        var screenPoint = this.setScreenPointer(options); // Sets screen points

		this._strokes = [];
		this.size = this.width / 5 + this._baseWidth;
		this._range = this.size / 2;

		var i, len;
		for (i = 0, len = this.size; i < len; i++) {
            // Pass both transformed and screen points (fabric.Point) to Stroke constructor
			this._strokes[i] = new fabric.Stroke(this.canvas.contextTop, point, screenPoint, this._range, this.color, this.width, this._inkAmount);
		}
	}
}); // End InkBrush

/**
 * LongfurBrush
 * Based on code by Mr. Doob.
 */
fabric.LongfurBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 1,

	_count: 0,
	_points: [], // Transformed points
    _screenPoints: [], // Screen points (fabric.Point instances)

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || 1;
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		this._points = [pointer];
        const screenCoords = this.canvas.getPointer(options.e, true);
        this._screenPoints = screenCoords ? [new fabric.Point(screenCoords.x, screenCoords.y)] : []; // Store initial screen point as Point
		this._count = 0;
        // this._drawn = false; // Handled by BaseBrush

		var ctx = this.canvas.contextTop,
			color = fabric.util.colorValues(this.color);

		ctx.strokeStyle = 'rgba(' + color[0] + ',' + color[1] + ',' + color[2] + ',' + (0.05 * this.opacity) + ')';
		ctx.lineWidth = this.width;
	},

	// Accept options
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return;

		this._points.push(pointer);
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (!screenCoords) return;
        const screenPointer = new fabric.Point(screenCoords.x, screenCoords.y); // Create Point
        this._screenPoints.push(screenPointer);

		var i, dx, dy, d, size,
			ctx = this.canvas.contextTop,
            screenPoints = this._screenPoints; // Use screen points (fabric.Point instances) for drawing

        if (screenPoints.length < 2) return; // Need points to draw

		for (i = 0; i < screenPoints.length; i++) {
			size = -Math.random();

            // Calculate distance and draw based on screen coordinates
			dx = screenPoints[i].x - screenPoints[this._count].x;
			dy = screenPoints[i].y - screenPoints[this._count].y;
			d = dx * dx + dy * dy;

			if (d < 4000 && Math.random() > d / 4000)	{
				ctx.beginPath();
				ctx.moveTo(screenPoints[this._count].x + (dx * size), screenPoints[this._count].y + (dy * size));
				ctx.lineTo(screenPoints[i].x - (dx * size) + Math.random() * 2, screenPoints[i].y - (dy * size) + Math.random() * 2);
				ctx.stroke();
			}
		}

		this._count++;
        this._drawn = true;
	},

	onMouseUp: function(options) { // Accept options
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
		// convertToImg called by BaseBrush.onMouseUp
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._points = [];
        this._screenPoints = [];
        this._count = 0;
    },

	_render: function() {}
}); // End LongfurBrush

/**
 * MarkerBrush
 * Based on code by Tennison Chan.
 */
fabric.MarkerBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 30,

	_baseWidth: 10,
	_lastPoint: null, // Transformed (fabric.Point)
	_lineWidth: 3,
	_point: null,     // Transformed (fabric.Point) - Not strictly needed for rendering
    _screenPoint: null, // Screen (fabric.Point) - Not strictly needed for rendering
    _lastScreenPoint: null, // Screen (fabric.Point)
	_size: 0,
    // _drawn: false, // Inherited

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		// IMPORTANT: MarkerBrush uses its own opacity property, separate from globalAlpha
		this.opacity = opt.opacity || 1;
		// Do NOT set canvas.contextTop.globalAlpha here, manage it per stroke in _render

		this._point = new fabric.Point(); // Initialize, though not used in render
        this._screenPoint = new fabric.Point(); // Initialize, though not used in render

		this.canvas.contextTop.lineJoin = 'round';
		this.canvas.contextTop.lineCap = 'round';
	},

	// Accept options, use screen points for drawing
	_render: function(pointer, options) {
        // Ensure _lastScreenPoint is a fabric.Point
        if (!this._lastScreenPoint) return;

		var ctx = this.canvas.contextTop,
            lineWidthDiff, i, len,
            currentScreenCoords = this.canvas.getPointer(options.e, true);

        if (!currentScreenCoords) return;
        const currentScreenPoint = new fabric.Point(currentScreenCoords.x, currentScreenCoords.y); // Create Point

		ctx.save(); // Save context state
        ctx.strokeStyle = this.color; // Set color for this render pass
        ctx.lineWidth = this._lineWidth; // Set line width

		ctx.beginPath();
		for(i = 0, len = (this._size / this._lineWidth) / 2; i < len; i++) {
			lineWidthDiff = (this._lineWidth - 1) * i;

			// Set alpha per line segment for the marker effect
			ctx.globalAlpha = 0.8 * this.opacity;
			ctx.moveTo(this._lastScreenPoint.x + lineWidthDiff, this._lastScreenPoint.y + lineWidthDiff);
			ctx.lineTo(currentScreenPoint.x + lineWidthDiff, currentScreenPoint.y + lineWidthDiff);
			ctx.stroke(); // Stroke each segment individually
		}
		ctx.restore(); // Restore context state (including globalAlpha)

        // Update transformed point (optional, if needed elsewhere)
		this._lastPoint = new fabric.Point(pointer.x, pointer.y);
        // Update screen point for the next segment
        this._lastScreenPoint = currentScreenPoint; // Store the fabric.Point
        this._drawn = true;
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		this._lastPoint = pointer; // Store transformed point
        this._lastScreenPoint = this._lastScreenPointer ? this._lastScreenPointer.clone() : null; // Use BaseBrush's _lastScreenPointer
		this._size = this.width + this._baseWidth;
        // this._drawn = false; // Handled by BaseBrush
	},

	// Accept options
	onMouseMove: function(pointer, options) {
		if (this.canvas._isCurrentlyDrawing) {
			this._render(pointer, options); // Pass options
		}
	},

	onMouseUp: function(options) { // Accept options
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
		// convertToImg called by BaseBrush.onMouseUp
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._point = new fabric.Point();
        this._lastPoint = null;
        this._screenPoint = new fabric.Point();
        this._lastScreenPoint = null;
    }
}); // End MarkerBrush

/**
 * RibbonBrush
 * Based on code by Mr. Doob.
 */
fabric.RibbonBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 1,

	_nrPainters: 50,
	_painters: [],
	_lastPoint: null, // Transformed point (fabric.Point)
    _lastScreenPoint: null, // Screen point for update logic (fabric.Point)
	_interval: null,
    // _drawn: false, // Inherited

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || 1;

        // Initialize painters relative to canvas size (might need adjustment if canvas resizes)
		for (var i = 0; i < this._nrPainters; i++) {
			this._painters.push({ dx:this.canvas.width/2, dy:this.canvas.height/2, ax:0, ay:0, div:.1, ease:Math.random() * .2 + .6 });
		}
	},

	// Update uses screen coordinates for drawing
	update: function() {
        // Ensure _lastScreenPoint is a fabric.Point
        if (!this._lastScreenPoint) return; // Need a point to move towards

		var ctx = this.canvas.contextTop, painters = this._painters;
		for (var i = 0; i < painters.length; i++)	{
			ctx.beginPath();
			ctx.moveTo(painters[i].dx, painters[i].dy);
            // Calculate acceleration based on the distance to the last *screen* point
			painters[i].dx -= painters[i].ax = (painters[i].ax + (painters[i].dx - this._lastScreenPoint.x) * painters[i].div) * painters[i].ease;
			painters[i].dy -= painters[i].ay = (painters[i].ay + (painters[i].dy - this._lastScreenPoint.y) * painters[i].div) * painters[i].ease;
			ctx.lineTo(painters[i].dx, painters[i].dy);
			ctx.stroke();
		}
        this._drawn = true; // Mark as drawn during update
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		var ctx = this.canvas.contextTop,
			color = fabric.util.colorValues(this.color);

		this._painters = [];
        const screenCoords = this.canvas.getPointer(options.e, true);
        const startX = screenCoords ? screenCoords.x : pointer.x; // Fallback
        const startY = screenCoords ? screenCoords.y : pointer.y; // Fallback

		for (var i = 0; i < this._nrPainters; i++) {
            // Initialize painters at the starting screen position
			this._painters.push({ dx: startX, dy: startY, ax:0, ay:0, div:.1, ease:Math.random() * .2 + .6 });
		}

		this._lastPoint = pointer; // Store transformed point
        this._lastScreenPoint = this._lastScreenPointer ? this._lastScreenPointer.clone() : new fabric.Point(startX, startY); // Use BaseBrush's _lastScreenPointer

		ctx.strokeStyle = 'rgba(' + color[0] + ',' + color[1] + ',' + color[2] + ',' + (0.05 * this.opacity) + ')';
		ctx.lineWidth = this.width;

		var self = this;
        clearInterval(this._interval); // Clear any previous interval
		this._interval = setInterval(function(){ self.update() }, 1000/60);
        // this._drawn = false; // Handled by BaseBrush
	},

	// Accept options
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return;
		this._lastPoint = pointer; // Update transformed point
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (screenCoords) {
            this._lastScreenPoint = new fabric.Point(screenCoords.x, screenCoords.y); // Update screen point for the update function
        }
	},

	onMouseUp: function(options) { // Accept options
		clearInterval(this._interval);
        this._interval = null;
		// convertToImg called by BaseBrush.onMouseUp
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        clearInterval(this._interval);
        this._interval = null;
        this._painters = [];
        this._lastPoint = null;
        this._lastScreenPoint = null;
        // Reinitialize painters if needed, or do it in onMouseDown
		// for (var i = 0; i < this._nrPainters; i++) {
		// 	this._painters.push({ dx:this.canvas.width/2, dy:this.canvas.height/2, ax:0, ay:0, div:.1, ease:Math.random() * .2 + .6 });
		// }
    },

	_render: function() {} // Drawing handled by interval timer
}); // End RibbonBrush

/**
 * ShadedBrush
 * Based on code by Mr. Doob.
 */
fabric.ShadedBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: .1,
	width: 1,
	shadeDistance: 1000,

	_points: [], // Transformed points
    _screenPoints: [], // Screen points (fabric.Point instances)

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || .3;
		this.shadeDistance = opt.shadeDistance || 1000; // Consider scaling this with zoom? Maybe not necessary.
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		this._points = [pointer];
        const screenCoords = this.canvas.getPointer(options.e, true);
        this._screenPoints = screenCoords ? [new fabric.Point(screenCoords.x, screenCoords.y)] : []; // Store initial screen point as Point
        // this._drawn = false; // Handled by BaseBrush

		var ctx = this.canvas.contextTop,
			color = fabric.util.colorValues(this.color);

		ctx.strokeStyle = 'rgba(' + color[0] + ',' + color[1] + ',' + color[2] + ',' + this.opacity + ')';
		ctx.lineWidth = this.width;
		ctx.lineJoin = ctx.lineCap = 'round';
	},

	// Accept options
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return;

		this._points.push(pointer);
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (!screenCoords) return;
        const screenPointer = new fabric.Point(screenCoords.x, screenCoords.y); // Create Point
        this._screenPoints.push(screenPointer);

		var ctx = this.canvas.contextTop,
            screenPoints = this._screenPoints, // Use screen points (fabric.Point instances) for drawing
            dx, dy, d, i, len;

        if (screenPoints.length < 2) return;

        const lastScreenPoint = screenPoints[screenPoints.length - 2]; // fabric.Point
        const currentScreenPoint = screenPoints[screenPoints.length - 1]; // fabric.Point

		ctx.beginPath();
		ctx.moveTo(lastScreenPoint.x, lastScreenPoint.y);
		ctx.lineTo(currentScreenPoint.x, currentScreenPoint.y);
		ctx.stroke();

        // Draw shading lines based on screen coordinates
		for (i = 0, len = screenPoints.length; i < len; i++) {
			dx = screenPoints[i].x - currentScreenPoint.x;
			dy = screenPoints[i].y - currentScreenPoint.y;
			d = dx * dx + dy * dy;

			if (d < this.shadeDistance) { // Use original shadeDistance logic
				ctx.beginPath();
				ctx.moveTo( currentScreenPoint.x + (dx * 0.2), currentScreenPoint.y + (dy * 0.2));
				ctx.lineTo( screenPoints[i].x - (dx * 0.2), screenPoints[i].y - (dy * 0.2));
				ctx.stroke();
			}
		}
        this._drawn = true;
	},

	onMouseUp: function(options) { // Accept options
		// convertToImg called by BaseBrush.onMouseUp
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._points = [];
        this._screenPoints = [];
    },

	_render: function() {}
}); // End ShadedBrush

/**
 * SketchyBrush
 * Based on code by Mr. Doob.
 */
fabric.SketchyBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 1,

	_count: 0,
	_points: [], // Transformed
    _screenPoints: [], // Screen (fabric.Point instances)

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || 1;
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		this._count = 0;
		this._points = [pointer];
        const screenCoords = this.canvas.getPointer(options.e, true);
        this._screenPoints = screenCoords ? [new fabric.Point(screenCoords.x, screenCoords.y)] : []; // Store initial screen point as Point
        // this._drawn = false; // Handled by BaseBrush

		var ctx = this.canvas.contextTop,
			color = fabric.util.colorValues(this.color);

		ctx.strokeStyle = 'rgba(' + color[0] + ',' + color[1] + ',' + color[2] + ',' + (0.05 * this.opacity) + ')';
		ctx.lineWidth = this.width;
	},

	// Accept options
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return;

		this._points.push(pointer);
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (!screenCoords) return;
        const screenPointer = new fabric.Point(screenCoords.x, screenCoords.y); // Create Point
        this._screenPoints.push(screenPointer);

		var i, dx, dy, d, factor = .3 * this.width,
			ctx = this.canvas.contextTop,
            screenPoints = this._screenPoints, // Use screen points (fabric.Point instances) for drawing
			count = this._count;

        if (screenPoints.length < 2) return;

        const lastScreenPoint = screenPoints[screenPoints.length - 2]; // fabric.Point
        const currentScreenPoint = screenPoints[screenPoints.length - 1]; // fabric.Point

		ctx.beginPath();
		ctx.moveTo(lastScreenPoint.x, lastScreenPoint.y);
		ctx.lineTo(currentScreenPoint.x, currentScreenPoint.y);
		ctx.stroke();

        // Draw sketchy lines based on screen coordinates
		for (i = 0; i < screenPoints.length; i++) {
			dx = screenPoints[i].x - screenPoints[count].x;
			dy = screenPoints[i].y - screenPoints[count].y;
			d = dx * dx + dy * dy;

			if (d < 4000 && Math.random() > d / 2000)	{ // Logic based on screen distance
				ctx.beginPath();
				ctx.moveTo(screenPoints[count].x + (dx * factor), screenPoints[count].y + (dy * factor));
				ctx.lineTo(screenPoints[i].x - (dx * factor), screenPoints[i].y - (dy * factor));
				ctx.stroke();
			}
		}

		this._count++;
        this._drawn = true;
	},

	onMouseUp: function(options) { // Accept options
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
		// convertToImg called by BaseBrush.onMouseUp
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._points = [];
        this._screenPoints = [];
        this._count = 0;
    },

	_render: function() {}
}); // End SketchyBrush

/**
 * SpraypaintBrush
 * Based on code by Tennison Chan.
 * Simplified to use fillRect instead of external image for better color control and reliability.
 */
fabric.SpraypaintBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 30,
    density: 20,         // How many particles per interval
    dotWidth: 1,         // Base size of particles
    dotWidthVariance: 0, // Random variation in particle size
    randomOpacity: false,// Use random opacity for particles

	_interval: 10, // Milliseconds between spray bursts
	_sprayChunks: [], // Stores particle data {x, y, width, opacity}
	_renderTimer: null, // Timer for spray effect
    _screenPoint: null, // Current screen pointer (fabric.Point)
	// _drawn: false, // Inherited

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.opacity = opt.opacity || 1; // Use provided opacity or default to 1
		this.color = opt.color || canvas.freeDrawingBrush.color;
        this.density = opt.density || 20;
        this.dotWidth = opt.dotWidth || 1;
        this.dotWidthVariance = opt.dotWidthVariance || 0;
        this.randomOpacity = opt.randomOpacity || false;
        this._interval = opt.interval || 10; // Allow interval override

        this._screenPoint = new fabric.Point(); // Initialize
		this._reset();
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer

        const screenCoords = this.canvas.getPointer(options.e, true);
        if (screenCoords) {
            this._screenPoint = new fabric.Point(screenCoords.x, screenCoords.y); // Store initial screen point
        } else {
            this._screenPoint = new fabric.Point(pointer.x, pointer.y); // Fallback
        }

		this._sprayChunks = []; // Reset spray chunks
        // this._drawn = false; // Handled by BaseBrush

        // Start the spray interval
        this.scheduleSpray();
	},

	// Accept options
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return;

        // Update the current screen point
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (screenCoords) {
            this._screenPoint = new fabric.Point(screenCoords.x, screenCoords.y);
        }

        // Add spray chunks immediately on move for responsiveness
        this.addSprayChunks(this._screenPoint);
        this._drawn = true;
	},

	onMouseUp: function(options) { // Accept options
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
        clearTimeout(this._renderTimer); // Stop the spray interval
        this._renderTimer = null;
		// convertToImg called by BaseBrush.onMouseUp
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        clearTimeout(this._renderTimer);
        this._renderTimer = null;
        this._screenPoint = new fabric.Point();
        this._sprayChunks = [];
    },

    // Add spray particles based on current screen position (fabric.Point)
    addSprayChunks: function(screenPointer) {
        if (!screenPointer) return;
        var points = this.density; // Use density property
        while (points--) {
            var dotWidth = this.dotWidth,
                offsetX = fabric.util.getRandom(this.width / 2, -this.width / 2),
                offsetY = fabric.util.getRandom(this.width / 2, -this.width / 2);

            if (this.dotWidthVariance > 0) {
                dotWidth = fabric.util.getRandom(this.dotWidth + this.dotWidthVariance, this.dotWidth - this.dotWidthVariance);
                dotWidth = Math.max(1, dotWidth); // Ensure minimum width of 1
            }

            var opacity = this.opacity;
            if (this.randomOpacity) {
                opacity = fabric.util.getRandom(this.opacity);
            }

            // Store screen coordinates for drawing
            this._sprayChunks.push({
                x: screenPointer.x + offsetX,
                y: screenPointer.y + offsetY,
                width: dotWidth,
                opacity: opacity
            });
        }
    },

    // Schedule the next spray burst
    scheduleSpray: function() {
        if (!this.canvas._isCurrentlyDrawing) {
            clearTimeout(this._renderTimer);
            this._renderTimer = null;
            return;
        }

        // Add chunks at the current location
        this.addSprayChunks(this._screenPoint);
        this._drawn = true; // Mark as drawn if adding chunks

        // Render all accumulated chunks
        this._render();

        // Schedule the next burst
        var self = this;
        this._renderTimer = setTimeout(function() { self.scheduleSpray(); }, this._interval);
    },

	// Render the spray particles onto contextTop
	_render: function() {
        var ctx = this.canvas.contextTop;
        ctx.save();
        ctx.fillStyle = this.color; // Use the brush color

        // Clear only the area needed (optimization - might need adjustment)
        // ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height); // Or clear only affected area

        var chunks = this._sprayChunks;
        for (var i = 0, len = chunks.length; i < len; i++) {
            var chunk = chunks[i];
            ctx.globalAlpha = chunk.opacity; // Apply individual opacity
            // Draw small rectangles (dots)
            ctx.fillRect(Math.floor(chunk.x), Math.floor(chunk.y), Math.max(1, Math.floor(chunk.width)), Math.max(1, Math.floor(chunk.width)));
        }
        ctx.restore();

        // Optional: Limit the number of chunks to prevent memory issues
        // if (this._sprayChunks.length > 10000) {
        //     this._sprayChunks.splice(0, this._sprayChunks.length - 10000);
        // }
	}
}); // End SpraypaintBrush


/**
 * SquaresBrush
 * Based on code by Mr. Doob.
 */
fabric.SquaresBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	bgColor: '#fff',
	opacity: 1,
	width: 1,

	_lastPoint: null, // Transformed (fabric.Point)
    _lastScreenPoint: null, // Screen (fabric.Point)
	// _drawn: false, // Inherited

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.bgColor = opt.bgColor || '#fff'; // Background color for the squares
		this.opacity = opt.opacity || canvas.contextTop.globalAlpha; // Use contextTop's alpha
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		var ctx = this.canvas.contextTop,
			color = fabric.util.colorValues(this.color),
			bgColor = fabric.util.colorValues(this.bgColor);

		this._lastPoint = pointer; // Store transformed point
        this._lastScreenPoint = this._lastScreenPointer ? this._lastScreenPointer.clone() : null; // Use BaseBrush's _lastScreenPointer
		// this._drawn = false; // Handled by BaseBrush

		this.canvas.contextTop.globalAlpha = this.opacity;
		ctx.fillStyle = bgColor ? 'rgba(' + bgColor[0] + ',' + bgColor[1] + ',' + bgColor[2] + ',' + bgColor[3] + ')' : 'transparent';
		ctx.strokeStyle = color ? 'rgba(' + color[0] + ',' + color[1] + ',' + color[2] + ',' + color[3] + ')' : 'transparent';
		ctx.lineWidth = this.width;
	},

	// Accept options, draw using screen coordinates
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing || !this._lastScreenPoint) return;

        const screenCoords = this.canvas.getPointer(options.e, true);
        if (!screenCoords) return;
        const screenPointer = new fabric.Point(screenCoords.x, screenCoords.y); // Create Point

		var ctx = this.canvas.contextTop,
            // Calculate delta in screen coordinates
			dx = screenPointer.x - this._lastScreenPoint.x,
			dy = screenPointer.y - this._lastScreenPoint.y,
			angle = 1.57079633, // 90 degrees
            // Calculate perpendicular offsets based on screen delta and brush width
			px = (Math.cos(angle) * dx - Math.sin(angle) * dy) * (this.width / 2), // Scale offset by width/2
			py = (Math.sin(angle) * dx + Math.cos(angle) * dy) * (this.width / 2);

		ctx.beginPath();
        // Use screen coordinates (fabric.Point instances) for drawing the square
		ctx.moveTo(this._lastScreenPoint.x - px, this._lastScreenPoint.y - py);
		ctx.lineTo(this._lastScreenPoint.x + px, this._lastScreenPoint.y + py);
		ctx.lineTo(screenPointer.x + px, screenPointer.y + py);
		ctx.lineTo(screenPointer.x - px, screenPointer.y - py);
		ctx.lineTo(this._lastScreenPoint.x - px, this._lastScreenPoint.y - py);
		ctx.fill();
		ctx.stroke();

		this._lastPoint = pointer; // Update transformed point
        this._lastScreenPoint = screenPointer; // Update screen point (already a Point)
		this._drawn = true;
	},

	onMouseUp: function(options) { // Accept options
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
		// convertToImg called by BaseBrush.onMouseUp
		this.canvas.contextTop.globalAlpha = 1; // Reset alpha
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._lastPoint = null;
        this._lastScreenPoint = null;
    },

	_render: function() {}
}); // End SquaresBrush

/**
 * WebBrush
 * Based on code by Mr. Doob.
 */
fabric.WebBrush = fabric.util.createClass(fabric.BaseBrush, {
	color: '#000',
	opacity: 1,
	width: 1,

	_count: 0,
	_points: [], // Transformed
    _screenPoints: [], // Screen (fabric.Point instances)
    _colorValues: null, // Store parsed color

	initialize: function(canvas, opt) {
		opt = opt || {};

		this.canvas = canvas;
		this.width = opt.width || canvas.freeDrawingBrush.width;
		this.color = opt.color || canvas.freeDrawingBrush.color;
		this.opacity = opt.opacity || 1;
	},

	// Accept options
	onMouseDown: function(pointer, options) {
        fabric.BaseBrush.prototype.onMouseDown.call(this, pointer, options); // Sets _lastScreenPointer
		this._points = [pointer];
        const screenCoords = this.canvas.getPointer(options.e, true);
        this._screenPoints = screenCoords ? [new fabric.Point(screenCoords.x, screenCoords.y)] : []; // Store initial screen point as Point
		this._count = 0;
		this._colorValues = fabric.util.colorValues(this.color);
        // this._drawn = false; // Handled by BaseBrush
	},

	// Accept options, draw using screen coordinates
	onMouseMove: function(pointer, options) {
        if (!this.canvas._isCurrentlyDrawing) return;

		this._points.push(pointer);
        const screenCoords = this.canvas.getPointer(options.e, true);
        if (!screenCoords) return;
        const screenPointer = new fabric.Point(screenCoords.x, screenCoords.y); // Create Point
        this._screenPoints.push(screenPointer);

		var ctx = this.canvas.contextTop,
            screenPoints = this._screenPoints, // Use screen points (fabric.Point instances) for drawing
			lastScreenPoint = screenPoints[screenPoints.length - 2], // fabric.Point
			colorValues = this._colorValues,
			i, dx, dy, d;

        if (!lastScreenPoint || !colorValues) return; // Ensure points and color are valid

		ctx.lineWidth = this.width;
		ctx.strokeStyle = 'rgba(' + colorValues[0] + ',' + colorValues[1] + ',' + colorValues[2] + ',' + (.5 * this.opacity) + ')';

		ctx.beginPath();
		ctx.moveTo(lastScreenPoint.x, lastScreenPoint.y);
		ctx.lineTo(screenPointer.x, screenPointer.y);
		ctx.stroke();

		ctx.strokeStyle = 'rgba(' + colorValues[0] + ',' + colorValues[1] + ',' + colorValues[2] + ',' + (.1 * this.opacity) + ')';

        // Draw web lines based on screen coordinates
		for (i = 0; i < screenPoints.length; i++) {
			dx = screenPoints[i].x - screenPoints[this._count].x;
			dy = screenPoints[i].y - screenPoints[this._count].y;
			d = dx * dx + dy * dy;

			if (d < 2500 && Math.random() > .9) { // Logic based on screen distance
				ctx.beginPath();
				ctx.moveTo(screenPoints[this._count].x, screenPoints[this._count].y);
				ctx.lineTo(screenPoints[i].x, screenPoints[i].y);
				ctx.stroke();
			}
		}
		this._count++;
        this._drawn = true;
	},

	onMouseUp: function(options) { // Accept options
		fabric.BaseBrush.prototype.onMouseUp.call(this, options);
		// convertToImg called by BaseBrush.onMouseUp
        this._reset();
	},

    _reset: function() {
        fabric.BaseBrush.prototype._reset.call(this);
        this._points = [];
        this._screenPoints = [];
        this._count = 0;
        this._colorValues = null;
    },

	_render: function() {}
}); // End WebBrush

})(typeof fabric !== 'undefined' ? fabric : require('fabric').fabric);
