#coding: utf-8

import parsing
import os

# parsing.parse_one_file('/Users/baulieu/scripts/FAO/test/test_files/BSF_V1_bas.stp')
# parsing.parse_one_file('/Users/baulieu/scripts/FAO/test/test_files/TeamDesk_pied_35.stp')
# parsing.parse_one_file('/Users/baulieu/scripts/FAO/test/test_files/test_BSF_V1_fond.stp')

path = '/Users/baulieu/scripts/FAO/test/test_files/pieces_STP'
parsing.parse_all_files(path)

import stepReader

# step = stepReader.StepFile()
# step.read('/Users/baulieu/scripts/FAO/test/test_files/BSF_V1_bas.stp')
# # step.read('/Users/baulieu/scripts/FAO/test/test_files/test_BSF_V1_fond.stp')
#
# if not step.success:
#     print("echec de l'ouverture")
# else:
#     step.get_ref_plane()
#     step.process_edge_loops_step_1()
#     step.process_edge_loops_step_2()
#     step.process_edge_loops_step_3()
#     for key in step.debug_edge_loop_ref.keys():
#         step.debug_edge_loop_ref[key]['oriented_edges'] = []
#         for e_c in step.debug_edge_loop_ref[key]['edge_curves']:
#             for elem_key in step.elements.keys():
#                 if step.elements[elem_key]['type'] == "ORIENTED_EDGE" and e_c == step.elements[elem_key]['properties'][3]:
#                     step.debug_edge_loop_ref[key]['oriented_edges'].append(elem_key)
    # for key in step.debug_edge_loop_ref.keys():
    #     print('-----------------------------')
    #     print(key)
    #     for i in range(0, len(step.debug_edge_loop_ref[key]['edge_curves'])):
    #         if step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][3]]['type'] == 'CIRCLE':
    #             print(step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][4])


    # key = 37
    # print(key)
    # for i in range(0, len(step.debug_edge_loop_ref[key]['edge_curves'])):
    #     if step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][3]]['type'] == 'CIRCLE':
    #         print("      arc " + str(i))
    #         print('start / end :', end='     ')
    #         l1 = step.elements[step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][1]]['properties'][1]]['properties'][1:]
    #         l2 = step.elements[step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][2]]['properties'][1]]['properties'][1:]
    #         print([l1[j] - l2[j] for j in range (0, len(l1))])
    #         # print(step.elements[step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][1]]['properties'][1]]['properties'][1:] - step.elements[step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][2]]['properties'][1]]['properties'][1:])
    #         # print(step.elements[step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][2]]['properties'][1]]['properties'][1:])
    #         print('oriented edges values :', end='      ')
    #         print(step.elements[step.debug_edge_loop_ref[key]['oriented_edges'][2*i]]['properties'][4], end='     ')
    #         print(step.elements[step.debug_edge_loop_ref[key]['oriented_edges'][2*i+1]]['properties'][4])
    #         print('edge curves values :', end='      ')
    #         print(step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][4])
    #         print('axis direction value:', end='      ')
    #         print(step.elements[step.elements[step.elements[step.elements[step.debug_edge_loop_ref[key]['edge_curves'][i]]['properties'][3]]['properties'][1]]['properties'][2]]['properties'][1:])
    #         print('')

    # for key in step.bottom_edge_loops.keys():
    #     print(step.debug_edge_loop_ref)
