from __future__ import print_function
# import matplotlib as matplt
# matplt.use('Agg')

"""
Some utility functions to display the registration results
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import model_pool.utils as utils
import model_pool.viewers_old as viewers
dpi=500
extension= '.png'


def checkerboard_2d(I0,I1,nrOfTiles=8):
    """
    Creates a checkerboard between two images
    
    :param I0: image 0, size XxYxZ 
    :param I1: image 1, size XxYxZ 
    :param nrOfTiles: number of desired tiles in each direction
    :return: returns tiled image
    """
    sz = I0.shape
    tileSize = int( np.array(sz).min()/nrOfTiles )
    nrOfTileXH = int( np.ceil(sz[0]/tileSize)/2+1 )
    nrOfTileYH = int( np.ceil(sz[1]/tileSize)/2+1 )
    cb_grid = np.kron([[1, 0] * nrOfTileYH, [0, 1] * nrOfTileYH] *nrOfTileXH, np.ones((tileSize, tileSize)))
    # now cut it to the same size
    cb_grid=cb_grid[0:sz[0],0:sz[1]]
    cb_image = I0*cb_grid + I1*(1-cb_grid)
    return cb_image


def _show_current_images_2d_map(iS, iT, iW, iSL,iTL, iWL,iter, vizImage, vizName, phiWarped, visual_param=None, i=0):

    sp_s = 331
    sp_t = 332
    sp_w = 333
    sp_c = 334
    sp_p = 335
    sp_v = 336
    sp_ls = 337
    sp_lt = 338
    sp_lw = 339

    font = {'size':10}


    plt.suptitle('Iteration = ' + str(iter))
    plt.setp(plt.gcf(), 'facecolor', 'white')
    plt.style.use('bmh')

    plt.subplot(sp_s).set_axis_off()
    plt.imshow(utils.t2np(iS),cmap='gray')
    plt.colorbar().ax.tick_params(labelsize=3)
    plt.title('source image',font)

    plt.subplot(sp_t).set_axis_off()
    plt.imshow(utils.t2np(iT),cmap='gray')
    plt.colorbar().ax.tick_params(labelsize=3)
    plt.title('target image',font)

    plt.subplot(sp_w).set_axis_off()
    plt.imshow(utils.t2np(iW),cmap='gray')
    plt.colorbar().ax.tick_params(labelsize=3)
    plt.title('warped image',font)

    plt.subplot(sp_c).set_axis_off()
    plt.imshow(checkerboard_2d(utils.t2np(iW), utils.t2np(iT)),cmap='gray')
    plt.colorbar().ax.tick_params(labelsize=3)
    plt.title('checkerboard',font)

    plt.subplot(sp_p).set_axis_off()
    plt.imshow(utils.t2np(iW),cmap='gray')

    plt.contour(utils.t2np(phiWarped[0, :, :]), np.linspace(-1, 1, 20), colors='r', linestyles='solid', linewidths=0.5)
    plt.contour(utils.t2np(phiWarped[1, :, :]), np.linspace(-1, 1, 20), colors='r', linestyles='solid', linewidths=0.5)

    plt.colorbar().ax.tick_params(labelsize=3)
    plt.title('warped image + grid',font)

    plt.subplot(sp_v).set_axis_off()
    plt.imshow(utils.t2np(vizImage), cmap='gray')
    plt.colorbar().ax.tick_params(labelsize=3)
    plt.title(vizName,font)

    plt.subplot(sp_ls).set_axis_off()
    plt.imshow(utils.t2np(iSL), cmap='gray')
    plt.title('Source Label',font)

    plt.subplot(sp_lt).set_axis_off()
    plt.imshow(utils.t2np(iTL), cmap='gray')
    plt.title('Target Label',font)

    plt.subplot(sp_lw).set_axis_off()
    plt.imshow(utils.t2np(iWL), cmap='gray')
    plt.title('Warped Label',font)

    if i==0 and visual_param['visualize']:
        plt.show()
    if visual_param['save_fig']:
        file_name = visual_param['pair_path'][i]
        join_p = lambda pth1,pth2: os.path.join(pth1, pth2)
        utils.make_dir(join_p(visual_param['save_fig_path_byname'], file_name))
        utils.make_dir(join_p(visual_param['save_fig_path_byiter'], visual_param['iter']))
        plt.savefig(join_p(join_p(visual_param['save_fig_path_byname'], file_name),visual_param['iter']+extension), dpi=dpi)
        plt.savefig(join_p(join_p(visual_param['save_fig_path_byiter'], visual_param['iter']), file_name+extension), dpi=dpi)
        plt.clf()


def _show_current_images_2d(iS, iT, iW,iSL, iTL,iWL, iter, vizImage, vizName, phiWarped, visual_param=None, i=0):

    _show_current_images_2d_map(iS, iT, iW,iSL, iTL,iWL, iter, vizImage, vizName, phiWarped, visual_param, i)


def _show_current_images_3d(iS, iT, iW, iter, vizImage, vizName, phiWarped, visual_param=None, i=0):

    if (phiWarped is not None) and (vizImage is not None):
        fig, ax = plt.subplots(5,3)
        phiw_a = 3
        vizi_a = 4
    elif (phiWarped is not None):
        fig, ax = plt.subplots(4,3)
        phiw_a = 3
    elif (vizImage is not None):
        fig, ax = plt.subplots(4,3)
        vizi_a = 3
    else:
        fig, ax = plt.subplots(3,3)

    plt.suptitle('Iteration = ' + str(iter))
    plt.setp(plt.gcf(), 'facecolor', 'white')
    plt.style.use('bmh')

    ivsx = viewers.ImageViewer3D_Sliced(ax[0][0], utils.t2np(iS), 0, 'source X', True)
    ivsy = viewers.ImageViewer3D_Sliced(ax[0][1], utils.t2np(iS), 1, 'source Y', True)
    ivsz = viewers.ImageViewer3D_Sliced(ax[0][2], utils.t2np(iS), 2, 'source Z', True)

    ivtx = viewers.ImageViewer3D_Sliced(ax[1][0], utils.t2np(iT), 0, 'target X', True)
    ivty = viewers.ImageViewer3D_Sliced(ax[1][1], utils.t2np(iT), 1, 'target Y', True)
    ivtz = viewers.ImageViewer3D_Sliced(ax[1][2], utils.t2np(iT), 2, 'target Z', True)

    ivwx = viewers.ImageViewer3D_Sliced(ax[2][0], utils.t2np(iW), 0, 'warped X', True)
    ivwy = viewers.ImageViewer3D_Sliced(ax[2][1], utils.t2np(iW), 1, 'warped Y', True)
    ivwz = viewers.ImageViewer3D_Sliced(ax[2][2], utils.t2np(iW), 2, 'warped Z', True)

    if phiWarped is not None:
        ivwxc = viewers.ImageViewer3D_Sliced_Contour(ax[phiw_a][0], utils.t2np(iW), utils.t2np(phiWarped), 0, 'warped X', True)
        ivwyc = viewers.ImageViewer3D_Sliced_Contour(ax[phiw_a][1], utils.t2np(iW), utils.t2np(phiWarped), 1, 'warped Y', True)
        ivwzc = viewers.ImageViewer3D_Sliced_Contour(ax[phiw_a][2], utils.t2np(iW), utils.t2np(phiWarped), 2, 'warped Z', True)

    if vizImage is not None:
        ivvxc = viewers.ImageViewer3D_Sliced(ax[vizi_a][0], utils.t2np(vizImage), 0, vizName + ' X', True)
        ivvyc = viewers.ImageViewer3D_Sliced(ax[vizi_a][1], utils.t2np(vizImage), 1, vizName + ' Y', True)
        ivvzc = viewers.ImageViewer3D_Sliced(ax[vizi_a][2], utils.t2np(vizImage), 2, vizName + ' Z', True)

    feh = viewers.FigureEventHandler(fig)

    feh.add_axes_event('button_press_event', ax[0][0], ivsx.on_mouse_press, ivsx.get_synchronize, ivsx.set_synchronize)
    feh.add_axes_event('button_press_event', ax[0][1], ivsy.on_mouse_press, ivsy.get_synchronize, ivsy.set_synchronize)
    feh.add_axes_event('button_press_event', ax[0][2], ivsz.on_mouse_press, ivsz.get_synchronize, ivsz.set_synchronize)

    feh.add_axes_event('button_press_event', ax[1][0], ivtx.on_mouse_press, ivtx.get_synchronize, ivtx.set_synchronize)
    feh.add_axes_event('button_press_event', ax[1][1], ivty.on_mouse_press, ivty.get_synchronize, ivty.set_synchronize)
    feh.add_axes_event('button_press_event', ax[1][2], ivtz.on_mouse_press, ivtz.get_synchronize, ivtz.set_synchronize)

    feh.add_axes_event('button_press_event', ax[2][0], ivwx.on_mouse_press, ivwx.get_synchronize, ivwx.set_synchronize)
    feh.add_axes_event('button_press_event', ax[2][1], ivwy.on_mouse_press, ivwy.get_synchronize, ivwy.set_synchronize)
    feh.add_axes_event('button_press_event', ax[2][2], ivwz.on_mouse_press, ivwz.get_synchronize, ivwz.set_synchronize)

    if phiWarped is not None:
        feh.add_axes_event('button_press_event', ax[phiw_a][0], ivwxc.on_mouse_press, ivwxc.get_synchronize, ivwxc.set_synchronize)
        feh.add_axes_event('button_press_event', ax[phiw_a][1], ivwyc.on_mouse_press, ivwyc.get_synchronize, ivwyc.set_synchronize)
        feh.add_axes_event('button_press_event', ax[phiw_a][2], ivwzc.on_mouse_press, ivwzc.get_synchronize, ivwzc.set_synchronize)

    if vizImage is not None:
        feh.add_axes_event('button_press_event', ax[vizi_a][0], ivvxc.on_mouse_press, ivvxc.get_synchronize,
                           ivvxc.set_synchronize)
        feh.add_axes_event('button_press_event', ax[vizi_a][1], ivvyc.on_mouse_press, ivvyc.get_synchronize,
                           ivvyc.set_synchronize)
        feh.add_axes_event('button_press_event', ax[vizi_a][2], ivvzc.on_mouse_press, ivvzc.get_synchronize,
                           ivvzc.set_synchronize)

    if (phiWarped is not None) and (vizImage is not None):
        feh.synchronize([ax[0][0], ax[1][0], ax[2][0], ax[phiw_a][0], ax[vizi_a][0]])
        feh.synchronize([ax[0][1], ax[1][1], ax[2][1], ax[phiw_a][1], ax[vizi_a][1]])
        feh.synchronize([ax[0][2], ax[1][2], ax[2][2], ax[phiw_a][2], ax[vizi_a][2]])
    elif (phiWarped is not None):
        feh.synchronize([ax[0][0], ax[1][0], ax[2][0], ax[phiw_a][0]])
        feh.synchronize([ax[0][1], ax[1][1], ax[2][1], ax[phiw_a][1]])
        feh.synchronize([ax[0][2], ax[1][2], ax[2][2], ax[phiw_a][2]])
    elif (vizImage is not None):
        feh.synchronize([ax[0][0], ax[1][0], ax[2][0], ax[vizi_a][0]])
        feh.synchronize([ax[0][1], ax[1][1], ax[2][1], ax[vizi_a][1]])
        feh.synchronize([ax[0][2], ax[1][2], ax[2][2], ax[vizi_a][2]])
    else:
        feh.synchronize([ax[0][0], ax[1][0], ax[2][0]])
        feh.synchronize([ax[0][1], ax[1][1], ax[2][1]])
        feh.synchronize([ax[0][2], ax[1][2], ax[2][2]])


    if i==0 and visual_param['visualize']:
        plt.show()
    if visual_param['save_fig']:
        file_name = visual_param['pair_path'][i]
        join_p = lambda pth1,pth2: os.path.join(pth1, pth2)
        utils.make_dir(join_p(visual_param['save_fig_path_byname'], file_name))
        utils.make_dir(join_p(visual_param['save_fig_path_byiter'], visual_param['iter']))

        plt.savefig(join_p(join_p(visual_param['save_fig_path_byname'], file_name),visual_param['iter']+extension), dpi=dpi)
        plt.savefig(join_p(join_p(visual_param['save_fig_path_byiter'], visual_param['iter']), file_name+extension), dpi=dpi)
        plt.clf()

def save_current_images(iter, iS, iT, iW,iSL, iTL, iWL, vizImages=None, vizName=None, phiWarped=None, visual_param=None):
    """
    Visualizes the current images during registration
    
    :param iter: iteration number 
    :param iS: source image BxCxXxYxZ (only displays B=0,C=0)
    :param iT: target image BxCxXxYxZ (only displays B=0,C=0)
    :param iW: warped image BxCxXxYxZ (only displays B=0,C=0)
    :param vizImage: custom visualization image XxYxZ
    :param vizName: name for this image
    :param phiWarped: warped map BxdimxXxYxZ (only displays B=0)
    """
    """
    Show current 2D registration results in relation to the source and target images
    :param iter: iteration number
    :param iS: source image
    :param iT: target image
    :param iW: current warped image
    :return: no return arguments
    """

    dim = iS.ndimension()-2

    if visual_param['save_fig'] == True:
        save_fig_num = min(visual_param['save_fig_num'], len(visual_param['pair_path']))
        print("num {} of pair would be saved in {}".format(save_fig_num,visual_param['save_fig_path']))
    else:
        save_fig_num = 1


    for i in range(save_fig_num):
        iSF = iS[i,0,...]
        iTF = iT[i,0,...]
        iWF = iW[i,0,...]
        iSLF = iSL[i, 0, ...]
        iTLF = iTL[i, 0, ...]
        iWLF = iWL[i, 0, ...]
        vizImage = vizImages[i,...]

        if phiWarped is not None:
            pwF = phiWarped[i,...]
        else:
            pwF = None

        if dim==2:
            _show_current_images_2d(iSF, iTF, iWF,iSLF,iTLF,iWLF, iter, vizImage, vizName, pwF, visual_param, i)
        elif dim==3:
            _show_current_images_3d(iSF, iTF, iWF, iter, vizImage, vizName, pwF, visual_param, i)
        else:
            raise ValueError( 'Debug output only supported in 1D and 3D at the moment')

        '''
        plt.show(block=False)
        plt.draw_all(force=True)
    
        print( 'Click mouse to continue press any key to exit' )
        wasKeyPressed = plt.waitforbuttonpress()
        if wasKeyPressed:
            sys.exit()
        '''