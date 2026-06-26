"""
parametres.py — Fenêtre des paramètres de MemeClicker
=======================================================
Contrôle le volume de la musique et des effets sonores (SFX).
Les réglages sont sauvegardés dans ~/.memeclicker_settings.json
et relus automatiquement par le jeu à chaque démarrage.
"""

import tkinter as tk
from tkinter import ttk
import json
import os

from audio_manager import audio

# ── Fichier de sauvegarde des paramètres ──────────────────────────────────────
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".memeclicker_settings.json")

DEFAULT_SETTINGS = {
    "music_volume": 50,
    "sfx_volume":   70,
}

# ── Palette (reprend celle du jeu) ────────────────────────────────────────────
BG_TEAL    = "#145a76"
PANEL_GRAY = "#d9d9d9"
BTN_BLUE   = "#1f618d"
WHITE      = "#ffffff"


# ── Utilitaires de persistance ────────────────────────────────────────────────
def load_settings() -> dict:
    """Charge les paramètres depuis le fichier JSON (crée les valeurs par défaut si absent)."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return {**DEFAULT_SETTINGS, **data}
        except (OSError, json.JSONDecodeError):
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    """Sauvegarde les paramètres dans le fichier JSON."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2)
    except OSError:
        pass


# ── Interface ─────────────────────────────────────────────────────────────────
class ParametresWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("MemeClicker — Paramètres")
        self.resizable(False, False)
        self.configure(bg=BG_TEAL)

        # Charger les réglages existants
        settings = load_settings()
        self._music_vol = tk.IntVar(value=settings["music_volume"])
        self._sfx_vol   = tk.IntVar(value=settings["sfx_volume"])

        self._build_ui()
        self._center_window(420, 320)

        # Musique de fond continue + sfx sur tous les boutons de cette fenêtre
        audio.start_music()
        self._brancher_sfx_sur_boutons()

    # ── Construction de l'interface ──────────────────────────────────────────
    def _build_ui(self):
        # ── En-tête ──
        tk.Label(
            self, text="⚙️  PARAMÈTRES",
            font=("Arial", 22, "bold"),
            bg=BG_TEAL, fg=WHITE,
        ).pack(pady=(24, 16))

        # ── Carte principale ──
        card = tk.Frame(self, bg=PANEL_GRAY, bd=4, relief="solid")
        card.pack(padx=30, pady=0, fill="both")

        self._make_slider_row(
            card,
            label="🎵  Volume Musique",
            var=self._music_vol,
            row=0,
        )

        ttk.Separator(card, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=6, padx=12
        )

        self._make_slider_row(
            card,
            label="🔊  Volume SFX",
            var=self._sfx_vol,
            row=2,
        )

        # ── Boutons ──
        btn_frame = tk.Frame(self, bg=BG_TEAL)
        btn_frame.pack(pady=20, fill="x", padx=30)

        tk.Button(
            btn_frame, text="💾  Sauvegarder",
            font=("Arial", 13, "bold"),
            bg=BTN_BLUE, fg=WHITE, relief="flat",
            width=16, height=2,
            command=self._save_and_close,
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_frame, text="✖  Annuler",
            font=("Arial", 13, "bold"),
            bg="#ff0000", fg=WHITE, relief="flat",
            width=12, height=2,
            command=self.destroy,
        ).pack(side="left")

    def _make_slider_row(self, parent: tk.Frame, label: str, var: tk.IntVar, row: int):
        """Crée une ligne : label — slider — valeur %"""
        parent.grid_columnconfigure(1, weight=1)

        tk.Label(
            parent, text=label,
            font=("Arial", 13, "bold"),
            bg=PANEL_GRAY, width=20, anchor="w",
        ).grid(row=row, column=0, padx=(16, 8), pady=14, sticky="w")

        slider = ttk.Scale(
            parent, from_=0, to=100,
            orient="horizontal", variable=var,
            command=lambda v, lbl=None: self._update_pct_label(var, lbl),
        )
        slider.grid(row=row, column=1, sticky="ew", padx=8)

        pct_lbl = tk.Label(
            parent, text=f"{var.get():3d} %",
            font=("Arial", 12, "bold"),
            bg=PANEL_GRAY, fg=BTN_BLUE, width=6,
        )
        pct_lbl.grid(row=row, column=2, padx=(4, 16))

        # Relier le slider à son label de valeur
        slider.config(
            command=lambda v, lbl=pct_lbl: self._update_pct_label(var, lbl)
        )

    # ── Callbacks ────────────────────────────────────────────────────────────
    @staticmethod
    def _update_pct_label(var: tk.IntVar, lbl: tk.Label):
        """Met à jour le label '% ' à côté du slider."""
        if lbl is not None:
            lbl.config(text=f"{int(float(var.get())):3d} %")

    def _save_and_close(self):
        """Sauvegarde les réglages et ferme la fenêtre."""
        save_settings({
            "music_volume": int(self._music_vol.get()),
            "sfx_volume":   int(self._sfx_vol.get()),
        })
        audio.refresh_volumes()
        self.destroy()

    def _brancher_sfx_sur_boutons(self):
        """Fait jouer un sfx aléatoire à chaque clic sur n'importe quel bouton de la fenêtre."""
        for widget in self.winfo_children():
            self._brancher_sfx_recursif(widget)

    def _brancher_sfx_recursif(self, widget):
        if isinstance(widget, tk.Button):
            widget.bind("<Button-1>", audio.play_random_sfx, add="+")
        for enfant in widget.winfo_children():
            self._brancher_sfx_recursif(enfant)

    # ── Centrage de la fenêtre ────────────────────────────────────────────────
    def _center_window(self, w: int, h: int):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


# ── Point d'entrée ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ParametresWindow()
    app.mainloop()
