from .capture import CaptureVideo, GestionnaireCapture
from .detection import DetecteurVisage
from .reconnaissance import GestionnaireReconnaissance
from .entrainement import EntraineurModele, entrainer_modele, reentrainer_modele

# Compatibilité des noms d'import utilisés par l'interface
ReconnaisseurVisage = GestionnaireReconnaissance

__all__ = [
    'CaptureVideo',
    'GestionnaireCapture',
    'DetecteurVisage',
    'GestionnaireReconnaissance',
    'ReconnaisseurVisage',
    'EntraineurModele',
    'entrainer_modele',
    'reentrainer_modele',
]
