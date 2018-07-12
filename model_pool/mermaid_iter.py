import numpy as np
import torch
import os
from collections import OrderedDict
from torch.autograd import Variable
from .base_model import BaseModel
from .reg_net_expr import *
from . import networks
from .losses import Loss
from .metrics import get_multi_metric
from data_pre.partition import Partition
#from model_pool.utils import weights_init
from model_pool.utils import *
#from model_pool.mermaid_net import MermaidNet
import torch.nn as nn
import matplotlib.pyplot as plt
from model_pool.nn_interpolation import get_nn_interpolation
import SimpleITK as sitk

import mermaid.pyreg.simple_interface as SI
import mermaid.pyreg.fileio as FIO
class RegNet(BaseModel):


    def name(self):
        return 'reg-unet'

    def initialize(self,opt):
        BaseModel.initialize(self,opt)
        which_epoch = opt['tsk_set']['which_epoch']
        self.print_val_detail = opt['tsk_set']['print_val_detail']
        self.spacing = np.asarray(opt['tsk_set']['extra_info']['spacing'])
        input_img_sz = [int(self.img_sz[i]*self.input_resize_factor[i]) for i in range(len(self.img_sz))]
        network_name =opt['tsk_set']['network_name']
        self.single_mod = True
        if network_name =='affine':
            self.affine_on = True
            self.svf_on = False
        elif network_name =='svf':
            self.affine_on = True
            self.svf_on = True
        self.si = SI.RegisterImagePair()
        self.im_io = FIO.ImageIO()
        self.criticUpdates = opt['tsk_set']['criticUpdates']
        self.loss_fn = Loss(opt)
        self.opt_optim = opt['tsk_set']['optim']
        self.step_count =0.
        print('---------- Networks initialized -------------')
        networks.print_network(self.network)





    def set_input(self, data, is_train=True):
        data[0]['image'] =(data[0]['image'].cuda()+1)/2
        data[0]['label'] =data[0]['label'].cuda()
        moving, target, l_moving,l_target = get_pair(data[0])
        input = data[0]['image']
        self.moving = moving
        self.target = target
        self.l_moving = l_moving
        self.l_target = l_target
        self.input = input
        self.fname_list = list(data[1])



    def affine_optimization(self):
        self.si.set_light_analysis_on(True)
        extra_info={}
        extra_info['pair_name'] = self.fname_list[0]
        extra_info['batch_id'] = self.fname_list[0]
        self.si.register_images(self.moving, self.target, self.spacing,extra_info=extra_info,LSource=self.l_moving,LTarget=self.l_target,
                                model_name='affine',
                                map_low_res_factor=0.5,
                                nr_of_iterations=100,
                                visualize_step=None,
                                optimizer_name='sgd',
                                use_multi_scale=True,
                                rel_ftol=0,
                                similarity_measure_type='ncc',
                                similarity_measure_sigma=0.5,
                                json_config_out_filename='cur_settings_affine.json',
                                params ='cur_settings_affine.json')
        self.output = self.si.get_warped_image()
        self.phi = self.si.opt.optimizer.ssOpt.get_map()
        self.disp = self.si.opt.optimizer.ssOpt.model.Ab

        return self.output, self.phi, self.disp


    def svf_optimization(self):
        self.si.set_light_analysis_on(True)
        extra_info = {}
        extra_info['pair_name'] = self.fname_list[0]
        extra_info['batch_id'] = self.fname_list[0]
        self.si.opt.optimizer.ssOpt.set_source_label(self.l_moving)
        LSource_warped = self.si.get_warped_label()

        self.si.register_images(self.output, self.target, self.spacing, extra_info=extra_info, LSource=LSource_warped,
                                LTarget=self.l_target,
                                model_name='svf_vector_momentum_map',
                                map_low_res_factor=0.5,
                                nr_of_iterations=100,
                                visualize_step=None,
                                optimizer_name='lbfgs_ls',
                                use_multi_scale=True,
                                rel_ftol=0,
                                similarity_measure_type='ncc',
                                similarity_measure_sigma=0.5,
                                json_config_out_filename='cur_settings_svf.json',
                                params='cur_settings_svf.json')
        self.disp = self.output
        self.output = self.si.get_warped_image()
        self.phi = self.si.opt.optimizer.ssOpt.get_map() + self.phi  ############# check if it is true


    def forward(self,input=None):
        if self.affine_on:
            return self.affine_optimization()
        elif self.svf_on:
            self.affine_optimization()
            return self.svf_optimization()






    # get image paths
    def get_image_paths(self):
        return self.fname_list


    def get_warped_img_map(self,img, phi):
        bilinear = Bilinear()
        warped_img_map = bilinear(img, phi)

        return warped_img_map


    def get_warped_label_map(self,label_map, phi, sched='nn'):
        if sched == 'nn':
            warped_label_map = get_nn_interpolation(label_map, phi)
            # check if here should be add assert
            assert abs(torch.sum(
                warped_label_map.detach() - warped_label_map.detach().round())) < 0.1, "nn interpolation is not precise"
        else:
            raise ValueError(" the label warpping method is not implemented")
        return warped_label_map

    def cal_val_errors(self):
        self.cal_test_errors()

    def cal_test_errors(self):
        self.get_evaluation()

    def get_evaluation(self):
        if self.single_mod:
            self.output, self.phi, self.disp= self.forward()
            self.warped_label_map = self.get_warped_label_map(self.l_moving,self.phi)
            warped_label_map_np= self.warped_label_map.detach().cpu().numpy()
            self.l_target_np= self.l_target.detach().cpu().numpy()

            self.val_res_dic = get_multi_metric(warped_label_map_np, self.l_target_np,rm_bg=False)
        else:
            step = 8
            print("Attention!!, the multi-step mode is on, {} step would be performed".format(step))
            for i in range(step):
                self.output, self.phi, self.disp = self.forward()
                self.input = torch.cat((self.output,self.target),1)
                self.warped_label_map = self.get_warped_label_map(self.l_moving, self.phi)
                self.l_moving = self.warped_label_map

            warped_label_map_np  =self.warped_label_map.detach().cpu().numpy()
            self.l_target_np = self.l_target.detach().cpu().numpy()
            self.val_res_dic = get_multi_metric(warped_label_map_np, self.l_target_np, rm_bg=False)
        # if not self.print_val_detail:
        #     print('batch_label_avg_res:{}'.format(self.val_res_dic['batch_label_avg_res']))
        # else:
        #     print('batch_avg_res{}'.format(self.val_res_dic['batch_avg_res']))
        #     print('batch_label_avg_res:{}'.format(self.val_res_dic['batch_label_avg_res']))


    def get_val_res(self):
        return np.mean(self.val_res_dic['batch_avg_res']['dice'][0,1:]), self.val_res_dic['batch_avg_res']['dice']

    def get_test_res(self):
        return self.get_val_res()




    def save(self, label):
        self.save_network(self.network, 'unet', label, self.gpu_ids)



    def save_fig_3D(self,phase):
        saving_folder_path = os.path.join(self.record_path, '3D')
        make_dir(saving_folder_path)
        for i in range(self.moving.size(0)):
            appendix = self.fname_list[i] + "_"+phase+ "_iter_" + str(self.iter_count)
            saving_file_path = saving_folder_path + '/' + appendix + "_moving.nii.gz"
            output = sitk.GetImageFromArray(self.moving[i, 0, ...])
            output.SetSpacing(self.spacing)
            sitk.WriteImage(output, saving_file_path)
            saving_file_path = saving_folder_path + '/' + appendix + "_target.nii.gz"
            output = sitk.GetImageFromArray(self.target[i, 0, ...])
            output.SetSpacing(self.spacing)
            sitk.WriteImage(output, saving_file_path)
            saving_file_path = saving_folder_path + '/' + appendix + "_reproduce.nii.gz"
            output = sitk.GetImageFromArray(self.output[i, 0, ...])
            output.SetSpacing(self.spacing)
            sitk.WriteImage(output, saving_file_path)

    def save_fig_2D(self,phase):
        saving_folder_path = os.path.join(self.record_path, '2D')
        make_dir(saving_folder_path)

        for i in range(self.moving.size(0)):
            appendix = self.fname_list[i] + "_"+phase+"_iter_" + str(self.iter_count)
            save_image_with_scale(saving_folder_path + '/' + appendix + "_moving.tif", self.moving[i, 0, ...])
            save_image_with_scale(saving_folder_path + '/' + appendix + "_target.tif", self.target[i, 0, ...])
            save_image_with_scale(saving_folder_path + '/' + appendix + "_reproduce.tif", self.output[i, 0, ...])

    def save_fig(self,phase,standard_record=False,saving_gt=True):
        from model_pool.visualize_registration_results import  show_current_images
        visual_param={}
        visual_param['visualize'] = False
        visual_param['save_fig'] = True
        visual_param['save_fig_path'] = self.record_path
        visual_param['save_fig_path_byname'] = os.path.join(self.record_path, 'byname')
        visual_param['save_fig_path_byiter'] = os.path.join(self.record_path, 'byiter')
        visual_param['save_fig_num'] = 5
        visual_param['pair_path'] = self.fname_list
        visual_param['iter'] = phase+"_iter_" + str(self.iter_count)
        disp=None
        extra_title = 'disp'
        if self.disp is not None and len(self.disp.shape)>2 and not self.debug_svf_on:
            disp = ((self.disp[:,...]**2).sum(1))**0.5


        if self.debug_svf_on:
            disp = self.disp[:,0,...]
            extra_title='affine'
        show_current_images(self.iter_count,  self.moving, self.target,self.output, self.l_moving,self.l_target,self.warped_label_map,
                            disp, extra_title, self.phi, visual_param=visual_param)


    def set_val(self):
        self.network.train(False)
        self.is_train = False
        torch.set_grad_enabled(False)

    def set_debug(self):
        self.network.train(False)
        self.is_train = False
        torch.set_grad_enabled(False)

    def set_test(self):
        self.network.train(False)
        self.is_train = False
        torch.set_grad_enabled(False)


