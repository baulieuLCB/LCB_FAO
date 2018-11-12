#coding: utf-8

import numpy
import re
import os
import warnings
import math

class StepFile:
    def __init__(self):
        # chemin d'accès du fichier de base
        self.file_path = ''
        # indique si la lecture a réussi ou si le fichier pose problème -> À TESTER APRÈS TOUTE OUVERTURE/LECTURE
        self.success = False
        # plan de référence de la pièce. Défini par l'axe normal au plan : 'x', 'y' ou 'z'
        self.ref_plane = ''
        # dictionnaire (keys = index) des contours fermés définissant l'objet
        self.edge_loops = dict()
        self.debug_edge_loop_ref = dict() # pour chaque référence dans step.edge_loops, contient la liste des références des oriented_edges et des edge_curves
        # dictionnaire de tous les éléments définits par le fichier STEP et jugés intéressants
        self.elements = dict()
        # dictionnaires des edge_loop comprises dans les deux plans qui nous intéressent : le plan supérieur et le plan inférieur.
        self.bottom_edge_loops = dict()
        self.top_edge_loops = dict()
        # dictionnaire des types d'usinage par edge_loop (reprise des références de self.edge_loops)
        self.machining = dict()
        # épaisseur de la pièce.
        self.thickness = 0
        # vaut 1 si la pièce est posée vers le haut, -1 si elle est posée vers le bas
        self.flip = 1
        # liste des types de données intéressantes dans le fichier STEP
        self.elements_of_interest = [
        'EDGE_LOOP',
        'ORIENTED_EDGE',
        'EDGE_CURVE',
        'VERTEX_POINT',
        'LINE',
        'CARTESIAN_POINT',
        'VECTOR',
        'DIRECTION',
        'CIRCLE',
        'AXIS2_PLACEMENT_3D'
        ]

    def read(self, file_path):
        '''
        Récupère les données placées dans le fichier step et les transforme en données propres.
            argument:
                - file_path:str chemin d'accès du fichier step
        '''
        if (os.path.splitext(file_path)[-1].lower()!='.stp') and (os.path.splitext(file_path)[-1].lower()!='.step'):
            self.success = False
            warnings.warn("WARNING : wrong file path : not a step file: " + file_path)
        else:
            self.file_path = file_path
            self.elements = dict()
            origin_file = open(file_path, 'r')
            # remplit le dictionnaire 'self.elements' avec tous les éléments intéressants du fichier step.
            for line in origin_file:
                if line[0] == '#':
                    ref, line_content = line.split("=")
                    temp = line_content.split('(')
                    type = temp[0]
                    content = ''
                    for elem in temp[1::]:
                        elem = elem.split(')')[0]
                        content += elem
                    if type in self.elements_of_interest:
                        properties = content.split(',')
                        # on arrondit toutes les dimensions au micromètre. (ce genre d'overkill)
                        for i in range(0, len(properties)):
                            try:
                                item = float(properties[i])
                                properties[i] = round(item, 3)
                            except:
                                pass
                        self.elements[ref] = {
                        'type': type,
                        'properties': properties
                        }
            # remplit le dictionnaire 'self.edge_loops' avec tous les EDGE_LOOP du fichier STEP contenues dans 'self.elements'
            edge_loops_list = [self.elements[k] for k in self.elements.keys() if self.elements[k]['type'] == 'EDGE_LOOP']
            count = -1
            for element in edge_loops_list:
                #chaque EDGE_LOOP contient une suite de ORIENTED_EDGE -> on les récupère.
                oriented_edges = [self.elements[k] for k in element['properties'][1::]]
                #chaque ORIENTED_EDGE peut être soit un point, soit un EDGE_CURVE. On ne garde que les EDGE_CURVE
                edge_curves = [(self.elements[elem['properties'][3]],elem['properties'][4]) for elem in oriented_edges if self.elements[elem['properties'][3]]['type']=="EDGE_CURVE"]
                edge_curve_list = []
                count+=1
                self.debug_edge_loop_ref[count] = dict()
                self.debug_edge_loop_ref[count]['edge_curves'] = [elem['properties'][3] for elem in oriented_edges if self.elements[elem['properties'][3]]['type']=="EDGE_CURVE"]
                for edge_curve_complete in edge_curves:
                    edge_curve = edge_curve_complete[0]
                    orientation = edge_curve_complete[1]
                    #récupérer les coordonnées exactes du start_point via le EDGE_CURVE->VERTEX_POINT->CARTESIAN_POINT
                    vertex_start_point = self.elements[edge_curve['properties'][1]]
                    cartesian_start_point = self.elements[vertex_start_point['properties'][1]]
                    curve_start_point = numpy.array([
                    float(cartesian_start_point['properties'][1]),
                    float(cartesian_start_point['properties'][2]),
                    float(cartesian_start_point['properties'][3]),
                    ])
                    #récupérer les coordonnées exactes du end_point via le EDGE_CURVE->VERTEX_POINT->CARTESIAN_POINT
                    vertex_end_point = self.elements[edge_curve['properties'][2]]
                    cartesian_end_point = self.elements[vertex_end_point['properties'][1]]
                    curve_end_point = numpy.array([
                    float(cartesian_end_point['properties'][1]),
                    float(cartesian_end_point['properties'][2]),
                    float(cartesian_end_point['properties'][3]),
                    ])
                    #récupérer l'objet LINE ou CIRCLE associé à la courbe
                    temp = self.elements[edge_curve['properties'][3]]
                    #c'est une LINE -> aucun autre attribut à récupérer
                    if temp['properties'][0] == "'Line'":
                        curve_type = 'Line'
                        curve = Curve(curve_type, curve_start_point, curve_end_point, None, None, 1)
                    #c'est un CIRCLE -> il faut récupérer le rayon et le centre du cercle (qui est le point réference du AXIS2_PLACEMENT_3D)
                    elif temp['properties'][0] == "'generated circle'":
                        curve_type = 'Circle'
                        curve_radius = float(temp['properties'][2])
                        # gros fail de tentative de recalcul du rayon des arcs -> tous les arcs ne sont pas des demi-cercles...
                        # curve_radius = math.sqrt((curve_end_point[2] - curve_start_point[2])**2 + (curve_end_point[1] - curve_start_point[1])**2 + (curve_end_point[0] - curve_start_point[0])**2) / 2
                        axis_center = self.elements[temp['properties'][1]]
                        cartesian_center = self.elements[axis_center['properties'][1]]
                        curve_center = numpy.array([
                        float(cartesian_center['properties'][1]),
                        float(cartesian_center['properties'][2]),
                        float(cartesian_center['properties'][3]),
                        ])
                        # explication : un cercle est défini en svg par son point de départ, d'arrivée, son rayon et deux valeurs:
                        #   -> large_arc_flag : détermine si l'angle de l'arc de cercle est supérieur ou égal à 180°.
                        #   -> sweep_flag : détermine l'angle de départ de l'arc.
                        #       (peut être compris par : sachant que le cercle est construit dans le sens horaire, faut-il se placer au-dessus ou en-dessous du plan de référence?)
                        #       Cette donnée est stockée dans le boléen en dernier élément du EDGE_CURVE correspondant.
                        direction_value = 0
                        # pour déterminer la valeur finale de direction_value, il faut regarder deux paramètres:
                        #   -> la direction de l'axe définissant le cercle (cette direction est manifestement choisie de manière aléatoire...)
                        #   -> la valeur du boléen en index 4 du EDGE_CURVE, qui fonctionne comme un sweep_flag : choix du sens horaire ou trigo.
                        # première donnée à prendre en compte : le boléen contenu en index 4 du EDGE_CURVE.
                        if edge_curve['properties'][4] == '.F.':
                            direction_value = abs(direction_value - 1)
                        # seconde donnée à prendre en compte : la direction de l'axe donné par la DIRECTION en index 2 de l'Axis2P3D
                        if sum(self.elements[self.elements[temp['properties'][1]]['properties'][2]]['properties'][1:]) < 0:
                            direction_value = abs(direction_value - 1)
                        curve = Curve(curve_type, curve_start_point, curve_end_point, curve_center, curve_radius, direction_value)
                    else:
                        print("type de courbe inattendu")
                    # on complète la liste des courbes qui constituent la EDGE_LOOP
                    edge_curve_list.append(curve)
                # correction à apporter : vérifier l'orientation de chaque courbe, ou la retourner. (vérifier que son point de départ et le point d'arrivée de la précédente)
                # attention : l'erreur peut n'arriver que sur certaines EDGE_CURVE de la EDGE_LOOP -> les vérifier une par une
                edge_curve_list_oriented = []
                # d'abord on recale les deux premières Curve
                if (edge_curve_list[0].end_point==edge_curve_list[1].start_point).all():
                    #bon scenario : les deux premieres Curve sont dans le même sens
                    edge_curve_list_oriented.append(edge_curve_list[0])
                    edge_curve_list_oriented.append(edge_curve_list[1])
                elif (edge_curve_list[0].start_point==edge_curve_list[1].start_point).all():
                    # les deux ont le meme start -> il faut retourner la première Curve
                    c = edge_curve_list[0]
                    edge_curve_list_oriented.append(Curve(c.type, c.end_point, c.start_point, c.circle_center, c.circle_radius, abs(c.circle_direction - 1)))
                    edge_curve_list_oriented.append(edge_curve_list[1])
                elif (edge_curve_list[0].end_point==edge_curve_list[1].end_point).all():
                    #les deux ont le même end -> il faut retourner la seconde Curve
                    c = edge_curve_list[1]
                    edge_curve_list_oriented.append(edge_curve_list[0])
                    edge_curve_list_oriented.append(Curve(c.type, c.end_point, c.start_point, c.circle_center, c.circle_radius, abs(c.circle_direction - 1)))
                elif (edge_curve_list[0].start_point==edge_curve_list[1].end_point).all():
                    #sles deux Curve sont inversées
                    c0 = edge_curve_list[0]
                    c1 = edge_curve_list[1]
                    edge_curve_list_oriented.append(Curve(c0.type, c0.end_point, c0.start_point, c0.circle_center, c0.circle_radius, abs(c0.circle_direction - 1)))
                    edge_curve_list_oriented.append(Curve(c1.type, c1.end_point, c1.start_point, c1.circle_center, c1.circle_radius, abs(c0.circle_direction - 1)))
                else:
                    #scenario inquiétant : les deux ne sont pas adjacents
                    print("défaut de continuité #1")
                    print(edge_curve_list[0].start_point)
                    print(edge_curve_list[0].end_point)
                    print(edge_curve_list[1].start_point)
                    print(edge_curve_list[1].end_point)
                    edge_curve_list_oriented.append(edge_curve_list[0])
                    edge_curve_list_oriented.append(edge_curve_list[1])
                #puis on reprend toutes les Curve suivantes on les faisant coller avec leur adjacent
                for i in range(2, len(edge_curve_list)):
                    if (edge_curve_list[i].start_point==edge_curve_list_oriented[i-1].end_point).all():
                        #la Curve est bien orientée
                        edge_curve_list_oriented.append(edge_curve_list[i])
                    elif (edge_curve_list[i].end_point==edge_curve_list_oriented[i-1].end_point).all():
                        #la Curve est mal orientée
                        c = edge_curve_list[i]
                        edge_curve_list_oriented.append(Curve(c.type, c.end_point, c.start_point, c.circle_center, c.circle_radius, abs(c.circle_direction - 1)))
                    else :
                        #scenario inquiétant : les deux ne sont pas adjacentes. On les copie telles quelles quand même
                        print("défaut de continuité #2")
                        print(edge_curve_list[i-1].start_point)
                        print(edge_curve_list[i-1].end_point)
                        print(edge_curve_list[i].start_point)
                        print(edge_curve_list[i].end_point)
                        edge_curve_list_oriented.append(edge_curve_list[i])
                self.edge_loops[count] = edge_curve_list_oriented
            self.success = True

    def get_ref_plane(self):
        '''
        Repère le plan de référence selon lequel est construit la pièce (en pratique : le plan de la plaque)
            argument:
        '''
        # Pour déterminer le plan en question, on récupère un arc quelconque.
        # Comme nous travaillons en 2,5D, cet arc sera nécessairement dans le plan de référence.
        # La définition des arcs dans le fichier STEP nous donne un axe normal au plan en question.
        circle = None
        for key in self.elements.keys():
            if self.elements[key]['type']=='CIRCLE':
                circle = self.elements[key]
                break
        if circle is not None:
            axis_ref = circle['properties'][1]
            direction_ref = self.elements[axis_ref]['properties'][2]
            direction_coord = self.elements[direction_ref]['properties'][1:]
            if float(direction_coord[0])**2 == 0 and float(direction_coord[1])**2 == 0 and float(direction_coord[2])**2 == 1:
                # le plan de référence est OXY
                self.ref_plane = 'z'
            elif float(direction_coord[0])**2 == 1 and float(direction_coord[1])**2 == 0 and float(direction_coord[2])**2 == 0:
                # le plan de référence est OYZ
                self.ref_plane = 'x'
            elif float(direction_coord[0])**2 == 0 and float(direction_coord[1])**2 == 1 and float(direction_coord[2])**2 == 0:
                # le plan de référence est OZX
                self.ref_plane = 'y'
        else:
            # il n'y a aucun arc de cercle dans le fichier. ah. Alternative : on mesure la pièce dans toutes les directions, et on choisit comme normale la direction qui mesure 18mm ou 35mm en partant de la plus petite
            print('pas de cercle dans le fichier : ' + self.file_path)
            thickness_x = self.get_thickness_axis('x')
            thickness_y = self.get_thickness_axis('y')
            thickness_z = self.get_thickness_axis('z')
            if thickness_x == min(thickness_x, thickness_y, thickness_z) and (thickness_x == 18 or thickness_x==35):
                self.ref_plane = 'x'
            elif thickness_y == min(thickness_x, thickness_y, thickness_z) and (thickness_y == 18 or thickness_y==35):
                self.ref_plane = 'y'
            else:
                self.ref_plane = 'z'

    def get_thickness_axis(self, axis):
        '''
        Renvoie l'épaisseur de la pièce sur un axe donné. Méthode simple : on trouve le point le plus haut, le plus bas et on renvoie la différence.
            argument:
                -axis: str nom de l'axe en question (X, Y ou Z)
        '''
        max = 0
        min = 0
        index = 1
        if axis.lower() == 'y':
            index = 2
        elif axis.lower() == 'z':
            index = 3
        for key in self.elements.keys():
            p = self.elements[key]
            if p['type'] == "CARTESIAN_POINT":
                if float(p['properties'][index]) > max:
                    max = float(p['properties'][index])
                elif float(p['properties'][index]) < min:
                    min = float(p['properties'][index])
        result = max-min
        return result

    def edge_loop_in_plane(self, ref_edge_loop, axis, height):
        '''
        Vérifie si tous les points d'une edge_loop sont contenus dans un même plan défini par la normale du plan (axis) et l'abscisse sur cette normale (height)
            argument:
                - ref_edge_loop:str reference d'une edge_loop dans le dictionnaire self.edge_loops
                - axis:str axe normal au plan ('x', 'y' ou 'z')
                - height:float abscisse sur l'axe définissant la position du plan
        '''
        result = True
        index = 0
        if axis.lower() == 'y':
            index = 1
        elif axis.lower() == 'z':
            index = 2
        # on liste les hauteurs de tous les points de la edge_loop
        height_list = []
        for curve in self.edge_loops[ref_edge_loop]:
            height_list.append(curve.start_point[index])
            height_list.append(curve.end_point[index])
        for h in height_list:
            if h != height:
                result = False
        return result

    def highest_point(self, axis):
        '''
        Renvoie la hauteur du point le plus haut suivant l'axe donné.
            argument:
                -axis: str axe définissant la hauteur ('x', 'y' ou 'z')
        '''
        changed = False
        max = 0
        index = 1
        if axis.lower() == 'y':
            index = 2
        elif axis.lower() == 'z':
            index = 3
        for key in self.elements.keys():
            p = self.elements[key]
            if p['type'] == "CARTESIAN_POINT":
                if float(p['properties'][index]) > max:
                    max = float(p['properties'][index])
                    changed = True
                elif changed is not True:
                    max = float(p['properties'][index])
                    changed = True
        return max

    def lowest_point(self, axis):
        '''
        Renvoie la hauteur du point le plus bas suivant l'axe donné.
            argument:
                -axis: str axe définissant la hauteur ('x', 'y' ou 'z')
        '''
        changed = False
        min = 0
        index = 1
        if axis.lower() == 'y':
            index = 2
        elif axis.lower() == 'z':
            index = 3
        for key in self.elements.keys():
            p = self.elements[key]
            if p['type'] == "CARTESIAN_POINT":
                if float(p['properties'][index]) < min:
                    min = float(p['properties'][index])
                    changed = True
                elif changed is not True:
                    min = float(p['properties'][index])
                    changed = True
        return min

    def process_edge_loops_step_1(self):
        '''
        remplit les dictionnaires top_edge_loops et bottom_edge_loops.
        WARNING : cas non géré pour l'instant : pocket in a pocket #muycomplicado (information perdue dans cette fonction)
            argument:
        '''
        # récupérer les hauteurs du plan le plus haut et le plus bas.
        # ATTENTION pour l'instant on ne sait pas lequel est le supérieur, lequel est l'inférieur
        point_min = self.lowest_point(self.ref_plane)
        point_max = self.highest_point(self.ref_plane)
        temp_lowest_loops = dict()
        temp_highest_loops = dict()
        # on parcourt tous les edge_loops
        for key in self.edge_loops.keys():
            # on vérifie si il est dans le plan inférieur ou dans le plan supérieur
            if self.edge_loop_in_plane(key, self.ref_plane, point_min):
                temp_lowest_loops[key] = self.edge_loops[key]
            elif self.edge_loop_in_plane(key, self.ref_plane, point_max):
                temp_highest_loops[key] = self.edge_loops[key]
        # repérer le plan inférieur.
        areas = dict()
        areas_lowest = []
        for key in temp_lowest_loops.keys():
            # si la edge_loop est uniquement composée d'un cercle, on calcule l'aire du cercle
            if len(temp_lowest_loops[key]) == 1 and temp_lowest_loops[key].type == 'Circle':
                areas[key] = math.pi*temp_lowest_loops[key].radius**2
            # sinon, on remplit un tableau des coordonnées des coins du polygone. On suppose que toutes les arètes sont droites.
            else:
                temp_coord = []
                for c in temp_lowest_loops[key]:
                    if self.ref_plane == 'x':
                        temp_coord.append((c.start_point[1], c.start_point[2]))
                    if self.ref_plane == 'y':
                        temp_coord.append((c.start_point[0], c.start_point[2]))
                    if self.ref_plane == 'z':
                        temp_coord.append((c.start_point[0], c.start_point[1]))
                areas[key] = self.polygon_area(temp_coord)
                areas_lowest.append(areas[key])
        areas_highest = []
        for key in temp_highest_loops.keys():
            # si la edge_loop est uniquement composée d'un cercle, on calcule l'aire du cercle
            if len(temp_highest_loops[key]) == 1 and temp_highest_loops[key].type == 'Circle':
                areas[key] = math.pi*temp_highest_loops[key].radius**2
            # sinon, on remplit un tableau des coordonnées des coins du polygone. On suppose que toutes les arètes sont droites.
            else:
                temp_coord = []
                for c in temp_highest_loops[key]:
                    if self.ref_plane == 'x':
                        temp_coord.append((c.start_point[1], c.start_point[2]))
                    if self.ref_plane == 'y':
                        temp_coord.append((c.start_point[0], c.start_point[2]))
                    if self.ref_plane == 'z':
                        temp_coord.append((c.start_point[0], c.start_point[1]))
                areas[key] = self.polygon_area(temp_coord)
                areas_highest.append(areas[key])
        highest_surface_effective_area = 0
        for key in temp_highest_loops.keys():
            if areas[key] == max(areas_highest):
                highest_surface_effective_area += areas[key]
            else:
                highest_surface_effective_area -= areas[key]
        lowest_surface_effective_area = 0
        for key in temp_lowest_loops.keys():
            if areas[key] == max(areas_lowest):
                lowest_surface_effective_area += areas[key]
            else:
                lowest_surface_effective_area -= areas[key]
        ref_delete = []
        if lowest_surface_effective_area > highest_surface_effective_area:
            # cas normal -> on reporte juste le highest dans le top et le lowest dans le bottom
            self.top_edge_loops = temp_highest_loops
            self.bottom_edge_loops = temp_lowest_loops
        else:
            # on inverse
            self.top_edge_loops = temp_lowest_loops
            self.bottom_edge_loops = temp_highest_loops
            # la pièce est "posée vers le bas", on modifie self.flip
            self.flip = -1

    def process_edge_loops_step_2(self):
        '''
        Nettoye les edge_loops de la face supérieure -> effectue un XOR entre les courbes extérieures du top_edge_loops et du bottom_edge_loops
            argument:
        '''
        ref = ''
        for k in self.bottom_edge_loops.keys():
            ref = k
        # on parcourt les edge_loop du top et on effectue un XOR avec la edge_loop du bottom
        for bottom_key in self.bottom_edge_loops.keys():
            for key in self.top_edge_loops.keys():
                count = 0
                to_delete = []
                for k in range(0, len(self.top_edge_loops[key])):
                    curve_top = self.top_edge_loops[key][k]
                    for curve_bottom in self.bottom_edge_loops[bottom_key]:
                        if self.is_curve_contained(curve_top, curve_bottom):
                            if k not in to_delete: # on suppose ici qu'une Curve ne peut être contenue que dans une seule Curve du bottom -> necessaire car parfois les courbes sont découpées en plusieurs arcs #CATIALOVE
                                to_delete.append(k)
                for i in to_delete[::-1]:
                    del self.top_edge_loops[key][i]
                    count+=1
        # on a supprimé les superpositions, à présent il faut éclater les Curve non continues et les compléter
        # on parcourt les top_edge_loops.
        i = 0
        while i < len(self.top_edge_loops.keys()):
            # on vérifie que la edge_loop est continue
            curve_continue = True
            j = 0
            # on récupère la référence effective de l'indice i dans le dictionnaire top_edge_loops
            k = list(self.top_edge_loops.keys())[i]
            print(self.top_edge_loops.keys())
            print(k)
            while j < len(self.top_edge_loops[k])-1:
                if not (self.top_edge_loops[k][j].end_point == self.top_edge_loops[k][j+1].start_point).all():
                    curve_continue = False
                    break
                j+=1
            # vérifier que la edge_loop n'est pas vide, sinon -> on la supprime
            if len(self.top_edge_loops[k]) == 0:
                del self.top_edge_loops[k]
                del self.edge_loops[k]
            else:
                if not curve_continue:
                    # effectuer la rupture
                    self.edge_loops[len(self.edge_loops)] = self.top_edge_loops[k][j+1:] # on reporte cette nouvelle edge_loop dans le dictionnaire principal
                    self.top_edge_loops[len(self.edge_loops)-1] = self.top_edge_loops[k][j+1:] # on reporte cette nouvelle edge_loop dans le dictionnaire des edge_loop du top, en respectant l'indexation.
                    self.top_edge_loops[k] = self.top_edge_loops[k][:j+1]
                    ## TODO: améliorer le process en allongeant la poche plutot qu'en la fermant simplement avec une Line
                    c = Curve('Line', self.top_edge_loops[k][-1].end_point, self.top_edge_loops[k][0].start_point, None, None, 1)
                    self.top_edge_loops[k].append(c)
                else :
                    # checker la liaison dernier-premier et directement relier sans faire de rupture
                    if not (self.top_edge_loops[k][0].start_point==self.top_edge_loops[k][-1].end_point).all():
                        ## TODO: améliorer le process en allongeant la poche plutot qu'en la fermant simplement avec une Line
                        c = Curve('Line', self.top_edge_loops[k][-1].end_point, self.top_edge_loops[k][0].start_point, None, None, 1)
                        self.top_edge_loops[k].append(c)
                i+=1

    def process_edge_loops_step_3(self):
        '''
        Détermine le profil de chaque edge_curve des dictionnaires self.top_edge_loops et self.bottom_edge_loops
        ATTENTION : modifier ici le ratio surface/périmetre pour la limite entre poche intérieure et contour intérieur
        ATTENTION_BIS : modifier le mode de détection du contour principal (algo de determination d'inclusion d'un contour dans un autre?) (ex : crash pour plateau de 1,50m)
            argument:
        '''
        # définition du ratio permettant de séparer les contours intérieurs des poches. Ratio en mm.
        # en pratique : si on devait usiner un rectangle long, ce serait la largeur du rectangle divisée par deux. à minimiser -> contours complexes
        ratio = 15
        # on mesure l'épaisseur de la pièce pour faire les contours
        self.thickness = int(self.get_thickness_axis(self.ref_plane))
        # on commence par mesurer les aires des bottom_edge_loops pour repérer le plus grand
        bottom_areas = []
        for key in self.bottom_edge_loops.keys():
            # il ne s'agira que de contours, puisqu'on est sur la face de dessous
            polygon = []
            for c in self.bottom_edge_loops[key]:
                polygon.append(c.start_point[1:])
            bottom_areas.append(self.polygon_area(polygon))
        # pour chaque edge_loop, on décide du type d'usinage à effectuer, et on le rentre dans self.machining
        for key in self.bottom_edge_loops.keys():
            polygon = []
            for c in self.bottom_edge_loops[key]:
                polygon.append(c.start_point[1:])
            edge_loop_area = self.polygon_area(polygon)
            if edge_loop_area == max(bottom_areas):
                # ce contour est le plus grand des contours du bottom, il s'agit forcément d'un contour extérieur de toute la profondeur.
                # ATTENTION : méthode de détermination à modifier #c'estpasbien
                self.machining[key] = MachiningProfile(key, self.bottom_edge_loops[key], 'profile_outside', 'straight_mill', 8, 5, 8, self.thickness+0.3, 3.1, 0)
            else:
                # choisir entre contour intérieur ou poche traversante
                perimeter = 0
                for i in range(0,len(polygon)-1):
                    perimeter += math.sqrt((polygon[i][0] - polygon[i+1][0])**2 + (polygon[i][1] - polygon[i+1][1])**2)
                if edge_loop_area / perimeter < ratio:
                    # le edge_loop est une poche intérieure
                    self.machining[key] = MachiningProfile(key, self.bottom_edge_loops[key], 'pocket_inside', 'straight_mill', 8, 5, 8, self.thickness+0.3, 3.1, 0)
                else:
                    # le edge_loop est un contour intérieur
                    self.machining[key] = MachiningProfile(key, self.bottom_edge_loops[key], 'profile_inside', 'straight_mill', 8, 5, 8, self.thickness+0.3, 3.1, 0)
        for key in self.top_edge_loops.keys():
            # il ne s'agit que de poches, les contours sont tous présents dans le bottom_edge_loops
            # ATTENTION : gérer le cas où on a une poche de toute la profondeur -> anormal, drop the pocket
            polygon = []
            perimeter = 0
            for c in self.top_edge_loops[key]:
                polygon.append(c.start_point[1:])
            for i in range(0,len(polygon)-1):
                perimeter += math.sqrt((polygon[i][0] - polygon[i+1][0])**2 + (polygon[i][1] - polygon[i+1][1])**2)
            # (attention, peu fiable, peut-être vrai auparavant) -> par construction, toutes les poches sont des contours extérieurs. -> ??????
            # opération : trouver le fond de la poche. technique : on choisit un point au pif, et on trouve le point le plus proche sur l'axe de référence
            # attention : on est obligés de chercher dans les points des edge_loops -> des points de construction se baladent dans self.elements, comme les milieux des Line.
            p = self.top_edge_loops[key][0].start_point
            min_depth = self.thickness # va recevoir la profondeur de la poche
            index = 0
            if self.ref_plane == 'y':
                index = 1
            if self.ref_plane == 'z':
                index = 2
            for i in self.edge_loops.keys():
                # on vérifie que la edge_loop en question n'appartient ni au top ni au bottom:
                if i not in list(self.top_edge_loops.keys()) and i not in list(self.bottom_edge_loops.keys()):
                    # on vérifie que cet edge_loop est bien parallèle au plan de référence
                    if self.edge_loop_in_plane(i, self.ref_plane, self.edge_loops[i][0].start_point[index]):
                        # on vérifie qu'il y a bien un point situé sur le même axe que notre point choisi au hasard
                        for curve in self.edge_loops[i]:
                            if self.ref_plane == 'x':
                                if (curve.start_point[1:] == p[1:]).all():
                                    if abs(p[0] - curve.start_point[0]) < min_depth:
                                        min_depth = abs(p[0] - curve.start_point[0])
                            if self.ref_plane == 'y':
                                if (curve.start_point[::2] == p[::2]).all():
                                    if abs(p[0] - curve.start_point[0]) < min_depth:
                                        min_depth = abs(p[0] - curve.start_point[0])
                            if self.ref_plane == 'z':
                                if (curve.start_point[:2] == p[:2]).all():
                                    if abs(p[0] - curve.start_point[0]) < min_depth:
                                        min_depth = abs(p[0] - curve.start_point[0])
            self.machining[key] = MachiningProfile(key, self.top_edge_loops[key], 'pocket_inside', 'straight_mill', 8, 5, 8, min_depth, 3.1, 0)
        for key in self.machining.keys():
            print("💪  " + str(key) + "    " + self.machining[key].type + "   " + str(self.machining[key].target_depth))
        print(self.flip)
        return False

    # fonctions utiles :

    def polygon_area(self, corners):
        '''
        Renvoie l'aire du polygone défini par une suite de points (corners) en utilisant la méthode shoelace.
            argument:
                -corners:[] liste des points définissants le polygone
        '''
        n = len(corners) # of corners
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += corners[i][0] * corners[j][1]
            area -= corners[j][0] * corners[i][1]
        area = abs(area) / 2.0
        return area

    def is_curve_contained(self, curve_1, curve_2):
        '''
        Prend deux Curve en entrée et vérifie si la première est contenue dans la seconde
        ATTENTION : pour l'instant, pour vérifier qu'un cercle est contenu dans l'autre, on vérifie juste que leur centre et rayon sont identiques
            arguments:
                -curve_1: Curve coubre qui doit contenue
                -curve_2: Curve courbe contenante
        '''
        result = False
        if curve_1.type == curve_2.type:
            # les deux courbes sont de même type, on différenciera les cas Circle et Line
            type = curve_1.type
            if type == 'Circle':
                # on projette tous les points en 2D sur le plan de référence
                if self.ref_plane == 'x':
                    circle_center_1_2D = curve_1.circle_center[1:]
                    circle_center_2_2D = curve_2.circle_center[1:]
                elif self.ref_plane == 'y':
                    circle_center_1_2D = curve_1.circle_center[::2]
                    circle_center_2_2D = curve_2.circle_center[::2]
                else:
                    circle_center_1_2D = curve_1.circle_center[0:2]
                    circle_center_2_2D = curve_2.circle_center[0:2]
                if (circle_center_1_2D == circle_center_2_2D).all() and curve_1.circle_radius == curve_2.circle_radius:
                    result = True
            elif type == 'Line':
                # on projette tous les points en 2D sur le plan de référence
                if self.ref_plane == 'x':
                    start_point_1_2D = curve_1.start_point[1:]
                    end_point_1_2D = curve_1.end_point[1:]
                    start_point_2_2D = curve_2.start_point[1:]
                    end_point_2_2D = curve_2.end_point[1:]
                elif self.ref_plane == 'y':
                    start_point_1_2D = curve_1.start_point[::2]
                    end_point_1_2D = curve_1.end_point[::2]
                    start_point_2_2D = curve_2.start_point[::2]
                    end_point_2_2D = curve_2.end_point[::2]
                else:
                    start_point_1_2D = curve_1.start_point[0:2]
                    end_point_1_2D = curve_1.end_point[0:2]
                    start_point_2_2D = curve_2.start_point[0:2]
                    end_point_2_2D = curve_2.end_point[0:2]
                if self.is_point_in_segment(start_point_1_2D, start_point_2_2D, end_point_2_2D) and self.is_point_in_segment(end_point_1_2D, start_point_2_2D, end_point_2_2D):
                    result = True
        return result

    def is_point_in_segment(self, p_1, p_2, p_3):
        '''
        Retourne True si point_1 appartient au segment [point_2, point_3], False sinon
            arguments:
                -p_1: numpy.array(3) point 1
                -p_2: numpy.array(3) point 2
                -p_3: numpy.array(3) point 3
        '''
        result = False
        # méthode : on calcule la distance entre chaque. la distance p_2-p_3 doit être égale à p_2-p_1 + p_1-p_3
        # moi = BEAUCOUP TROP CON -> en fait comme tout est en 2D ça aurait pu être fait plus simplement. Bah super.
        D23 = math.sqrt((p_2[0]-p_3[0])**2 + (p_2[1]-p_3[1])**2)
        D21 = math.sqrt((p_2[0]-p_1[0])**2 + (p_2[1]-p_1[1])**2)
        D13 = math.sqrt((p_1[0]-p_3[0])**2 + (p_1[1]-p_3[1])**2)
        if(D23 == D21 + D13):
            result = True
        return result


class Curve:
    def __init__(self, curve_type, start, end, center, radius, circle_direction):
        self.type = curve_type
        self.start_point = start
        self.end_point = end
        self.circle_center = center
        self.circle_radius = radius
        self.circle_direction = circle_direction


class MachiningProfile:
    def __init__(self, ref, curves, type, drill_type='straight_mill', drill_radius=8, holding_tabs_height=5, holding_tabs_width=8, target_depth = 18.3, depth_increment=3.1, stock_surface=0):
        self.ref = ref  # référence du edge_loop dans self.edge_loops.
        self.curves = curves  # renseigner les curves constituant le contour. (stockées dans self.edge_loops[ref])
        self.type = type  # type d'usinage : peut être 'profile_inside', 'profile_outside', 'pocket_inside', 'pocket_outside' ou 'engrave'
        self.drill_type = drill_type  # type de fraise : peut être 'straight_mill', '45_mill'.
        self.drill_radius = drill_radius  # rayon de la fraise.
        self.forward_feedrate = 0  # vitesse d'avance l'usinage en mm/mn -> tbd
        self.plunge_feedrate = 0  # vitesse de plongée de la fraise en mm/mn -> tbd
        self.holding_tabs_height = holding_tabs_height  # hauteur des holding tabs
        self.holding_tabs_width = holding_tabs_width  # largeur des holding tabs
        self.holding_tabs_number = 0  # nombre de holding tabs -> tbd
        self.target_depth = target_depth  # profondeur finale d'usinage
        self.depth_increment = depth_increment  # profondeur de passe
        self.stock_surface = stock_surface  # profondeur de base pour l'usinage (exemple : poche dans une poche : ne pas ré-usiner pour rien)
        # déterminer la vitesse d'avance et le plunge_feedrate
        if drill_radius > 4:
            self.forward_feedrate = 15000
            self.plunge_feedrate = 500
        else:
            self.forward_feedrate = 5000
            self.plunge_feedrate = 500
        # déterminer le nombre de holding tabs. La règle : compris entre 3 et 6, 1 tous les 800mm.
        # pour simplifier, on considerera que toutes les Curve sont des Line
        length = 0
        for c in self.curves:
            length += math.sqrt((c.start_point[0]-c.end_point[0])**2 + (c.start_point[1]-c.end_point[1])**2 + (c.start_point[2]-c.end_point[2])**2)
        self.holding_tabs_number = int(length/800)
        if self.holding_tabs_number > 6:
            self.holding_tabs_number = 6
        elif self.holding_tabs_number < 3:
            self.holding_tabs_number = 3
