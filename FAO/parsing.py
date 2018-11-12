#coding : UTF-8

import svgwrite
import os
from FAO.stepReader import *
import svg_stack

# ATTENTION : la version officielle de svg_stack ne fonctionne pas avec python3.
# Pour utiliser svg_stack, installer un fork patché : https://github.com/astraw/svg_stack/issues/3


#chemin du dossier de sortie
parsed_files_path = "/Users/baulieu/scripts/FAO/files/parsing"

def get_parsed_files_path():
    """
    renvoie le chemin du dossier produits par le parser
        argument:
            - entry_files_path:str chemin du dossier des fichiers test d'entrée
    """
    # svg_file_generator(parsed_files_path)
    return parsed_files_path

def parse_all_files(path):
    # nettoyage du dossier -> suppression des anciens fichiers
    if os.path.exists(os.path.join(parsed_files_path, '18mm.svg')):
        os.remove(os.path.join(parsed_files_path, '18mm.svg'))
    if os.path.exists(os.path.join(parsed_files_path, '18mmXL.svg')):
        os.remove(os.path.join(parsed_files_path, '18mmXL.svg'))
    if os.path.exists(os.path.join(parsed_files_path, '35mm.svg')):
        os.remove(os.path.join(parsed_files_path, '35mm.svg'))
    for folderPath in ['18mm_1250_2500_before_nesting', '18mm_1500_3000_before_nesting', '35mm_1250_2500_before_nesting', 'strange_thickness']:
        for name in os.listdir(os.path.join(parsed_files_path, folderPath)):
            os.remove(os.path.join(parsed_files_path, folderPath, name))
    svg_35 = svg_stack.Document()
    svg_18_normal = svg_stack.Document()
    svg_18_XL = svg_stack.Document()
    # traitement de toutes les pièces
    for file in os.listdir(path):
        print(file)
        parse_one_file(os.path.join(path, file))
    # concaténation de toutes les pièces de 35mm en un seul fichier
    layout35 = svg_stack.HBoxLayout()
    for file in os.listdir(os.path.join(parsed_files_path, '35mm_1250_2500_before_nesting')):
        if os.path.splitext(file)[-1].lower() =='.svg':
            layout35.addSVG(os.path.join(parsed_files_path, '35mm_1250_2500_before_nesting', file), alignment = svg_stack.AlignCenter)
    layout35.setSpacing(100)
    svg_35.setLayout(layout35)
    svg_35.save(os.path.join(parsed_files_path, '35mm.svg'))
    # concaténation de toutes les pièces de 18mm en un seul fichier
    layout18normal = svg_stack.HBoxLayout()
    for file in os.listdir(os.path.join(parsed_files_path, '18mm_1250_2500_before_nesting')):
        if os.path.splitext(file)[-1].lower() =='.svg':
            layout18normal.addSVG(os.path.join(parsed_files_path, '18mm_1250_2500_before_nesting', file), alignment = svg_stack.AlignCenter)
    layout18normal.setSpacing(100)
    svg_18_normal.setLayout(layout18normal)
    svg_18_normal.save(os.path.join(parsed_files_path, '18mm.svg'))
    # concaténation de toutes les pièces de 18mm XL en un seul fichier
    layout18XL = svg_stack.HBoxLayout()
    for file in os.listdir(os.path.join(parsed_files_path, '18mm_1500_3000_before_nesting')):
        if os.path.splitext(file)[-1].lower() =='.svg':
            layout18XL.addSVG(os.path.join(parsed_files_path, '35mm_1500_3000_before_nesting', file), alignment = svg_stack.AlignCenter)
    layout18XL.setSpacing(100)
    svg_18_XL.setLayout(layout18XL)
    svg_18_XL.save(os.path.join(parsed_files_path, '18mmXL.svg'))

def parse_one_file(path):
    """
    crée un StepFile à partir du fichier indiqué, effectue les opérations disponibles dans le stepReader, puis le traduit en syntaxe svg et l'écrit dans un fichier.
    Retourne le path du fichier dans lequel la pièce est écrite.
        arguments:
            - path: str chemin du fichier à analyser
    """
    step = StepFile()
    step.read(path)
    if not step.success:
        print("impossible d'ouvrir le fichier : " + path)
    else:
        # on détermine le plan de référence de la pièce
        step.get_ref_plane()
        # on repère les contours supérieurs et intérieurs
        step.process_edge_loops_step_1()
        # on les nettoye, on sépare les poches débouchantes des contours
        step.process_edge_loops_step_2()
        # on détermine le profil d'usinage de chaque contour
        step.process_edge_loops_step_3()
        height = 0
        width = 0
        file_path = ''
        # on mesure la "boite" dans laquelle rentre la pièce -> servira à répartir entre les différentes tailles de panneaux
        if step.ref_plane == 'x':
            height = abs(step.highest_point('z') - step.lowest_point('z'))
            width = abs(step.highest_point('y') - step.lowest_point('y'))
        elif step.ref_plane == 'y':
            height = abs(step.highest_point('x') - step.lowest_point('x'))
            width = abs(step.highest_point('z') - step.lowest_point('z'))
        elif step.ref_plane == 'z':
            height = abs(step.highest_point('y') - step.lowest_point('y'))
            width = abs(step.highest_point('x') - step.lowest_point('x'))
        # on détermine dans quel fichier écrire en fonction des dimensions de la pièce
        # ATTENTION : CHECKER QUE LES TROIS DOSSIERS EN QUESTION EXISTENT, ET LES CRÉER SINON. TROP CHIANT À FAIRE, JE LE FERAI PLUS TARD.
        print(step.thickness)
        if step.thickness == 35:
            file_path = os.path.join(parsed_files_path, '35mm_1250_2500_before_nesting', os.path.splitext(os.path.basename(path))[0] + ".svg")
        elif step.thickness == 18:
            if height < 1250 and width < 2500:
                file_path = os.path.join(parsed_files_path, '18mm_1250_2500_before_nesting', os.path.splitext(os.path.basename(path))[0] + ".svg")
            elif height < 2500 and width < 1250:
                file_path = os.path.join(parsed_files_path, '18mm_1250_2500_before_nesting', os.path.splitext(os.path.basename(path))[0] + ".svg")
            else:
                file_path = os.path.join(parsed_files_path, '18mm_1500_3000_before_nesting', os.path.splitext(os.path.basename(path))[0] + ".svg")
            # il faudrait lever un warning en else ici et quitter la fonction
        else:
            file_path = os.path.join(parsed_files_path, 'strange_thickness', os.path.splitext(os.path.basename(path))[0] + ".svg")
        offset_0 = 0
        offset_1 = 0
        if step.ref_plane == 'x':
            offset_0 = -step.lowest_point('y')
            if step.flip == -1:
                offset_1 = step.highest_point('z')
            else:
                offset_1 = -step.lowest_point('z')
        if step.ref_plane == 'y':
            offset_0 = -step.lowest_point('z')
            if step.flip == -1:
                offset_1 = step.highest_point('x')
            else:
                offset_1 = -step.lowest_point('x')
        if step.ref_plane == 'z':
            offset_0 = -step.lowest_point('x')
            if step.flip == -1:
                offset_1 = step.highest_point('y')
            else:
                offset_1 = -step.lowest_point('y')
        # début de l'écriture dans un fichier svg ne contenant que la pièce en question
        print('------------')
        print(file_path)
        print('------------')
        dwg = svgwrite.Drawing(filename = file_path, size = (width, height), viewBox = ("0 0 {} {}".format(width,height)))
        for key in step.bottom_edge_loops.keys():
            # on convertit toutes les Curve du edge_loop en 2D
            pt_list = []
            str_list = []
            p = step.bottom_edge_loops[key][0].start_point
            str_list.append("M {},{}".format(relevant_coord(p, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(p, step.ref_plane)[1] + offset_1))
            for c in step.bottom_edge_loops[key]:
                if c.type == 'Line':
                    str_list.append(" L {},{}".format(relevant_coord(c.end_point, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(c.end_point, step.ref_plane)[1] + offset_1))
                elif c.type == 'Circle':
                    if step.flip == -1:
                        str_list.append(" A {},{} {} {} {} {} {}".format(c.circle_radius, c.circle_radius, 0, 0, c.circle_direction, relevant_coord(c.end_point, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(c.end_point, step.ref_plane)[1] + offset_1))
                    else:
                        str_list.append(" A {},{} {} {} {} {} {}".format(c.circle_radius, c.circle_radius, 0, 0, abs(c.circle_direction - 1), relevant_coord(c.end_point, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(c.end_point, step.ref_plane)[1] + offset_1))
            s = ' '.join(str_list)
            # on définit le stroke à utiliser
            r = 0
            g = 0
            b = 0
            if step.machining[key].type == 'profile_inside':
                r = 200
            elif step.machining[key].type == 'profile_outside':
                r = 100
            elif step.machining[key].type == 'pocket_outside':
                g = 200
            elif step.machining[key].type == 'pocket_inside':
                g = 100
            elif step.machining[key].type == 'engrave':
                r = 250
            b = int(step.machining[key].target_depth)
            dwg.add(dwg.path(s).stroke(color = 'rgb({}, {}, {})'.format(r, g, b), width = 0.2).fill("none"))
        for key in step.top_edge_loops.keys():
            # on convertit toutes les Curve du edge_loop en 2D
            pt_list = []
            str_list = []
            p = step.top_edge_loops[key][0].start_point
            str_list.append("M {},{}".format(relevant_coord(p, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(p, step.ref_plane)[1] + offset_1))
            for c in step.top_edge_loops[key]:
                if c.type == 'Line':
                    str_list.append(" L {},{}".format(relevant_coord(c.end_point, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(c.end_point, step.ref_plane)[1] + offset_1))
                elif c.type == 'Circle':
                    if step.flip == -1:
                        str_list.append(" A {},{} {} {} {} {} {}".format(c.circle_radius, c.circle_radius, 0, 0, c.circle_direction, relevant_coord(c.end_point, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(c.end_point, step.ref_plane)[1] + offset_1))
                    else:
                        str_list.append(" A {},{} {} {} {} {} {}".format(c.circle_radius, c.circle_radius, 0, 0, abs(c.circle_direction - 1), relevant_coord(c.end_point, step.ref_plane)[0] + offset_0, step.flip * relevant_coord(c.end_point, step.ref_plane)[1] + offset_1))
            s = ' '.join(str_list)
            # on définit le stroke à utiliser
            r = 0
            g = 0
            b = 0
            if step.machining[key].type == 'profile_inside':
                r = 200
            elif step.machining[key].type == 'profile_outside':
                r = 100
            elif step.machining[key].type == 'pocket_outside':
                g = 200
            elif step.machining[key].type == 'pocket_inside':
                g = 100
            elif step.machining[key].type == 'engrave':
                r = 255
            b = int(step.machining[key].target_depth)
            dwg.add(dwg.path(s).stroke(color = 'rgb({}, {}, {})'.format(r, g, b), width = 0.2).fill("none"))
        dwg.save()
    return file_path

def relevant_coord(point, axis):
    result = []
    if axis == 'x':
        result = point[1:]
    elif axis == 'y':
        # result = point[::2].reverse()
        result = [point[2], point[0]]
    elif axis == 'z':
        result = point[:2]
    return result

def svg_file_generator(parsed_files_path):
    """
    génere trois fichiers svg vides dans le dossier spécifié
        argument:
            - parsed_files_path:str chemin du dossier des fichiers test d'entrée
    """
    #vider le dossier de destination
    for file_path in os.listdir(parsed_files_path):
        os.remove(os.path.join(parsed_files_path, file_path))
    #création de chaque fichier vide.
    dwg1 = svgwrite.Drawing(os.path.join(parsed_files_path, '18mm.svg'), profile='tiny')
    dwg1.add(dwg1.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))
    dwg2 = svgwrite.Drawing(os.path.join(parsed_files_path, '18mmXL.svg'), profile='tiny')
    dwg3 = svgwrite.Drawing(os.path.join(parsed_files_path, '35mm.svg'), profile='tiny')
    #enregistrement des fichiers
    dwg1.save()
    dwg2.save()
    dwg3.save()
    return "boloooooooooos"
