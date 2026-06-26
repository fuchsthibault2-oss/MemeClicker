#!/usr/bin/env python3
"""
MemeClicker FINAL — fusion de meme_clicker.py et main_1_.py
------------------------------------------------------------
Version modifiée : Difficulté accrue + transitions d'étapes instantanées.
"""

import tkinter as tk
from tkinter import font as tkfont, ttk
import json
import os
import sys
import subprocess
import random

from audio_manager import audio

# ======================================================================
# DOSSIER DES IMAGES
# ======================================================================
from PIL import Image, ImageTk

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
IMAGE_SIZE  = (52, 52)   # taille d'affichage dans la boutique (pixels)

# ======================================================================
# PALETTE DE COULEURS
# ======================================================================
BG_TEAL   = "#145a76"
PANEL_GRAY = "#d9d9d9"
PANEL_DARK = "#111111"
BTN_BLUE   = "#1f618d"
RED_BAR    = "#cc1111"
GRAY_BAR   = "#bdbdbd"
WHITE      = "#ffffff"

SAVE_FILE = os.path.join(os.path.expanduser("~"), ".memeclicker_final_save.json")

# ======================================================================
# DONNÉES : MEMES DE LA BOUTIQUE
# ======================================================================
UPGRADES_DATA = [
    {"id": 1, "name": "Black Business man",           "emoji": "📈", "type": "click",
     "base_cost": 15,    "power": 1,    "owned": 0},
    {"id": 2, "name": "Gumball",   "emoji": "🐈‍⬛", "type": "sec",
     "base_cost": 120,   "power": 2,    "owned": 0},
    {"id": 3, "name": "Plankton",              "emoji": "🐱", "type": "click",
     "base_cost": 400,   "power": 4,    "owned": 0},
    {"id": 4, "name": "Polite Cat",           "emoji": "😺", "type": "sec",
     "base_cost": 900,   "power": 8,   "owned": 0},
    {"id": 5, "name": "Shrek",                "emoji": "🧅", "type": "click",
     "base_cost": 2500,  "power": 16,   "owned": 0},
    {"id": 6, "name": "Gigachad Cat",         "emoji": "🗿", "type": "sec",
     "base_cost": 6000,  "power": 32,   "owned": 0},
    {"id": 7, "name": "Fung Pu Kanda",        "emoji": "🐼", "type": "click",
     "base_cost": 15000, "power": 64,   "owned": 0},
    {"id": 8, "name": "Bob",                  "emoji": "🧽", "type": "sec",
     "base_cost": 40000, "power": 128,  "owned": 0},
    {"id": 9, "name": "Supreme67",            "emoji": "⚡", "type": "sec",
     "base_cost": 120000,"power": 256,  "owned": 0},
    {"id": 0, "name": "Elon Musk",            "emoji": "🚀", "type": "sec",
     "base_cost": 140000,    "power": 512,  "owned": 0},
]

MILESTONE_THRESHOLDS = [0] 
MILESTONE_EMOJIS   = ["click!"]

TIMER_SECONDS = 60


# ======================================================================
# UTILITAIRE : formatage des grands nombres
# ======================================================================
def fmt(n: float) -> str:
    n = float(n)
    if n < 1000:
        return f"{n:,.0f}".replace(",", " ")
    for unit, div in [("K", 1e3), ("M", 1e6), ("B", 1e9), ("T", 1e12)]:
        if n < div * 1000:
            return f"{n / div:.2f}{unit}"
    return f"{n:.2e}"


# ======================================================================
# CLASSE PRINCIPALE
# ======================================================================
class MemeClicker(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("MemeClicker FINAL v2.0")
        self.geometry("1150x700")
        self.configure(bg=BG_TEAL)
        self.minsize(960, 620)

        # --- état du jeu ---
        self.money        = 0.0    
        self.total_earned = 0.0    
        self.per_click    = 1.0    
        self.per_sec      = 0.0    
        self.upgrades     = [dict(u) for u in UPGRADES_DATA]

        # --- système d'étapes (Difficulté augmentée) ---
        self.etape         = 1
        self.objectif      = 150.0    # Augmenté (anciennement 80.0)
        self.temps_restant = TIMER_SECONDS
        self.jeu_actif     = True
        self.en_pause      = False

        self._overlay = None     
        self._taille_rond = 260

        self._load_game()
        self._build_fonts()
        self._build_style()
        self._load_images()   
        self._build_layout()
        self._refresh_all()

        # Musique de fond en boucle continue
        audio.start_music()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._tick_ms = 100
        self._elapsed_ms = 0   
        self.after(self._tick_ms, self._game_loop)

    def _build_fonts(self):
        self.f_title  = tkfont.Font(family="Arial", size=18, weight="bold")
        self.f_h2     = tkfont.Font(family="Arial", size=12, weight="bold")
        self.f_normal = tkfont.Font(family="Arial", size=11)
        self.f_small  = tkfont.Font(family="Arial", size=9)
        self.f_btn    = tkfont.Font(family="Arial", size=10, weight="bold")
        self.f_overlay_btn = tkfont.Font(family="Arial", size=16, weight="bold")
        self.f_emoji  = tkfont.Font(family="Arial", size=72)

    def _build_style(self):
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure(
            "Red.Horizontal.TProgressbar",
            thickness=28,
            troughcolor=GRAY_BAR,
            background=RED_BAR,
        )

    def _load_images(self):
        self._meme_images = {}
        for up in self.upgrades:
            path = os.path.join(IMAGES_DIR, f"meme_{up['id']}.png")
            try:
                img = Image.open(path).convert("RGBA")
                img = img.resize(IMAGE_SIZE, Image.LANCZOS)
                self._meme_images[up["id"]] = ImageTk.PhotoImage(img)
            except Exception:
                self._meme_images[up["id"]] = None   

        self._centre_pil = {}   
        for up in self.upgrades:
            path = os.path.join(IMAGES_DIR, f"meme_{up['id']}.png")
            try:
                self._centre_pil[up["id"]] = Image.open(path).convert("RGBA")
            except Exception:
                self._centre_pil[up["id"]] = None
        self._centre_photo = None   

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=300)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_left_sidebar()
        self._build_center()
        self._build_right_sidebar()

        tk.Label(self, text="MemeClicker FINAL v2.0 — Python/Tkinter",
                 bg=BG_TEAL, fg=WHITE, font=self.f_small
                 ).grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=4)

    def _build_left_sidebar(self):
        outer = tk.Frame(self, bg=BG_TEAL)
        outer.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=30)

        frame = tk.Frame(outer, bg=PANEL_GRAY, bd=4, relief="solid")
        frame.pack(fill="both", expand=True)

        def make_btn(label, command, disabled=False):
            bg = "#a0a0a0" if disabled else BTN_BLUE
            st = "disabled" if disabled else "normal"
            b = tk.Button(frame, text=label, font=self.f_btn,
                          bg=bg, fg=WHITE,
                          relief="flat", cursor="hand2",
                          state=st, command=command)
            b.pack(pady=6, padx=8, fill="both", expand=True)
            if not disabled:
                b.bind("<Button-1>", audio.play_random_sfx, add="+")
            return b

        self.btn_pause = make_btn("⏸  Pause",      self._toggle_pause)
        make_btn("⚙️  Paramètres", self._launch_parametres)
        make_btn("❓  Aide",        self._open_help)
        self.btn_achievements = make_btn("🏆  Succès\n(Comming Soon)", lambda: None, disabled=True)

    def _build_center(self):
        center = tk.Frame(self, bg=BG_TEAL)
        center.grid(row=0, column=1, sticky="nsew", pady=20)
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(2, weight=1)

        box = tk.Frame(center, bg=PANEL_GRAY, bd=3, relief="solid")
        box.grid(row=0, column=0, pady=(0, 6), ipadx=40, ipady=8)
        tk.Label(box, text="Argent possédé", font=self.f_title, bg=PANEL_GRAY).pack()
        self.lbl_money = tk.Label(box, text="0 $",
                                  font=("Arial", 14, "bold"), bg=PANEL_GRAY, fg="#117a65")
        self.lbl_money.pack()

        stats = tk.Frame(center, bg=BG_TEAL)
        stats.grid(row=1, column=0, pady=4)
        self.lbl_persec   = tk.Label(stats, text="Argent gagné/sec : 0 $",
                                     font=self.f_normal, bg=BG_TEAL, fg=WHITE)
        self.lbl_persec.pack()
        self.lbl_perclick = tk.Label(stats, text="Argent gagné/click : 1 $",
                                     font=self.f_normal, bg=BG_TEAL, fg=WHITE)
        self.lbl_perclick.pack()

        self._canvas_container = tk.Frame(center, bg=BG_TEAL)
        self._canvas_container.grid(row=2, column=0, sticky="nsew", pady=10, padx=20)
        self._canvas_container.grid_columnconfigure(0, weight=1)
        self._canvas_container.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self._canvas_container, bg=BG_TEAL, highlightthickness=0,
                                cursor="hand2")
        self.canvas.grid(row=0, column=0)

        self._circle_id = self.canvas.create_oval(0, 0, 0, 0,
                                                   fill=WHITE, outline=PANEL_DARK, width=4)
        self._centre_img_id = self.canvas.create_image(0, 0, anchor="center")
        self._emoji_id      = self.canvas.create_text(0, 0, text="click!", font=("Arial", 72, "bold"), fill=BTN_BLUE)

        for item in (self._circle_id, self._centre_img_id, self._emoji_id):
            self.canvas.tag_bind(item, "<ButtonPress-1>",   self._on_press)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self._on_release)

        self._canvas_container.bind("<Configure>", self._resize_circle)

        self.lbl_popup = tk.Label(center, text="", font=("Arial", 12, "bold"),
                                  bg=BG_TEAL, fg="#9be37c")
        self.lbl_popup.grid(row=3, column=0)

        prog_frame = tk.Frame(center, bg=BG_TEAL)
        prog_frame.grid(row=4, column=0, sticky="ew", padx=30, pady=(8, 0))
        prog_frame.grid_columnconfigure(0, weight=1)

        self.lbl_objectif = tk.Label(prog_frame,
                                     text=f"Étape 1 — Objectif : 150 $",
                                     font=self.f_h2, bg=BG_TEAL, fg=WHITE)
        self.lbl_objectif.pack(anchor="w", pady=2)

        self.progress_bar = ttk.Progressbar(prog_frame, orient="horizontal",
                                            mode="determinate",
                                            style="Red.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", ipady=4)

    def _build_right_sidebar(self):
        outer = tk.Frame(self, bg=BG_TEAL)
        outer.grid(row=0, column=2, sticky="nsew", padx=(8, 15), pady=30)

        frame = tk.Frame(outer, bg=PANEL_GRAY, bd=4, relief="solid")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Boutique de memes", font=self.f_title,
                 bg=PANEL_GRAY, pady=10).pack(fill="x")

        timer_box = tk.Frame(frame, bg=WHITE, bd=3, relief="solid")
        timer_box.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(timer_box, text="Temps restant", font=self.f_h2, bg=WHITE).pack(pady=4)
        self.lbl_timer = tk.Label(timer_box, text=f"{TIMER_SECONDS} s",
                                  font=("Arial", 14, "bold"), bg=WHITE, fg=RED_BAR)
        self.lbl_timer.pack(pady=4)

        list_container = tk.Frame(frame, bg=PANEL_GRAY)
        list_container.pack(fill="both", expand=True, padx=8, pady=4)

        scroll_canvas = tk.Canvas(list_container, bg=PANEL_GRAY,
                                  highlightthickness=0, width=260)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                  command=scroll_canvas.yview)
        self._upgrade_list_frame = tk.Frame(scroll_canvas, bg=PANEL_GRAY)

        self._upgrade_list_frame.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(
                scrollregion=scroll_canvas.bbox("all")))
        _win = scroll_canvas.create_window((0, 0), window=self._upgrade_list_frame,
                                           anchor="nw")

        def _on_scroll_resize(event):
            scroll_canvas.itemconfig(_win, width=event.width)
        scroll_canvas.bind("<Configure>", _on_scroll_resize)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scroll_canvas.bind_all(
            "<MouseWheel>",
            lambda e: scroll_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._upgrade_widgets = []
        for up in self.upgrades:
            row = tk.Frame(self._upgrade_list_frame, bg=PANEL_GRAY,
                           highlightbackground=PANEL_DARK, highlightthickness=2)
            row.pack(fill="x", pady=4, padx=2)

            photo = self._meme_images.get(up["id"])
            if photo is not None:
                img_lbl = tk.Label(row, image=photo, bg=PANEL_GRAY,
                                   width=IMAGE_SIZE[0], height=IMAGE_SIZE[1])
                img_lbl.image = photo   
            else:
                img_lbl = tk.Label(row, text=up["emoji"], font=("Arial", 26),
                                   bg=PANEL_GRAY, width=3)
            img_lbl.grid(row=0, column=0, rowspan=2, padx=6, pady=5)

            tk.Label(row, text=up["name"], font=self.f_h2, bg=PANEL_GRAY,
                     anchor="w").grid(row=0, column=1, sticky="w", padx=4)

            info_lbl = tk.Label(row, text="", font=self.f_small, bg=PANEL_GRAY,
                                anchor="w")
            info_lbl.grid(row=1, column=1, sticky="w", padx=4)

            btn = tk.Button(row, text="Acheter\n—", font=self.f_btn,
                            bg=BTN_BLUE, fg=WHITE, relief="flat", cursor="hand2",
                            command=lambda uid=up["id"]: self._buy_upgrade(uid))
            btn.grid(row=0, column=2, rowspan=2, padx=8, pady=6, sticky="ns")
            btn.bind("<Button-1>", audio.play_random_sfx, add="+")

            row.grid_columnconfigure(1, weight=1)
            self._upgrade_widgets.append({
                "id": up["id"], "row": row,
                "info": info_lbl, "btn": btn,
            })

    # ------------------------------------------------------------------
    # LOGIQUE DE JEU
    # ------------------------------------------------------------------
    def _cost_of(self, upgrade: dict) -> float:
        return upgrade["base_cost"] * (1.15 ** upgrade["owned"])

    def _on_press(self, event=None):
        if not self.jeu_actif or self.en_pause:
            return
        audio.play_random_sfx()
        c = self._taille_rond / 2
        r = c * 0.88
        self.canvas.coords(self._circle_id, c - r, c - r, c + r, c + r)
        self.canvas.itemconfig(self._circle_id, fill="#e0e0e0")
        self._set_centre_image_scale(0.83)

    def _on_release(self, event=None):
        if not self.jeu_actif or self.en_pause:
            return
        c = self._taille_rond / 2
        r = c * 0.95
        self.canvas.coords(self._circle_id, c - r, c - r, c + r, c + r)
        self.canvas.itemconfig(self._circle_id, fill=WHITE)
        self._set_centre_image_scale(0.95)

        gain = self.per_click
        self.money        += gain
        self.total_earned += gain
        self._flash_popup(gain)
        self._pulse_circle()
        self._refresh_money()
        self._refresh_milestone()
        self._check_objectif()

    def _buy_upgrade(self, upgrade_id: int):
        if not self.jeu_actif or self.en_pause:
            return
        up   = next(u for u in self.upgrades if u["id"] == upgrade_id)
        cost = self._cost_of(up)
        if self.money >= cost:
            self.money -= cost
            up["owned"] += 1
            if up["type"] == "sec":
                self.per_sec += up["power"]
            else:
                self.per_click += up["power"]
            self._refresh_all()
        else:
            w = next(w for w in self._upgrade_widgets if w["id"] == upgrade_id)
            w["btn"].config(bg="#ff7675")
            self.after(200, lambda: w["btn"].config(bg=BTN_BLUE))

    def _game_loop(self):
        if self.jeu_actif and not self.en_pause:
            self._elapsed_ms += self._tick_ms

            gain = self.per_sec * (self._tick_ms / 1000.0)
            if gain > 0:
                self.money        += gain
                self.total_earned += gain

            if self._elapsed_ms >= 1000:
                self._elapsed_ms -= 1000
                self._tick_second()

            self._refresh_money()
            self._refresh_milestone()
            self._refresh_buy_buttons()
            self._refresh_objectif_bar()
            self._check_objectif()

        self.after(self._tick_ms, self._game_loop)

    def _tick_second(self):
        if self.temps_restant > 0:
            self.temps_restant -= 1
            self.lbl_timer.config(text=f"{self.temps_restant} s")
            if self.temps_restant <= 10:
                self.lbl_timer.config(fg="#ff2222")
            else:
                self.lbl_timer.config(fg=RED_BAR)
        else:
            self._game_over()

    def _check_objectif(self):
        """Vérifie si l'objectif est atteint et passe DIRECTEMENT à la suite."""
        if self.money >= self.objectif and self.jeu_actif:
            self.etape        += 1
            self.objectif      = int(self.objectif * 1.5)  # Multiplicateur augmenté de 1.2 à 1.5
            self.temps_restant = TIMER_SECONDS            # Reset du timer instantané
            self._refresh_all()                           # Transition invisible et fluide

    # ------------------------------------------------------------------
    # RAFRAÎCHISSEMENT DE L'AFFICHAGE
    # ------------------------------------------------------------------
    def _refresh_all(self):
        self._refresh_money()
        self._refresh_milestone()
        self._refresh_buy_buttons()
        self._refresh_objectif_bar()

    def _refresh_money(self):
        self.lbl_money.config(text=f"{fmt(self.money)} $")
        self.lbl_persec.config(text=f"Argent gagné/sec : {fmt(self.per_sec)} $")
        self.lbl_perclick.config(text=f"Argent gagné/click : {fmt(self.per_click)} $")

    def _refresh_buy_buttons(self):
        for w in self._upgrade_widgets:
            up   = next(u for u in self.upgrades if u["id"] == w["id"])
            cost = self._cost_of(up)
            can  = self.money >= cost
            tag  = "$/sec" if up["type"] == "sec" else "$/click"
            w["btn"].config(
                text=f"Acheter\n{fmt(cost)} $",
                bg=BTN_BLUE if can else "#8a8a8a"
            )
            w["info"].config(text=f"+{fmt(up['power'])} {tag}   (×{up['owned']})")

    def _refresh_milestone(self):
        achetes = [u for u in self.upgrades if u["owned"] > 0]
        if achetes:
            meilleur = max(achetes, key=lambda u: u["base_cost"])
            pil_img  = self._centre_pil.get(meilleur["id"])
            if pil_img is not None:
                self.canvas.itemconfig(self._circle_id, state="hidden")
                self.canvas.itemconfig(self._emoji_id, state="hidden")
                self._update_centre_image(pil_img)
                return
        self.canvas.itemconfig(self._circle_id, state="normal")
        self.canvas.itemconfig(self._centre_img_id, state="hidden")
        self.canvas.itemconfig(self._emoji_id, state="normal")
        idx = 0
        for i, threshold in enumerate(MILESTONE_THRESHOLDS):
            if self.total_earned >= threshold:
                idx = i
        emoji = MILESTONE_EMOJIS[idx] if idx < len(MILESTONE_EMOJIS) else "🌌"
        self.canvas.itemconfig(self._emoji_id, text=emoji)

    def _update_centre_image(self, pil_img):
        taille = int(self._taille_rond * 0.95)
        if taille < 10:
            return

        img_resized = pil_img.resize((taille, taille), Image.LANCZOS).convert("RGBA")

        from PIL import ImageDraw
        masque = Image.new("L", (taille, taille), 0)
        draw   = ImageDraw.Draw(masque)
        draw.ellipse((0, 0, taille - 1, taille - 1), fill=255)

        img_cercle = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
        img_cercle.paste(img_resized, mask=masque)

        self._centre_photo = ImageTk.PhotoImage(img_cercle)
        c = self._taille_rond / 2
        self.canvas.itemconfig(self._centre_img_id, image=self._centre_photo, state="normal")
        self.canvas.coords(self._centre_img_id, c, c)

    def _set_centre_image_scale(self, scale: float):
        achetes = [u for u in self.upgrades if u["owned"] > 0]
        if not achetes:
            return
        meilleur = max(achetes, key=lambda u: u["base_cost"])
        pil_img  = self._centre_pil.get(meilleur["id"])
        if pil_img is None:
            return

        from PIL import ImageDraw
        taille = int(self._taille_rond * scale)
        if taille < 10:
            return

        img_resized = pil_img.resize((taille, taille), Image.LANCZOS).convert("RGBA")
        masque = Image.new("L", (taille, taille), 0)
        ImageDraw.Draw(masque).ellipse((0, 0, taille - 1, taille - 1), fill=255)
        img_cercle = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
        img_cercle.paste(img_resized, mask=masque)

        self._centre_photo = ImageTk.PhotoImage(img_cercle)
        c = self._taille_rond / 2
        self.canvas.itemconfig(self._centre_img_id, image=self._centre_photo, state="normal")
        self.canvas.coords(self._centre_img_id, c, c)

    def _refresh_objectif_bar(self):
        self.lbl_objectif.config(
            text=f"Étape {self.etape} — Objectif : {fmt(self.objectif)} $"
        )
        pct = min(100.0, (self.money / self.objectif) * 100) if self.objectif else 100
        self.progress_bar["value"] = pct

    # ------------------------------------------------------------------
    # EFFETS VISUELS
    # ------------------------------------------------------------------
    def _flash_popup(self, gain: float):
        self.lbl_popup.config(text=f"+{fmt(gain)} $")
        self.after(400, lambda: self.lbl_popup.config(text=""))

    def _pulse_circle(self):
        self.canvas.itemconfig(self._circle_id, outline="#9be37c")
        self.after(120, lambda: self.canvas.itemconfig(self._circle_id, outline=PANEL_DARK))

    def _resize_circle(self, event):
        taille = min(event.width, event.height) * 0.82
        taille = max(taille, 180)
        self._taille_rond = taille

        self.canvas.config(width=taille, height=taille)
        c = taille / 2
        r = c * 0.95

        self.canvas.coords(self._circle_id, c - r, c - r, c + r, c + r)
        self.canvas.coords(self._emoji_id,  c, c)
        self.canvas.coords(self._centre_img_id, c, c)

        new_size = max(11, int(taille / 4))
        self.canvas.itemconfig(self._emoji_id, font=("Arial", new_size))

        self._refresh_milestone()

    # ------------------------------------------------------------------
    # OVERLAYS FLOTTANTS
    # ------------------------------------------------------------------
    def _close_overlay(self):
        if self._overlay is not None:
            self._overlay.destroy()
            self._overlay = None
        self.en_pause = False

    def _open_overlay(self, w=360, h=300) -> tk.Frame:
        self._close_overlay()
        self.en_pause = True

        f = tk.Frame(self, bg=PANEL_GRAY, bd=0, relief="flat",
                     highlightthickness=0)
        f.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._overlay = f
        return f

    def _toggle_pause(self):
        if not self.jeu_actif:
            return
        if self.en_pause and self._overlay is not None:
            self._close_overlay()
            self.btn_pause.config(text="⏸  Pause")
            return
        f = self._open_overlay(350, 380)
        tk.Label(f, text="JEU EN PAUSE", font=("Arial", 36, "bold"),
                 bg=PANEL_GRAY, fg="black").pack(pady=40)

        def continuer():
            self._close_overlay()
            self.btn_pause.config(text="⏸  Pause")

        def recommencer():
            self._reset_game()

        def quitter():
            self._on_close()

        tk.Button(f, text="▶️Continuer",    bg=BTN_BLUE, fg=WHITE, font=self.f_overlay_btn,
                  width=20, height=2, command=continuer).pack(pady=12)
        tk.Button(f, text="💾 Sauvegarder", bg="#006eff", fg=WHITE, font=self.f_overlay_btn,
                  width=20, height=2, command=self._save_game).pack(pady=12)
        tk.Button(f, text="♻️Recommencer", bg="#258A00", fg=WHITE, font=self.f_overlay_btn,
                  width=20, height=2, command=recommencer).pack(pady=12)
        tk.Button(f, text="⬅️Quitter",      bg="#ff1500", fg=WHITE, font=self.f_overlay_btn,
                  width=20, height=2, command=quitter).pack(pady=12)
        self.btn_pause.config(text="▶  Reprendre")
        self._brancher_sfx_recursif(f)

    def _launch_parametres(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        chemin = os.path.join(base_dir, "parametres.py")
        try:
            subprocess.Popen([sys.executable, chemin])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible d'ouvrir parametres.py\n{e}")

    def _open_help(self):
        if not self.jeu_actif or self.en_pause:
            return
        f = self._open_overlay(390, 320)
        tk.Label(f, text="COMMENT JOUER ?", font=("Arial", 30, "bold"),
                 bg=PANEL_GRAY).pack(pady=30)
        texte = (
            "• Clique sur le rond au centre pour gagner de l'argent.\n\n"
            "• Achète des mèmes dans la boutique à droite :\n"
            "  - type $/sec  → revenu passif automatique\n"
            "  - type $/click → bonus par clic\n\n"
            "• Atteins l'objectif de l'étape avant la fin du\n"
            "  temps imparti (60 s). Sinon c'est Game Over !\n\n"
            "• L'emoji du rond évolue avec tes gains totaux."
        )
        tk.Label(f, text=texte, bg=PANEL_GRAY, font=("Arial", 16),
                 justify="left").pack(padx=40, pady=10)
        tk.Button(f, text="J'ai compris !", bg=BTN_BLUE, fg=WHITE,
                  font=self.f_overlay_btn, width=20, height=2,
                  command=self._close_overlay).pack(pady=30)
        self._brancher_sfx_recursif(f)

    def _game_over(self):
        self.jeu_actif = False
        self.en_pause  = True

        self.canvas.itemconfig(self._circle_id, fill="#b2bec3")
        self.canvas.itemconfig(self._emoji_id,  text="💀")
        self.lbl_timer.config(text="0 s", fg="#ff2222")

        if self._overlay is not None:
            self._overlay.destroy()
            self._overlay = None

        f = tk.Frame(self, bg=PANEL_GRAY, bd=0, relief="flat",
                     highlightthickness=0)
        f.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._overlay = f

        tk.Label(f, text="GAME OVER", font=("Arial", 40, "bold"),
                 bg=PANEL_GRAY, fg=RED_BAR).pack(pady=40)
        tk.Label(f, text=f"Étape atteinte : {self.etape}",
                 font=("Arial", 20, "bold"), bg=PANEL_GRAY).pack(pady=10)

        tk.Button(f, text="Recommencer", bg=BTN_BLUE, fg=WHITE,
                  font=self.f_overlay_btn, width=20, height=2,
                  command=self._reset_game).pack(pady=16)
        tk.Button(f, text="Quitter le jeu", bg="#444444", fg=WHITE,
                  font=self.f_overlay_btn, width=20, height=2,
                  command=self.destroy).pack(pady=10)
        self._brancher_sfx_recursif(f)

    # ------------------------------------------------------------------
    # SAUVEGARDE / CHARGEMENT / RESET
    # ------------------------------------------------------------------
    def _save_game(self):
        data = {
            "money":        self.money,
            "total_earned": self.total_earned,
            "per_click":    self.per_click,
            "per_sec":      self.per_sec,
            "etape":        self.etape,
            "objectif":     self.objectif,
            "temps_restant":self.temps_restant,
            "owned":        {str(u["id"]): u["owned"] for u in self.upgrades},
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        except OSError:
            pass

    def _load_game(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.money         = data.get("money",         0.0)
            self.total_earned  = data.get("total_earned",  0.0)
            self.per_click     = data.get("per_click",     1.0)
            self.per_sec       = data.get("per_sec",       0.0)
            self.etape         = data.get("etape",         1)
            self.objectif      = data.get("objectif",      150.0) # Modifié ici pour les sauvegardes
            self.temps_restant = data.get("temps_restant", TIMER_SECONDS)
            owned = data.get("owned", {})
            for u in self.upgrades:
                u["owned"] = owned.get(str(u["id"]), owned.get(u["id"], 0))
        except (OSError, json.JSONDecodeError):
            pass

    def _reset_game(self):
        self.money         = 0.0
        self.total_earned  = 0.0
        self.per_click     = 1.0
        self.per_sec       = 0.0
        self.etape         = 1
        self.objectif      = 150.0    # Mis à jour à 150
        self.temps_restant = TIMER_SECONDS
        self.jeu_actif     = True
        self._elapsed_ms   = 0

        for u in self.upgrades:
            u["owned"] = 0

        try:
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
        except OSError:
            pass

        if self._overlay is not None:
            self._overlay.destroy()
            self._overlay = None
        self.en_pause = False
        self.btn_pause.config(text="⏸  Pause")

        self.canvas.itemconfig(self._circle_id, fill=WHITE, outline=PANEL_DARK)
        self.lbl_timer.config(text=f"{TIMER_SECONDS} s", fg=RED_BAR)

        self._refresh_all()

    def _on_close(self):
        self._save_game()
        self.destroy()

    def _brancher_sfx_recursif(self, widget):
        """Fait jouer un sfx aléatoire à chaque clic sur tous les boutons d'un widget (et ses enfants)."""
        if isinstance(widget, tk.Button):
            widget.bind("<Button-1>", audio.play_random_sfx, add="+")
        for enfant in widget.winfo_children():
            self._brancher_sfx_recursif(enfant)


if __name__ == "__main__":
    app = MemeClicker()
    app.mainloop()