"""
interface/app.py
Interface graphique Tkinter – 4 onglets :
    1. 📝 Enregistrement   2. 🎥 Contrôle d'Accès   3. 📋 Journaux
    4. ⚙️  Administration

CORRECTIONS v2.1 :
  - Images capturées chiffrées (AES-256 Fernet) PUIS tatouées avant sauvegarde
  - Logs en temps réel (auto-refresh toutes les 2 s via root.after)
  - Alertes SMTP uniquement pour les imposteurs
  - Utilisateurs admin mis à jour en temps réel après chaque action

THREAD SAFETY : Tous les widgets Tkinter sont modifiés UNIQUEMENT depuis le
main thread.  Les threads de fond déposent leurs données dans des queue.Queue
et le main thread les lit via root.after().
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import os
import cv2
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime

from config                          import settings
from core.biometrie.capture          import GestionnaireCapture
from core.biometrie.reconnaissance   import GestionnaireReconnaissance
from core.database.gestionnaire      import GestionnaireDB
from core.securite.chiffrement       import GestionnaireChiffrement
from core.securite.tatouage          import GestionnaireTatouage
from core.notifications.email_alerts import GestionnaireNotifications


# ═══════════════════════════════════════════════════════════════════════════════
#  PALETTE & HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
C = {
    'bg'    : '#1a1a2e',
    'panel' : '#16213e',
    'card'  : '#0f3460',
    'accent': '#e94560',
    'green' : '#27ae60',
    'orange': '#e67e22',
    'text'  : '#ecf0f1',
    'muted' : '#95a5a6',
    'white' : '#ffffff',
}
FONT_TITLE  = ('Segoe UI', 18, 'bold')
FONT_HEADER = ('Segoe UI', 12, 'bold')
FONT_BODY   = ('Segoe UI', 10)
FONT_SMALL  = ('Segoe UI', 9)


def _label(parent, text, font=FONT_BODY, fg=None, **kw):
    return tk.Label(parent, text=text, font=font,
                    fg=fg or C['text'], bg=kw.pop('bg', C['panel']), **kw)

def _btn(parent, text, cmd, color=None, **kw):
    color = color or C['accent']
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg=C['white'], font=FONT_BODY,
                     relief='flat', cursor='hand2',
                     padx=12, pady=6, **kw)

def _entry(parent, textvariable=None, show=None, width=24):
    kw = dict(bg=C['card'], fg=C['text'], font=FONT_BODY,
              insertbackground=C['text'], relief='flat',
              highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['muted'], width=width)
    if show:
        kw['show'] = show
    if textvariable:
        kw['textvariable'] = textvariable
    return tk.Entry(parent, **kw)


def _frame_to_photoimage(bgr_frame, size=(480, 360)):
    """Convertit une frame BGR (numpy) en PhotoImage – doit être appelé dans le main thread."""
    rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(rgb).resize(size))


def _setup_styles():
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass

    style.configure('Nav.TButton',
                    background=C['panel'], foreground=C['text'],
                    font=FONT_BODY, padding=(16, 10), borderwidth=0)
    style.map('Nav.TButton',
              background=[('active', C['card']), ('pressed', C['accent'])],
              foreground=[('active', C['white']), ('pressed', C['white'])])

    style.configure('NavActive.TButton',
                    background=C['accent'], foreground=C['white'],
                    font=FONT_BODY, padding=(16, 10), borderwidth=0)
    style.map('NavActive.TButton',
              background=[('active', '#d32f3d'), ('pressed', '#b91c1c')])

    style.configure('Card.TFrame', background=C['panel'])
    style.configure('Secondary.TFrame', background=C['card'])


# ═══════════════════════════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
class ApplicationBiometrique:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🔐 Recon")
        self.root.geometry('1200x760')
        self.root.configure(bg=C['bg'])
        self.root.resizable(True, True)

        # ── Services ──────────────────────────────────────────────────────────
        self.db       = GestionnaireDB(settings.DB_PATH)
        self.capture  = GestionnaireCapture(
            settings.CAMERA_INDEX, settings.CLAHE_CLIP_LIMIT,
            settings.BRIGHTNESS_BOOST, settings.CONTRAST_BOOST)
        self.recog    = GestionnaireReconnaissance(
            settings.MODEL_DIR, settings.RECOGNITION_THRESHOLD)
        self.chiffre  = GestionnaireChiffrement(settings.ENCRYPTION_KEY_PATH)
        self.tatouage = GestionnaireTatouage()
        self.notif    = GestionnaireNotifications(
            settings.SMTP_HOST, settings.SMTP_PORT,
            settings.SMTP_EMAIL, settings.SMTP_PASSWORD,
            settings.ALERT_EMAIL, settings.SMTP_ENABLED)

        # ── État threads ───────────────────────────────────────────────────────
        self._surveillance_active = False
        self._enroll_active       = False

        # ── Queues thread-safe ─────────────────────────────────────────────────
        self._enroll_q      = queue.Queue(maxsize=4)   # (count, total, bgr_frame)
        self._enroll_done_q = queue.Queue()             # ('ok'|'error', ...)
        self._surv_q        = queue.Queue(maxsize=4)   # ('frame'|'error'|'stopped', data)
        self._result_q      = queue.Queue()             # (nom, resultat, score)

        # ── Dernier snapshot logs (pour détecter les nouveaux) ─────────────────
        self._last_log_count = 0

        self._build_ui()

        # ── Auto-refresh logs toutes les 2 secondes ───────────────────────────
        self._auto_refresh_logs()

    # ═══════════════════════════════════════════════════════════════════════════
    #  UI PRINCIPALE
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        _setup_styles()

        header = tk.Frame(self.root, bg=C['panel'], height=70)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg=C['panel'])
        title_frame.pack(side='left', fill='y', padx=20)
        _label(title_frame, "🔐 Recon", FONT_TITLE, fg=C['white'], bg=C['panel']).pack(anchor='w')
        _label(title_frame, "Plateforme de reconnaissance biométrique", FONT_SMALL,
               fg=C['muted'], bg=C['panel']).pack(anchor='w', pady=(4, 0))

        nav_frame = tk.Frame(header, bg=C['panel'])
        nav_frame.pack(side='right', padx=20)

        self._nav_buttons = []
        nav_items = [
            ("📝 Enregistrement", self._build_tab_enregistrement),
            ("🎥 Accès", self._build_tab_acces),
            ("📋 Journaux", self._build_tab_logs),
            ("⚙️ Administration", self._build_tab_admin),
        ]
        for idx, (label, _) in enumerate(nav_items):
            btn = ttk.Button(nav_frame, text=label,
                             command=lambda ix=idx: self._switch_tab(ix),
                             style='Nav.TButton')
            btn.pack(side='left', padx=6, pady=14)
            self._nav_buttons.append(btn)

        separator = tk.Frame(self.root, height=2, bg=C['card'])
        separator.pack(fill='x')

        self._content_frame = tk.Frame(self.root, bg=C['bg'])
        self._content_frame.pack(fill='both', expand=True, padx=20, pady=(12, 10))

        self._tabs = []
        for build_tab in [item[1] for item in nav_items]:
            self._tabs.append(build_tab())

        self._current_tab = 0
        self._switch_tab(0)

        self.root.protocol('WM_DELETE_WINDOW', self._quitter)

    def _switch_tab(self, index: int):
        """Sélectionne l'onglet et met à jour le style de la navbar."""
        for i, tab in enumerate(self._tabs):
            if i == index:
                tab.pack(fill='both', expand=True)
            else:
                tab.pack_forget()

        self._current_tab = index
        for i, btn in enumerate(self._nav_buttons):
            btn_style = 'NavActive.TButton' if i == index else 'Nav.TButton'
            btn.configure(style=btn_style)

    def _poll_enroll(self):
        """Polling pendant l'enregistrement: lit la queue de fin d'enregistrement."""
        try:
            result = self._enroll_done_q.get_nowait()
            self._enroll_active = False
            self._btn_start_enroll.config(state='normal')
            if result[0] == 'ok':
                _, nom, n_img, n_users = result
                self._lbl_enroll_status.config(
                    text=f"✅ {nom} enregistré ({n_img} images)", fg=C['green'])
                self._rafraichir_stats()
                # Mise à jour immédiate de la liste admin
                self._charger_utilisateurs()
                messagebox.showinfo("Succès",
                    f"Utilisateur « {nom} » enregistré avec {n_img} images.\n"
                    f"Modèle entraîné sur {n_users} utilisateur(s).")
                for v in self._vars_enroll.values():
                    v.set('')
            else:
                messagebox.showerror("Erreur enregistrement", result[1])
            return
        except queue.Empty:
            pass

        if self._enroll_active:
            self.root.after(30, self._poll_enroll)

    def _build_tab_enregistrement(self):
        """Onglet Enregistrement (version minimale/placeholder)."""
        tab = tk.Frame(self._content_frame, bg=C['panel'])

        left = tk.Frame(tab, bg=C['panel'], width=340)
        left.pack(side='left', fill='y', padx=20, pady=20)
        left.pack_propagate(False)

        _label(left, "Enregistrement", FONT_HEADER, bg=C['panel']).pack(pady=(0, 8))

        # Champs utilisateur (conservés pour compatibilité future)
        self._vars_enroll = {
            'nom': tk.StringVar(), 'code': tk.StringVar(), 'email': tk.StringVar()
        }
        _label(left, "Nom", FONT_SMALL, bg=C['panel']).pack(anchor='w')
        _entry(left, textvariable=self._vars_enroll['nom']).pack(fill='x', pady=4)
        _label(left, "Code", FONT_SMALL, bg=C['panel']).pack(anchor='w')
        _entry(left, textvariable=self._vars_enroll['code']).pack(fill='x', pady=4)
        _label(left, "Email", FONT_SMALL, bg=C['panel']).pack(anchor='w')
        _entry(left, textvariable=self._vars_enroll['email']).pack(fill='x', pady=4)

        self._btn_start_enroll = _btn(left, "▶  Démarrer l'enregistrement",
                                      lambda: messagebox.showinfo(
                                          "Indisponible", "L'enregistrement a été désactivé dans cette version."),
                                      C['green'])
        self._btn_start_enroll.pack(fill='x', pady=(8, 4))

        self._lbl_enroll_status = _label(left, "Prêt", FONT_SMALL, C['muted'], bg=C['panel'])
        self._lbl_enroll_status.pack()

        right = tk.Frame(tab, bg=C['bg'])
        right.pack(side='left', fill='both', expand=True, padx=(0, 20), pady=20)

        self._lbl_cam_enroll = tk.Label(right, bg=C['bg'],
                                        text="Aperçu caméra", fg=C['muted'], font=FONT_BODY)
        self._lbl_cam_enroll.pack(expand=True)
        return tab

    # ═══════════════════════════════════════════════════════════════════════════
    #  ONGLET 2 – CONTRÔLE D'ACCÈS
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_tab_acces(self):
        tab = tk.Frame(self._content_frame, bg=C['panel'])

        ctrl = tk.Frame(tab, bg=C['panel'])
        ctrl.pack(fill='x', padx=20, pady=10)

        self._btn_start_surv = _btn(ctrl, "▶  Démarrer surveillance",
                                    self._demarrer_surveillance, C['green'])
        self._btn_start_surv.pack(side='left', padx=4)

        self._btn_stop_surv = _btn(ctrl, "⏹  Arrêter",
                                   self._arreter_surveillance, C['accent'])
        self._btn_stop_surv.pack(side='left', padx=4)
        self._btn_stop_surv.config(state='disabled')

        self._lbl_surv_status = _label(ctrl, "Surveillance inactive",
                                       FONT_SMALL, C['muted'], bg=C['panel'])
        self._lbl_surv_status.pack(side='left', padx=16)

        cam_frame = tk.Frame(tab, bg=C['bg'])
        cam_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        self._lbl_cam_surv = tk.Label(cam_frame, bg=C['bg'],
                                      text="Caméra inactive", fg=C['muted'], font=FONT_BODY)
        self._lbl_cam_surv.pack(side='left', expand=True)

        res = tk.Frame(cam_frame, bg=C['panel'], width=280)
        res.pack(side='right', fill='y', padx=(10, 0))
        res.pack_propagate(False)

        _label(res, "Dernier accès", FONT_HEADER, bg=C['panel']).pack(pady=(10, 4))
        self._lbl_result_nom    = _label(res, "—", FONT_HEADER, C['muted'], bg=C['panel'])
        self._lbl_result_nom.pack()
        self._lbl_result_status = _label(res, "—", FONT_BODY, C['muted'], bg=C['panel'])
        self._lbl_result_status.pack()
        self._lbl_result_conf   = _label(res, "", FONT_SMALL, C['muted'], bg=C['panel'])
        self._lbl_result_conf.pack()
        return tab

    def _demarrer_surveillance(self):
        if not self.recog.modele_entraine():
            messagebox.showwarning("Modèle absent",
                "Enregistrez au moins un utilisateur avant de lancer la surveillance.")
            return
        self._surveillance_active = True
        self._btn_start_surv.config(state='disabled')
        self._btn_stop_surv.config(state='normal')
        self._lbl_surv_status.config(text="🟢 Surveillance active", fg=C['green'])
        threading.Thread(target=self._boucle_surveillance, daemon=True).start()
        self._poll_surv()

    def _arreter_surveillance(self):
        self._surveillance_active = False
        self._btn_start_surv.config(state='normal')
        self._btn_stop_surv.config(state='disabled')
        self._lbl_surv_status.config(text="Surveillance inactive", fg=C['muted'])
        self._lbl_cam_surv.config(image='', text="Caméra inactive")

    def _boucle_surveillance(self):
        """Thread de fond : capture, détection, reconnaissance + chiffrement + tatouage.
        AUCUN appel Tkinter depuis ce thread."""
        try:
            cap = self.capture.ouvrir_camera()
        except RuntimeError as e:
            self._surv_q.put(('error', str(e)))
            return

        last_action = 0.0

        while self._surveillance_active:
            ret, frame = cap.read()
            if not ret:
                break

            faces, gray = self.capture.detecter_visages(frame)
            display     = frame.copy()

            for (x, y, w, h) in faces:
                face_img    = gray[y:y+h, x:x+w]
                uid, score  = self.recog.reconnaitre(face_img)
                now         = datetime.now().timestamp()
                cooldown_ok = (now - last_action) > 3.0

                if uid is not None:
                    user = self.db.obtenir_utilisateur_par_id(uid)
                    if user:
                        nom      = user['nom']
                        autorise = bool(user['autorise'])
                        couleur  = (0, 220, 0) if autorise else (0, 0, 220)
                        resultat = 'autorisé'  if autorise else 'non autorisé'
                    else:
                        nom, couleur, resultat = "Inconnu", (0, 0, 220), 'non autorisé'
                else:
                    nom, couleur, resultat = "Imposteur", (0, 0, 255), 'imposteur'

                cv2.rectangle(display, (x, y), (x+w, y+h), couleur, 2)
                cv2.putText(display, f"{nom}  {score:.0%}",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, couleur, 2)

                if cooldown_ok:
                    last_action = now
                    ts_str  = datetime.now().strftime('%Y%m%d_%H%M%S')

                    # ── 1. Sauvegarder l'image brute temporairement ───────────
                    img_brute = os.path.join(settings.LOGS_DIR, f"log_{ts_str}.png")
                    cv2.imwrite(img_brute, frame[y:y+h, x:x+w])

                    # ── 2. Insérer le tatouage LSB (intégrité) ────────────────
                    msg_tat = (f"nom:{nom}|resultat:{resultat}|"
                               f"confiance:{score:.4f}|ts:{ts_str}")
                    try:
                        self.tatouage.inserer_tatouage(img_brute, msg_tat)
                    except Exception as e:
                        print(f"⚠️  Tatouage échoué : {e}")

                    # ── 3. Chiffrer le fichier tatouée → .png.enc ────────────
                    try:
                        img_chiffree = self.chiffre.chiffrer_fichier(img_brute)
                        # img_brute est supprimé par chiffrer_fichier ; on garde le .enc
                        log_img = img_chiffree
                    except Exception as e:
                        print(f"⚠️  Chiffrement échoué, image gardée en clair : {e}")
                        log_img = img_brute

                    # ── 4. Enregistrer le log en base ─────────────────────────
                    self.db.ajouter_log(nom, resultat, score, log_img,
                                        uid if uid is not None else None)

                    # ── 5. Alerte SMTP uniquement pour les imposteurs ─────────
                    if resultat == 'imposteur':
                        threading.Thread(
                            target=self.notif.alerte_imposteur,
                            args=(log_img,), daemon=True).start()

                    # Signaler au main thread
                    try:
                        self._result_q.put_nowait((nom, resultat, score))
                    except queue.Full:
                        pass

            try:
                self._surv_q.put_nowait(('frame', display.copy()))
            except queue.Full:
                pass

        cap.release()
        self._surv_q.put(('stopped', None))

    def _poll_surv(self):
        """Polling dans le main thread : lit les queues de surveillance et met à jour l'UI."""
        try:
            while True:
                msg = self._surv_q.get_nowait()
                kind, data = msg[0], msg[1]
                if kind == 'frame':
                    img = _frame_to_photoimage(data, (700, 480))
                    self._lbl_cam_surv.config(image=img, text='')
                    self._lbl_cam_surv.image = img
                elif kind == 'error':
                    messagebox.showerror("Caméra", data)
                    self._arreter_surveillance()
                    return
                elif kind == 'stopped':
                    break
        except queue.Empty:
            pass

        try:
            while True:
                nom, resultat, score = self._result_q.get_nowait()
                self._afficher_resultat(nom, resultat, score)
                self._rafraichir_stats()
        except queue.Empty:
            pass

        if self._surveillance_active:
            self.root.after(30, self._poll_surv)
        else:
            self._lbl_cam_surv.config(image='', text="Caméra inactive")

    def _afficher_resultat(self, nom, resultat, score):
        couleurs = {'autorisé': C['green'], 'non autorisé': C['accent'], 'imposteur': C['orange']}
        emojis   = {'autorisé': '✅', 'non autorisé': '🚫', 'imposteur': '⚠️'}
        c = couleurs.get(resultat, C['muted'])
        self._lbl_result_nom.config(text=nom, fg=c)
        self._lbl_result_status.config(
            text=f"{emojis.get(resultat, '')} {resultat.capitalize()}", fg=c)
        self._lbl_result_conf.config(text=f"Confiance : {score:.1%}", fg=C['muted'])

    # ═══════════════════════════════════════════════════════════════════════════
    #  ONGLET 3 – JOURNAUX  (temps réel : auto-refresh toutes les 2 s)
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_tab_logs(self):
        tab = tk.Frame(self._content_frame, bg=C['panel'])

        ctrl = tk.Frame(tab, bg=C['panel'])
        ctrl.pack(fill='x', padx=20, pady=10)

        _label(ctrl, "Filtre :", bg=C['panel']).pack(side='left')
        self._filtre_logs = tk.StringVar(value='tous')
        for v, t in [('tous', 'Tous'), ('autorisé', '✅ Autorisés'),
                     ('non autorisé', '🚫 Refusés'), ('imposteur', '⚠️ Imposteurs')]:
            tk.Radiobutton(ctrl, text=t, variable=self._filtre_logs, value=v,
                           command=self._rafraichir_logs,
                           bg=C['panel'], fg=C['text'], selectcolor=C['card'],
                           font=FONT_SMALL,
                           activebackground=C['panel']).pack(side='left', padx=6)

        _btn(ctrl, "🔄 Rafraîchir", self._rafraichir_logs, C['card']).pack(side='right')

        # Indicateur de mise à jour automatique
        self._lbl_logs_indicator = _label(ctrl, "● temps réel", FONT_SMALL,
                                          C['green'], bg=C['panel'])
        self._lbl_logs_indicator.pack(side='right', padx=8)

        cols = ('Horodatage', 'Nom', 'Résultat', 'Confiance', 'Image')
        self._tree_logs = ttk.Treeview(tab, columns=cols, show='headings', height=18)
        for c in cols:
            self._tree_logs.heading(c, text=c)
            self._tree_logs.column(c, width=180 if c != 'Image' else 260, anchor='center')

        sb = ttk.Scrollbar(tab, orient='vertical', command=self._tree_logs.yview)
        self._tree_logs.configure(yscrollcommand=sb.set)
        self._tree_logs.pack(side='left', fill='both', expand=True,
                             padx=(20, 0), pady=(0, 20))
        sb.pack(side='left', fill='y', pady=(0, 20))

        self._tree_logs.bind('<Double-1>', self._voir_log_image)
        self._rafraichir_logs()
        return tab

    def _rafraichir_logs(self):
        """Vide et recharge la Treeview depuis la base de données."""
        for row in self._tree_logs.get_children():
            self._tree_logs.delete(row)
        logs = self.db.obtenir_logs(self._filtre_logs.get())
        tags_map = {'autorisé': 'vert', 'non autorisé': 'rouge', 'imposteur': 'orange'}
        self._tree_logs.tag_configure('vert',   foreground=C['green'])
        self._tree_logs.tag_configure('rouge',  foreground=C['accent'])
        self._tree_logs.tag_configure('orange', foreground=C['orange'])
        for log in logs:
            ts  = log['timestamp'][:19].replace('T', ' ')
            tag = tags_map.get(log['resultat'], '')
            self._tree_logs.insert('', 'end',
                values=(ts, log['nom_detecte'], log['resultat'],
                        f"{log['confiance']:.1%}", log.get('image_path', '')),
                tags=(tag,))
        # Mettre à jour le compteur pour l'auto-refresh
        self._last_log_count = len(logs)

    def _auto_refresh_logs(self):
        """Vérifie toutes les 2 secondes si de nouveaux logs sont arrivés.
        Si oui, recharge silencieusement le tableau sans perturber l'utilisateur."""
        try:
            logs = self.db.obtenir_logs(self._filtre_logs.get())
            if len(logs) != self._last_log_count:
                self._rafraichir_logs()
                # Faire clignoter l'indicateur temps réel
                self._lbl_logs_indicator.config(fg=C['orange'])
                self.root.after(600, lambda: self._lbl_logs_indicator.config(fg=C['green']))
        except Exception:
            pass
        # Replanifier dans 2 secondes (même si la fenêtre est fermée, daemon=True)
        self.root.after(2000, self._auto_refresh_logs)

    def _voir_log_image(self, event):
        sel = self._tree_logs.selection()
        if not sel:
            return
        vals     = self._tree_logs.item(sel[0])['values']
        img_path = str(vals[4]) if len(vals) > 4 else ''
        if not img_path:
            messagebox.showinfo("Image", "Aucune image disponible pour ce log.")
            return

        # ── Déchiffrement à la volée si le fichier est .enc ──────────────────
        if img_path.endswith('.enc'):
            if not os.path.exists(img_path):
                messagebox.showinfo("Image", "Fichier chiffré introuvable.")
                return
            try:
                temp_path = img_path.replace('.enc', '.tmp_view.png')
                self.chiffre.dechiffrer_fichier(img_path, temp_path)
                afficher_path = temp_path
                nettoyer = True
            except Exception as e:
                messagebox.showerror("Déchiffrement", f"Impossible de déchiffrer : {e}")
                return
        else:
            if not os.path.exists(img_path):
                messagebox.showinfo("Image", "Fichier image introuvable.")
                return
            afficher_path = img_path
            nettoyer = False

        win = tk.Toplevel(self.root)
        win.title(f"Image – {vals[1]}")
        win.configure(bg=C['bg'])
        img = ImageTk.PhotoImage(Image.open(afficher_path).resize((400, 400)))
        lbl = tk.Label(win, image=img, bg=C['bg'])
        lbl.image = img
        lbl.pack(padx=20, pady=20)

        # Nettoyer le fichier temporaire quand la fenêtre se ferme
        if nettoyer:
            def _on_close():
                try:
                    os.remove(afficher_path)
                except Exception:
                    pass
                win.destroy()
            win.protocol('WM_DELETE_WINDOW', _on_close)

    # ═══════════════════════════════════════════════════════════════════════════
    #  ONGLET 4 – ADMINISTRATION  (mise à jour temps réel)
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_tab_admin(self):
        tab = tk.Frame(self._content_frame, bg=C['panel'])

        left = tk.Frame(tab, bg=C['panel'], width=340)
        left.pack(side='left', fill='y', padx=20, pady=20)
        left.pack_propagate(False)

        _label(left, "Utilisateurs", FONT_HEADER, bg=C['panel']).pack(pady=(0, 8))

        self._list_users = tk.Listbox(left, bg=C['card'], fg=C['text'], font=FONT_BODY,
                                      selectbackground=C['accent'], height=16,
                                      relief='flat', borderwidth=0)
        self._list_users.pack(fill='both', expand=True)
        self._list_users.bind('<<ListboxSelect>>', self._selectionner_utilisateur)

        _btn(left, "🔄 Rafraîchir", self._charger_utilisateurs, C['card']).pack(
            fill='x', pady=(8, 2))

        right = tk.Frame(tab, bg=C['panel'])
        right.pack(side='left', fill='both', expand=True, padx=(0, 20), pady=20)

        _label(right, "Détails", FONT_HEADER, bg=C['panel']).pack(pady=(0, 8))
        self._lbl_user_details = _label(right, "Sélectionnez un utilisateur",
                                        FONT_BODY, C['muted'], bg=C['panel'])
        self._lbl_user_details.pack(pady=10)

        btn_frame = tk.Frame(right, bg=C['panel'])
        btn_frame.pack(pady=10)

        self._btn_autoriser = _btn(btn_frame, "✅ Autoriser",   self._autoriser_user,  C['green'])
        self._btn_autoriser.grid(row=0, column=0, padx=4, pady=4)
        self._btn_revoquer  = _btn(btn_frame, "🚫 Révoquer",    self._revoquer_user,   C['accent'])
        self._btn_revoquer.grid(row=0, column=1, padx=4, pady=4)
        self._btn_supprimer = _btn(btn_frame, "🗑️ Supprimer",   self._supprimer_user,  C['accent'])
        self._btn_supprimer.grid(row=0, column=2, padx=4, pady=4)
        self._btn_reentrain = _btn(btn_frame, "🧠 Ré-entraîner", self._reentraine,     C['card'])
        self._btn_reentrain.grid(row=1, column=0, columnspan=3, sticky='ew', padx=4, pady=4)

        for b in (self._btn_autoriser, self._btn_revoquer,
                  self._btn_supprimer, self._btn_reentrain):
            b.config(state='disabled')

        self._selected_user = None
        self._charger_utilisateurs()
        return tab

    def _charger_utilisateurs(self):
        """Recharge la liste depuis la DB – appelé lors de toute modification."""
        self._list_users.delete(0, 'end')
        self._users_cache = self.db.lister_utilisateurs()
        for u in self._users_cache:
            status = "✅" if u['autorise'] else "🚫"
            self._list_users.insert('end', f"{status}  {u['nom']}  [{u['code']}]")
        self._rafraichir_stats()

    def _selectionner_utilisateur(self, _):
        sel = self._list_users.curselection()
        if not sel:
            return
        self._selected_user = self._users_cache[sel[0]]
        u = self._selected_user
        details = (f"Nom : {u['nom']}\n"
                   f"Code : {u['code']}\n"
                   f"Email : {u.get('email', '—')}\n"
                   f"Créé le : {u['date_creation'][:10] if u.get('date_creation') else '—'}\n"
                   f"Statut : {'✅ Autorisé' if u['autorise'] else '🚫 Révoqué'}")
        self._lbl_user_details.config(text=details, fg=C['text'])
        for b in (self._btn_autoriser, self._btn_revoquer,
                  self._btn_supprimer, self._btn_reentrain):
            b.config(state='normal')

    def _autoriser_user(self):
        if self._selected_user:
            self.db.modifier_autorisation(self._selected_user['code'], True)
            self._charger_utilisateurs()   # ← mise à jour immédiate

    def _revoquer_user(self):
        if self._selected_user:
            self.db.modifier_autorisation(self._selected_user['code'], False)
            self._charger_utilisateurs()   # ← mise à jour immédiate

    def _supprimer_user(self):
        if not self._selected_user:
            return
        if not messagebox.askyesno("Confirmer",
                f"Supprimer {self._selected_user['nom']} définitivement ? (RGPD)"):
            return
        code = self._selected_user['code']
        uid  = self._selected_user['id']
        user_img_dir = os.path.join(settings.IMAGES_DIR, str(uid))
        if os.path.exists(user_img_dir):
            import shutil
            shutil.rmtree(user_img_dir)
        self.db.supprimer_utilisateur(code)
        try:
            self.recog.entrainer_modele(settings.IMAGES_DIR)
        except Exception:
            pass
        self._selected_user = None
        self._lbl_user_details.config(text="Utilisateur supprimé", fg=C['muted'])
        for b in (self._btn_autoriser, self._btn_revoquer,
                  self._btn_supprimer, self._btn_reentrain):
            b.config(state='disabled')
        self._charger_utilisateurs()       # ← mise à jour immédiate

    def _reentraine(self):
        try:
            n = self.recog.entrainer_modele(settings.IMAGES_DIR)
            messagebox.showinfo("Ré-entraînement",
                                f"Modèle ré-entraîné sur {n} utilisateur(s).")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    # Onglet Sécurité et helpers supprimés (sécurité gérée côté core)

    # ═══════════════════════════════════════════════════════════════════════════
    #  HELPERS COMMUNS
    # ═══════════════════════════════════════════════════════════════════════════
    def _rafraichir_stats(self):
        try:
            s   = self.db.stats()
            txt = (f"👥 {s['utilisateurs']} utilisateurs  |  "
                   f"✅ {s['autorise']}  🚫 {s['refuse']}  ⚠️ {s['imposteur']}  "
                   f"| {s['total']} logs")
            self._lbl_stats.config(text=txt)
        except Exception:
            pass

    def _quitter(self):
        self._surveillance_active = False
        self._enroll_active       = False
        self.root.after(200, self.root.destroy)
