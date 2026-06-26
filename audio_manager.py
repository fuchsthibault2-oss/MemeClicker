"""
audio_manager.py — Gestion centralisée du son pour MemeClicker
================================================================
- Joue la musique de fond en boucle continue (avec verrou inter-processus).
- Joue un SFX aléatoire (parmi sfx1/sfx2/sfx3) à chaque clic de bouton.
- Lit le volume (musique / sfx) depuis le fichier de paramètres
  partagé (~/.memeclicker_settings.json), pour rester synchronisé
  avec la fenêtre "Paramètres".
"""

import os
import json
import random
import socket  # Importation essentielle pour le verrou inter-processus

# Mets DEBUG = True temporairement pour voir dans la console pourquoi
# le son ne se charge pas (chemin invalide, pygame absent, etc.)
DEBUG = True


def _log(message):
    if DEBUG:
        print(f"[audio_manager] {message}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".memeclicker_settings.json")

DEFAULT_SETTINGS = {
    "music_volume": 50,
    "sfx_volume": 70,
}

SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

MUSIC_FILE = os.path.join(SOUNDS_DIR, "Musique_GameJam_Page_d_accueil1.wav")
SFX_FILES = [
    os.path.join(SOUNDS_DIR, "sfx1.mp3"),
    os.path.join(SOUNDS_DIR, "sfx2.mp3"),
    os.path.join(SOUNDS_DIR, "sfx3.mp3"),
]

try:
    import pygame
    _PYGAME_OK = True
except Exception as e:
    _PYGAME_OK = False
    _log(f"pygame indisponible à l'import : {e!r}")


def load_settings() -> dict:
    """Charge les paramètres (volume musique / sfx) depuis le fichier JSON partagé."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return {**DEFAULT_SETTINGS, **data}
        except (OSError, json.JSONDecodeError):
            pass
    return dict(DEFAULT_SETTINGS)


class AudioManager:
    """Gère la musique de fond et les effets sonores du jeu."""

    def __init__(self):
        self._ready = False
        self._sfx_sounds = []
        self._music_loaded = False
        self._music_socket = None  # Initialisation de la socket de verrouillage
        self._init_mixer()

    # ------------------------------------------------------------------
    def _init_mixer(self):
        _log(f"BASE_DIR = {BASE_DIR}")
        _log(f"SOUNDS_DIR = {SOUNDS_DIR}  (existe : {os.path.isdir(SOUNDS_DIR)})")
        _log(f"MUSIC_FILE = {MUSIC_FILE}  (existe : {os.path.exists(MUSIC_FILE)})")
        for p in SFX_FILES:
            _log(f"SFX_FILE = {p}  (existe : {os.path.exists(p)})")

        if not _PYGAME_OK:
            _log("ARRÊT : pygame n'a pas pu être importé. "
                 "Installe-le avec : pip install pygame-ce")
            return
        try:
            pygame.mixer.init()
            self._ready = True
            _log("pygame.mixer.init() réussi.")
        except Exception as e:
            self._ready = False
            _log(f"ARRÊT : pygame.mixer.init() a échoué : {e!r}")
            return

        # Charge les sfx une seule fois en mémoire
        for path in SFX_FILES:
            try:
                self._sfx_sounds.append(pygame.mixer.Sound(path))
                _log(f"SFX chargé : {path}")
            except Exception as e:
                _log(f"ÉCHEC chargement SFX {path} : {e!r}")

        # Charge la musique de fond (chargée à la demande via pygame.mixer.music)
        self._music_loaded = os.path.exists(MUSIC_FILE)
        if not self._music_loaded:
            _log(f"ATTENTION : fichier musique introuvable -> {MUSIC_FILE}")

        self.refresh_volumes()

    # ------------------------------------------------------------------
    def refresh_volumes(self):
        """Relit le fichier de paramètres et applique les volumes courants."""
        settings = load_settings()
        music_vol = max(0, min(100, settings.get("music_volume", 50))) / 100.0
        sfx_vol = max(0, min(100, settings.get("sfx_volume", 70))) / 100.0

        self._music_volume = music_vol
        self._sfx_volume = sfx_vol

        if not self._ready:
            return

        try:
            pygame.mixer.music.set_volume(music_vol)
        except Exception:
            pass

        for sound in self._sfx_sounds:
            try:
                sound.set_volume(sfx_vol)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def start_music(self):
        """Lance la musique de fond en boucle infinie (ne fait rien si déjà lancée ou jouée ailleurs)."""
        if not self._ready:
            _log("start_music ignoré : mixer non prêt (voir messages ci-dessus).")
            return
        if not self._music_loaded:
            _log("start_music ignoré : fichier musique non trouvé.")
            return
        try:
            if pygame.mixer.music.get_busy():
                _log("start_music ignoré : musique déjà en cours de lecture.")
                return  # déjà en train de jouer localement

            # --- VERROU INTER-PROCESSUS ---
            # On tente de lier une socket sur un port local unique pour bloquer les doublons
            try:
                self._music_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._music_socket.bind(('127.0.0.1', 45242))  # Port arbitraire dédié à MemeClicker
            except OSError:
                # Si le port est déjà pris, un autre processus (ex: Menu principal) joue déjà la musique
                _log("start_music ignoré : la musique est déjà gérée par une autre fenêtre.")
                self._music_socket = None
                return

            pygame.mixer.music.load(MUSIC_FILE)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(loops=-1)  # -1 = boucle infinie
            _log(f"Musique lancée (volume={self._music_volume}).")
        except Exception as e:
            _log(f"ÉCHEC start_music : {e!r}")
            if self._music_socket:
                try:
                    self._music_socket.close()
                except Exception:
                    pass
                self._music_socket = None

    def stop_music(self):
        if not self._ready:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        if self._music_socket:
            try:
                self._music_socket.close()
            except Exception:
                pass
            self._music_socket = None

    # ------------------------------------------------------------------
    def play_random_sfx(self, event=None):
        """Joue un SFX choisi au hasard parmi les 3 disponibles."""
        # En actualisant ici, le processus principal met à jour son volume musical en direct au moindre clic
        self.refresh_volumes()

        if not self._ready:
            _log("play_random_sfx ignoré : mixer non prêt.")
            return
        if not self._sfx_sounds:
            _log("play_random_sfx ignoré : aucun sfx chargé.")
            return
        try:
            son = random.choice(self._sfx_sounds)
            son.set_volume(self._sfx_volume)
            son.play()
        except Exception as e:
            _log(f"ÉCHEC play_random_sfx : {e!r}")


# Instance unique partagée par tout le projet
audio = AudioManager()