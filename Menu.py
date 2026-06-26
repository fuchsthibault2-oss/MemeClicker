import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from audio_manager import audio

# Dossier contenant tous les fichiers .py du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _lancer(nom_fichier):
    """Lance un fichier Python en arrière-plan (non bloquant)."""
    chemin = os.path.join(BASE_DIR, nom_fichier)
    try:
        subprocess.Popen([sys.executable, chemin])
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'ouvrir {nom_fichier}\n{e}")


# --- FONCTIONS POUR OUVRIR LES AUTRES FICHIERS ---
def ouvrir_jouer():
    _lancer("meme_clicker_final_9_.py")


def ouvrir_parametre():
    _lancer("parametres.py")


def ouvrir_credit():
    _lancer("credit.py")


# --- FENÊTRE PRINCIPALE ---
fenetre = tk.Tk()
fenetre.title("Meme Clicker - Menu")
fenetre.state("zoomed")  # Plein écran (fenêtré maximisé) sur Windows
fenetre.resizable(False, False)  # Empêche de redimensionner pour garder le fond propre


# --- INTRO EN TEXTE DÉFILANT (STYLE STAR WARS) ---
intro_canvas = tk.Canvas(fenetre, bg="black", highlightthickness=0)
intro_canvas.pack(fill="both", expand=True)

# Texte corrigé et formaté avec des sauts de ligne pour le défilement
texte_intro = (
    "En 2077, les gouvernements mondiaux ont commencé\n"
    "à contrôler les réseaux sociaux de manière radicale.\n\n"
    "Mais des individus résistent encore et toujours à l'envahisseur.\n\n"
    "VOUS en faites partie.\n\n"
    "VOUS avez le pouvoir de sauver Internet\n"
    "en ramenant les MEMES pour lui redonner sa couleur d'autrefois.\n\n"
    "Changez le monde.\n\n"
    "def : Mème(nom masculin) : Image, vidéo ou texte humoristique diffusé \n"
    "largement sur Internet et faisant l'objet de nombreuses variations."
)

# Création du texte de l'intro (Couleur jaune style Star Wars, modifiable en "white")
intro_texte_id = intro_canvas.create_text(
    0, 0,
    text=texte_intro,
    font=("Liberation Mono", 20, "bold"),
    fill="#FFE81F",  # Jaune Star Wars mythique
    justify="center",
    anchor="center"
)

# Indicateur pour passer l'intro
skip_texte_id = intro_canvas.create_text(
    0, 0,
    text="[ ESPACE ou CLIC pour passer ]",
    font=("Arial", 12, "italic"),
    fill="gray",
    anchor="se"
)

y_pos = 1000  # Position de départ initiale (sera ajustée dynamiquement)
intro_active = True


def demarrer_menu_principal():
    """Détruit l'intro et affiche le menu principal avec la musique."""
    global intro_active
    if not intro_active:
        return
    intro_active = False
    
    # Nettoyage de l'intro
    intro_canvas.destroy()
    fenetre.unbind("<space>")
    
    # Affichage du vrai menu de jeu
    canvas.pack(fill="both", expand=True)
    audio.start_music()  # La musique se lance au moment où le menu apparaît !


def animer_intro():
    """Boucle d'animation pour faire monter le texte."""
    global y_pos
    if not intro_active:
        return
    
    largeur = intro_canvas.winfo_width()
    hauteur = intro_canvas.winfo_height()
    
    # Met à jour les coordonnées (centré horizontalement, monte verticalement)
    intro_canvas.coords(intro_texte_id, largeur / 2, y_pos)
    intro_canvas.coords(skip_texte_id, largeur - 30, hauteur - 30)
    
    y_pos -= 0.6  # Vitesse du défilement (baisse cette valeur pour ralentir)
    
    # Si le texte a fini de défiler au-dessus de l'écran (hauteur estimée à -400)
    if y_pos < -400:
        demarrer_menu_principal()
    else:
        fenetre.after(15, animer_intro)  # ~60 FPS


def initialiser_intro(event):
    """Initialise la position de départ du texte sous l'écran réel."""
    global y_pos
    y_pos = event.height + 100
    intro_canvas.unbind("<Configure>")  # Évite de réinitialiser à chaque micro-changement
    animer_intro()


# Assignation des événements de l'intro
intro_canvas.bind("<Configure>", initialiser_intro)
intro_canvas.bind("<Button-1>", lambda e: demarrer_menu_principal())
fenetre.bind("<space>", lambda e: demarrer_menu_principal())


# --- FOND ET ÉLÉMENTS DU MENU PRINCIPAL (Masqués au début) ---
canvas = tk.Canvas(fenetre, highlightthickness=0)

# Chargement de l'image originale avec Pillow
try:
    image_originale = Image.open("menubackground.png")
    image_fond_tk = None

    def redimensionner_fond(event):
        global image_fond_tk
        img_redim = image_originale.resize(
            (event.width, event.height), Image.LANCZOS
        )
        image_fond_tk = ImageTk.PhotoImage(img_redim)
        canvas.delete("fond")
        canvas.create_image(0, 0, image=image_fond_tk, anchor="nw", tags="fond")
        canvas.tag_lower("fond")

    canvas.bind("<Configure>", redimensionner_fond)

except Exception:
    canvas.config(bg="#1e1e2e")
    canvas.create_text(
        400,
        300,
        text="(Image 'menubackground.png' manquante)",
        fill="white",
        font=("Arial", 12),
    )

# --- TITRE ---
titre_id = canvas.create_text(
    0, 150,
    text="Meme Clicker",
    font=("Liberation Mono", 70, "bold"),
    fill="light gray",
    justify="center",
)
soustitre_id = canvas.create_text(
    0, 250,
    text="Objectif : Stonks",
    font=("Liberation Mono", 40, "bold"),
    fill="light gray",
    justify="center",
)


# --- BOUTONS ---
style_bouton = {
    "font": ("Arial", 16, "bold"),
    "bg": "#3D3D3B",
    "fg": "black",
    "activebackground": "#353532",
    "width": 15,
    "height": 2,
    "bd": 3,
}

bouton_jouer = tk.Button(fenetre, text="Jouer", command=ouvrir_jouer, **style_bouton)
bouton_parametre = tk.Button(fenetre, text="Paramètres", command=ouvrir_parametre, **style_bouton)
bouton_credit = tk.Button(fenetre, text="Crédit", command=ouvrir_credit, **style_bouton)

bouton_jouer_id = canvas.create_window(0, 380, window=bouton_jouer)
bouton_parametre_id = canvas.create_window(0, 480, window=bouton_parametre)
bouton_credit_id = canvas.create_window(0, 580, window=bouton_credit)


def recentrer_elements(event):
    """Recentre le titre et les boutons horizontalement."""
    centre_x = event.width / 2
    canvas.coords(titre_id, centre_x, 150)
    canvas.coords(soustitre_id, centre_x, 250)
    canvas.coords(bouton_jouer_id, centre_x, 380)
    canvas.coords(bouton_parametre_id, centre_x, 480)
    canvas.coords(bouton_credit_id, centre_x, 580)


canvas.bind("<Configure>", recentrer_elements, add="+")

# --- SFX ALÉATOIRE SUR CHAQUE BOUTON ---
for _bouton in (bouton_jouer, bouton_parametre, bouton_credit):
    _bouton.bind("<Button-1>", audio.play_random_sfx, add="+")

# Lancement de la boucle principale
fenetre.mainloop()