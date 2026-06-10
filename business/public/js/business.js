// business app — plan Essential
// =============================================================================
// Animation des icônes du desktop (page /desk)
// - Entrée en cascade (fade + slide + rotation/scale) au rendu de la page
// - Effet de survol (scale + légère rotation) géré en CSS (business_desk.css)
//
// IMPORTANT : tout est fait ici, dans l'app `business`. Aucun fichier standard
// Frappe/ERPNext n'est modifié. On observe le DOM rendu par
// `frappe/desk/page/desktop/desktop.js` et on anime les icônes après leur rendu.
//
// Robustesse : on tente GSAP (CDN) pour un easing « rebond » ; si GSAP n'est
// pas disponible (offline / CDN bloqué), on retombe sur une animation CSS pure
// (@keyframes businessIconIn) qui donne le même rendu, sans dépendance externe.
// =============================================================================

(function () {
	"use strict";

	const GSAP_SRC = "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js";
	const GSAP_TIMEOUT = 2000; // ms avant de basculer sur le fallback CSS

	const ROOT = document.documentElement;
	const animated = new WeakSet(); // conteneurs déjà animés (évite de rejouer)
	let ready = false; // true dès qu'on sait quel chemin utiliser (GSAP ou CSS)
	let use_css = false; // true => fallback CSS (GSAP indisponible)
	let raf = null;

	// --- chargement de GSAP -------------------------------------------------
	function on_ready(css_fallback) {
		ready = true;
		use_css = !!css_fallback;
		schedule();
	}

	function load_gsap() {
		if (window.gsap) {
			on_ready(false);
			return;
		}
		if (document.querySelector("script[data-business-gsap]")) return;

		const s = document.createElement("script");
		s.src = GSAP_SRC;
		s.async = true;
		s.setAttribute("data-business-gsap", "1");
		s.onload = function () {
			on_ready(false);
		};
		s.onerror = function () {
			on_ready(true); // CDN injoignable -> fallback CSS
		};
		document.head.appendChild(s);

		// Si GSAP n'a pas répondu à temps, on bascule sur le fallback CSS.
		setTimeout(function () {
			if (!ready) on_ready(true);
		}, GSAP_TIMEOUT);
	}

	// --- ciblage des icônes -------------------------------------------------
	// Grille principale uniquement (on exclut les mini-icônes des dossiers).
	function get_main_container() {
		return document.querySelector(".desktop-container > .icons-container");
	}
	function get_top_level_icons(container) {
		return container.querySelectorAll(":scope > .icons > .desktop-icon");
	}

	// --- animations ---------------------------------------------------------
	function animate_with_gsap(icons) {
		window.gsap.killTweensOf(icons);
		window.gsap.fromTo(
			icons,
			{ opacity: 0, y: 26, scale: 0.82, rotation: -8 },
			{
				opacity: 1,
				y: 0,
				scale: 1,
				rotation: 0,
				duration: 0.5,
				ease: "back.out(1.6)",
				stagger: 0.05,
				overwrite: true,
				// On nettoie le transform pour laisser le survol CSS reprendre la
				// main. L'opacité reste inline (=1) et neutralise le pré-masquage.
				clearProps: "transform",
			}
		);
	}

	function animate_with_css(icons) {
		icons.forEach(function (el, i) {
			el.style.animation =
				"businessIconIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both";
			el.style.animationDelay = i * 0.05 + "s";
			el.addEventListener("animationend", function handler(e) {
				if (e.target !== el) return; // ignore les bulles d'enfants
				el.style.animation = "";
				el.style.animationDelay = "";
				el.style.opacity = "1"; // neutralise le pré-masquage, garde l'icône visible
				el.removeEventListener("animationend", handler);
			});
		});
	}

	function animate() {
		const container = get_main_container();
		if (!container || animated.has(container)) return;

		const icons = get_top_level_icons(container);
		if (!icons.length) return; // pas encore rendu, on réessaiera

		animated.add(container);

		// Pas d'animation en mode édition (réorganisation des icônes).
		const page = window.frappe && frappe.pages && frappe.pages["desktop"];
		const edit_mode = page && page.desktop_page && page.desktop_page.edit_mode;
		if (edit_mode) {
			ROOT.classList.remove("business-anim"); // s'assurer qu'elles restent visibles
			return;
		}

		if (!use_css && window.gsap) {
			animate_with_gsap(icons);
		} else {
			animate_with_css(icons);
		}
	}

	// rAF anti-rebond : l'observer peut déclencher plusieurs fois pendant le rendu.
	function schedule() {
		if (!ready) return;
		if (raf) cancelAnimationFrame(raf);
		raf = requestAnimationFrame(function () {
			raf = null;
			animate();
		});
	}

	// --- fond animé ambiant -------------------------------------------------
	// Formes géométriques discrètes qui « tombent » lentement, DERRIÈRE les
	// icônes (cf. .business-bg dans business_desk.css). Injecté dans
	// .desktop-wrapper, reconstruit à chaque re-rendu du desktop.
	function build_background() {
		const wrapper = document.querySelector(".desktop-wrapper");
		if (!wrapper) return;
		if (wrapper.querySelector(":scope > .business-bg")) return; // déjà présent
		// On respecte la préférence « réduire les animations ».
		if (
			window.matchMedia &&
			window.matchMedia("(prefers-reduced-motion: reduce)").matches
		) {
			return;
		}

		const bg = document.createElement("div");
		bg.className = "business-bg";
		bg.setAttribute("aria-hidden", "true");

		const COUNT = 14;
		for (let i = 0; i < COUNT; i++) {
			const shape = document.createElement("span");
			shape.className = "business-bg-shape";
			if (i % 3 === 0) shape.classList.add("is-round"); // quelques cercles
			if (i % 4 === 0) shape.classList.add("is-soft"); // léger flou -> profondeur

			const size = 22 + Math.random() * 70;
			shape.style.width = size + "px";
			shape.style.height = size + "px";
			shape.style.left = (Math.random() * 100).toFixed(2) + "%";
			shape.style.opacity = (0.04 + Math.random() * 0.06).toFixed(3);
			shape.style.setProperty("--sway", (Math.random() * 80 - 40).toFixed(0) + "px");
			shape.style.setProperty("--spin", (Math.random() * 220 - 110).toFixed(0) + "deg");
			shape.style.animationDuration = (20 + Math.random() * 22).toFixed(1) + "s";
			// Délai négatif -> les formes sont déjà réparties à l'écran au départ.
			shape.style.animationDelay = (-Math.random() * 40).toFixed(1) + "s";
			bg.appendChild(shape);
		}
		wrapper.insertBefore(bg, wrapper.firstChild);
	}

	// --- observation du DOM -------------------------------------------------
	// Le desktop est re-rendu à chaque affichage (et en mode édition).
	function observe() {
		const obs = new MutationObserver(function (mutations) {
			for (const m of mutations) {
				for (const node of m.addedNodes) {
					if (node.nodeType !== 1) continue;
					const hit =
						(node.matches &&
							(node.matches(".icons-container") ||
								node.matches(".desktop-container"))) ||
						(node.querySelector && node.querySelector(".icons-container"));
					if (hit) {
						build_background();
						schedule();
						return;
					}
				}
			}
		});
		obs.observe(document.body, { childList: true, subtree: true });
	}

	// --- init ---------------------------------------------------------------
	function init() {
		// Active le pré-masquage CSS au plus tôt pour éviter un flash.
		ROOT.classList.add("business-anim");
		load_gsap();
		observe();
		build_background(); // cas où la page est déjà rendue
		schedule();
	}

	if (document.body) {
		init();
	} else {
		document.addEventListener("DOMContentLoaded", init);
	}
})();

// ── Fix POS ERPNext v16 — côté client ────────────────────────────────────────
// Les données de boot Frappe (frappe.boot.user.can_read) sont calculées à partir
// des rôles uniquement, pas via le hook has_permission Python. Même avec le hook
// serveur (business/overrides/pos_perm.py), le formulaire interne créé par le POS
// via frm.refresh() appelle has_read_permission() → lit this.perm[0].read issu
// du boot → retourne 0 → bloque setup() → script_manager undefined → TypeError.
//
// Ce patch est scopé à la route "point-of-sale" : le formulaire interne n'est
// jamais affiché directement à l'utilisateur ; l'accès réel est contrôlé par le
// Profil PDV et l'Entrée d'ouverture (vérifiés côté serveur via le hook Python).
(function () {
	var _orig = frappe.ui.form.Form.prototype.has_read_permission;
	frappe.ui.form.Form.prototype.has_read_permission = function () {
		if (frappe.get_route && frappe.get_route()[0] === "point-of-sale") {
			return 1;
		}
		return _orig.call(this);
	};
})();
