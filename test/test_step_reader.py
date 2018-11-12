#test

from FAO import *
import pytest
import os
from FAO.stepReader import *


# test parsing

#chemins du dossier où sont stockés les fichiers de test
#@pytest.fixture()
#def path_test_files():
#    return "/Users/baulieu/scripts/FAO/test/test_files/pieces_STP"

# chemin du dossier contenant de nombreuses fichier STEP standards
path = "/Users/baulieu/scripts/FAO/test/test_files/pieces_STP"
# chemin d'un fichier STEP complexe connu
path2 = "/Users/baulieu/scripts/FAO/test/test_files/TeamDesk_pied_35.stp"

def test_read_step_file():
    '''
    ouvre tous les fichiers step du dossier test pour vérifier qu'ils peuvent tous être parsés, et vérifie qu'aucune parenthèse n'est restée dans les propriétésself.
        argument:
    '''
    step = StepFile()
    for file in os.listdir(path):
        step.read(os.path.join(path, file))
        for key in step.elements.keys():
            for elem in step.elements[key]['properties']:
                assert ')' not in elem

def test_get_ref_plane():
    '''
    ouvre tous les fichiers step du dossier test pour vérifier qu'ils définissent tous un plan de référence
        argument:
    '''
    step = StepFile()
    for file in os.listdir(path):
        step.read(os.path.join(path, file))
        step.ref_plane = ''
        step.get_ref_plane()
        print(file)
        print(step.ref_plane)
        assert step.ref_plane is not ''

def test_get_thickness_axis():
    '''
    ouvre un fichier connu et vérifie que ses dimensions sur les trois axes sont bonnes
        argument:
    '''
    step = StepFile()
    step.read(path2)
    assert step.get_thickness_axis('x') == 35
    assert step.get_thickness_axis('y') == 980
    assert step.get_thickness_axis('z') == 731
