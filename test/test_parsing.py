#test

from FAO import *
import pytest
import os
from FAO.parsing import *


# test parsing

# chemins du dossier où sont stockés les fichiers de test
#@pytest.fixture()
#def path_test_files():
#    return "/Users/baulieu/scripts/FAO/test/test_files"


def test_nombre_fichiers_sortie_parsing():
    """
    Vérifie qu'il n'y a que trois fichiers dans le dossier de sortie du parsing
        argument:
            - path_test_files:str chemin du dossier des fichiers test d'entrée
    """
    path = get_parsed_files_path()
    files_list = [f for f in os.listdir(path) if f[0] != '.' and not os.path.isdir(f)]
    assert len(files_list) == 3

def test_format_fichiers_sortie_parsing():
    """
    Vérifie que tous les fichiers renvoyés par le parser sont des .SVG
        argument:
            - path_test_files:str chemin du dossier des fichiers test d'entrée
    """
    path = get_parsed_files_path()
    files_list = [f for f in os.listdir(path) if f[0] != '.' and not os.path.isdir(f)]
    extensions = [f for f in files_list if os.path.splitext(f)[-1].lower() == '.svg']
    assert len(extensions) == 3
