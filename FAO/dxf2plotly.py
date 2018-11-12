# coding: utf8

import plotly.graph_objs as go
import plotly
import stepReader


step = stepReader.StepFile()
#step.read('/Users/baulieu/scripts/FAO/test/test_files/test_BSF_V1_fond.stp')
step.read('/Users/baulieu/scripts/FAO/test/test_files/BSF_V1_bas.stp')
step.get_ref_plane()
step.process_edge_loops_step_1()
step.process_edge_loops_step_2()


if step.success:
    data = []

    loops_display=[25]

    for k in step.edge_loops.keys():
        #print(k)
        edge_loop = step.edge_loops[k]
        coordinates = []
        for curve in edge_loop:
            if curve.type == 'Line':
                coordinates.append(curve.start_point)
                coordinates.append(curve.end_point)
                #coordinates.append(curve.end_point)
                #coordinates.append(curve.start_point)

                datadico = dict()

                datadico['x'] = [c[0] for c in coordinates]
                datadico['y'] = [c[1] for c in coordinates]
                datadico['z'] = [c[2] for c in coordinates]

                datadico['type'] = 'scatter3d'
                datadico['mode'] = 'lines'

                datadico['line'] = dict(color='black', width=4)
            else:
                datadico = dict()

        data.append(datadico)

    layout = dict()

    camera = dict(eye=dict(x=1.7, y=1.7, z=0.5))

    scene = dict(
        xaxis = dict(
            nticks=4, range = [-100,100],),
        yaxis = dict(
            nticks=4, range = [-50,100],),
        zaxis = dict(
            nticks=4, range = [-100,100],)
    )
    scene['xaxis'] = dict(title='')
    scene['yaxis'] = dict(title='')
    scene['zaxis'] = dict(title='')
    scene['camera'] = camera

    layout['title'] = 'STEP file reader'
    layout['showlegend'] = False
    layout['scene'] = scene


    fig = dict(data=data, layout=layout)

    plotly.offline.plot(fig)
else:
    print("tu t'es bien fait bolosser")
