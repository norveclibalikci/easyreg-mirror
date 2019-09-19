from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



from model_pool.modules import *
from functions.bilinear import *
from torch.utils.checkpoint import checkpoint
from model_pool.utils import sigmoid_decay
from model_pool.losses import NCCLoss


#
# class AffineNet(nn.Module):
#     """
#     here we need two affine net,
#     1. do the affine by training single forward network
#     # in this case if we want to do the affine
#     we need to  warp the image then made it as a new input
#
#     2. do affine by training a multi_step network
#     in this case, it is like svf , we would feed raw image once, and the
#     network would warp the phi, the advantage of this method is we don't need
#     to warp the image for several time as interpolation would introduce unstability
#     """
#     def __init__(self, img_sz=None, opt=None):
#         super(AffineNet, self).__init__()
#         self.img_sz = img_sz if len(img_sz)<4 else img_sz[2:]
#         self.dim = len(self.img_sz)
#         self.affine_gen = Affine_unet_im()
#         self.affine_cons= AffineConstrain()
#         self.id_map= gen_identity_map(self.img_sz)
#         self.bilinear = Bilinear(zero_boundary=False)
#         self.epoch = -1
#
#     def set_cur_epoch(self, cur_epoch):
#         self.epoch = cur_epoch
#
#     def gen_affine_map(self,Ab):
#         Ab = Ab.view( Ab.shape[0],4,3 ) # 3d: (batch,3)
#         id_map = self.id_map.view(self.dim, -1)
#         affine_map = None
#         if self.dim == 3:
#             affine_map = torch.matmul( Ab[:,:3,:], id_map)
#             affine_map = Ab[:,3,:].contiguous().view(-1,3,1) + affine_map
#             affine_map= affine_map.view([Ab.shape[0]] + list(self.id_map.shape))
#         return affine_map
#
#     def scale_reg_loss(self,param=None,sched='l2'):
#         constr_map =self.affine_cons(param, sched=sched)
#         reg = constr_map.sum()
#         return reg
#
#
#     def forward(self,moving,target=None):
#         affine_param = self.affine_gen(moving,target)
#         affine_map = self.gen_affine_map(affine_param)
#         #affine_map=affine_map.repeat(input.shape[0],1,1,1,1)
#         output = self.bilinear(moving,affine_map)
#         return output, affine_map, affine_param
#
#     def get_extra_to_plot(self):
#         return None, None
#
#
#
#
# class AffineNetCycle(nn.Module):   # is not implemented, need to be done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#     """
#     here we need two affine net,
#     1. do the affine by training single forward network
#     # in this case if we want to do the affine
#     we need to  warp the image then made it as a new input
#
#     2. do affine by training a multi_step network
#     in this case, it is like svf , we would feed raw image once, and the
#     network would warp the phi, the advantage of this method is we don't need
#     to warp the image for several time as interpolation would introduce unstability
#     """
#     def __init__(self, img_sz=None, opt=None):
#         super(AffineNetCycle, self).__init__()
#         self.img_sz = img_sz
#         self.dim = len(img_sz)
#
#         self.step = opt['tsk_set']['reg']['affine_net'][('affine_net_iter',7,'the number of the step used in multi-step affine')]
#         print("Num of step in multi-step affine network is {}".format(self.step))
#         self.using_complex_net = True
#         self.affine_gen = Affine_unet_im() if self.using_complex_net else Affine_unet()
#         self.affine_cons= AffineConstrain()
#         self.id_map= gen_identity_map(self.img_sz)
#         self.zero_boundary = True
#         self.bilinear =Bilinear(self.zero_boundary)
#         self.epoch = -1
#
#
#     def set_cur_epoch(self, cur_epoch):
#         self.epoch = cur_epoch
#
#
#     def gen_affine_map(self,Ab):
#         Ab = Ab.view( Ab.shape[0],4,3 ) # 3d: (batch,3)
#         id_map = self.id_map.view(self.dim, -1)
#         affine_map = None
#         if self.dim == 3:
#             affine_map = torch.matmul( Ab[:,:3,:], id_map)
#             affine_map = Ab[:,3,:].contiguous().view(-1,3,1) + affine_map
#             affine_map= affine_map.view([Ab.shape[0]] + list(self.id_map.shape))
#         return affine_map
#
#     def update_affine_param(self, cur_af, last_af): # A2(A1*x+b1) + b2 = A2A1*x + A2*b1+b2
#         cur_af = cur_af.view(cur_af.shape[0], 4, 3)
#         last_af = last_af.view(last_af.shape[0],4,3)
#         updated_af = Variable(torch.zeros_like(cur_af.data)).cuda()
#         if self.dim==3:
#             updated_af[:,:3,:] = torch.matmul(cur_af[:,:3,:],last_af[:,:3,:])
#             updated_af[:,3,:] = cur_af[:,3,:] + torch.squeeze(torch.matmul(cur_af[:,:3,:], torch.transpose(last_af[:,3:,:],1,2)),2)
#         updated_af = updated_af.contiguous().view(cur_af.shape[0],-1)
#         return updated_af
#
#     def get_inverse_affine_param(self,affine_param):
#         """A2(A1*x+b1) +b2= A2A1*x + A2*b1+b2 = x    A2= A1^-1, b2 = - A2^b1"""
#
#         affine_param = affine_param.view(affine_param.shape[0], 4, 3)
#         inverse_param = torch.zeros_like(affine_param.data).cuda()
#         for n in range(affine_param.shape[0]):
#             tm_inv = torch.inverse(affine_param[n, :3,:])
#             inverse_param[n, :3, :] = tm_inv
#             inverse_param[n, :, 3] = - torch.matmul(tm_inv, affine_param[n, 3, :])
#             inverse_param = inverse_param.contiguous().view(affine_param.shape[0], -1)
#         return inverse_param
#
#     def scale_reg_loss(self,param=None,sched='l2'):
#         constr_map =self.affine_cons(param, sched=sched)
#         reg = constr_map.sum()
#         return reg
#
#     def forward(self,moving=None,target=None):
#         output = None
#         moving_cp = moving
#         affine_param_last = None
#         bilinear = [Bilinear(self.zero_boundary) for i in range(self.step)]
#
#         for i in range(self.step):
#             affine_param = self.affine_gen(moving,target)
#             if i >0:
#                 affine_param = self.update_affine_param(affine_param,affine_param_last)
#             affine_param_last = affine_param
#             affine_map = self.gen_affine_map(affine_param)
#             output = bilinear[i](moving_cp,affine_map)
#             moving = output
#
#         return output, affine_map, affine_param
#
#     def get_extra_to_plot(self):
#         return None, None



class AffineNetSym(nn.Module):   # is not implemented, need to be done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    """
    A multi-step symmetirc -force affine network

    at each step. the network would update the affine parameter
    the advantage is we don't need to warp the image for several time (only interpolated by the latest affine transform) as the interpolation would diffuse the image

    """
    def __init__(self, img_sz=None, opt=None):
        super(AffineNetSym, self).__init__()
        self.img_sz = img_sz
        """ the image sz  in numpy coord"""
        self.dim = len(img_sz)
        """ the dim of image"""
        self.step = opt['tsk_set']['reg']['affine_net'][('affine_net_iter',1,'num of step')]
        """ the num of step"""
        self.step_record = self.step
        """ a copy on step"""
        self.using_complex_net = opt['tsk_set']['reg']['affine_net'][('using_complex_net',True,'use complex version of affine net')]
        """if true, use complex version of affine net"""
        self.acc_multi_step_loss = opt['tsk_set']['reg']['affine_net'][('acc_multi_step_loss',False,'accumulate loss from each step')]
        """accumulate loss from each step"""
        self.epoch_activate_multi_step = opt['tsk_set']['reg']['affine_net'][('epoch_activate_multi_step',-1,'epoch to activate multi-step affine')]
        """epoch to activate multi-step affine"""
        self.reset_lr_for_multi_step = opt['tsk_set']['reg']['affine_net'][('reset_lr_for_multi_step',False,'if True, reset learning rate when multi-step begins')]
        """if True, reset learning rate when multi-step begins"""
        self.lr_for_multi_step = opt['tsk_set']['reg']['affine_net'][('lr_for_multi_step',opt['tsk_set']['optim']['lr']/2,'if reset_lr_for_multi_step, reset learning rate into # when multi-step begins')]
        """if reset_lr_for_multi_step, reset learning rate into # when multi-step begins"""
        self.epoch_activate_sym = opt['tsk_set']['reg']['affine_net'][('epoch_activate_sym',-1,'epoch to activate symmetric forward')]
        """epoch to activate symmetric forward"""
        self.epoch_activate_sym_loss = opt['tsk_set']['reg']['affine_net'][('epoch_activate_sym_loss',-1,'the epoch to take symmetric loss into backward , only if epoch_activate_sym and epoch_activate_sym_loss')]
        """ the epoch to take symmetric loss into backward , only if epoch_activate_sym and epoch_activate_sym_loss"""
        self.epoch_activate_extern_loss = opt['tsk_set']['reg']['affine_net'][('epoch_activate_extern_loss',-1,'epoch to activate lncc loss')]
        """epoch to activate lncc loss"""
        self.affine_gen = Affine_unet_im() if self.using_complex_net else Affine_unet()
        """ the affine network output the affine parameter"""
        self.affine_cons= AffineConstrain()
        """ the func return regularization loss on affine parameter"""
        self.id_map= gen_identity_map(self.img_sz)
        """ the identity map"""
        self.gen_identity_ap()
        """ generate identity affine parameter"""

        ################### init variable  #####################3
        self.iter_count = 0
        """the num of iteration"""
        self.using_multi_step = True
        """ set multi-step on"""
        self.zero_boundary = True
        """ zero boundary is used for interpolated images"""
        self.epoch = -1
        """ the current epoch"""
        self.reset_lr = False
        """ reset learning rate"""
        self.ncc = NCCLoss()
        """ normalized cross correlation loss"""
        self.extern_loss = None
        """ external loss used during training"""
        self.compute_loss = True
        """ compute loss, set true during affine netowrk training"""




    def set_loss_fn(self, loss_fn):
        """ set loss function"""
        self.extern_loss = loss_fn


    def set_cur_epoch(self, cur_epoch):
        """ set current epoch"""
        self.epoch = cur_epoch

    def check_if_update_lr(self):
        """
        check if the learning rate need to be updated
        during affine training, both epoch_activate_multi_step and reset_lr_for_multi_step are activated
        the learning rate would be set to reset_lr_for_multi_step
        """
        if self.epoch == self.epoch_activate_multi_step and self.reset_lr_for_multi_step:
            lr = self.lr_for_multi_step
            self.reset_lr_for_multi_step = False
            print("the lr is change into {} due to the activation of the multi-step".format(lr))
            return True, lr
        else:
            return False, None

    def gen_affine_map(self,Ab):
        """
        generate the affine transformation map with regard to affine parameter
        :param Ab: affine parameter
        :return: affine transformation map
        """
        Ab = Ab.view( Ab.shape[0],4,3) # 3d: (batch,3)
        id_map = self.id_map.view(self.dim, -1)
        affine_map = None
        if self.dim == 3:
            affine_map = torch.matmul( Ab[:,:3,:], id_map)
            affine_map = Ab[:,3,:].contiguous().view(-1,3,1) + affine_map
            affine_map= affine_map.view([Ab.shape[0]] + list(self.id_map.shape))
        return affine_map


    def update_affine_param(self, cur_af, last_af): # A2(A1*x+b1) + b2 = A2A1*x + A2*b1+b2
        """
        update the current affine parameter A2 based on last affine parameter A1
         A2(A1*x+b1) + b2 = A2A1*x + A2*b1+b2, results in the composed affine parameter A3=(A2A1, A2*b1+b2)
        :param cur_af: current affine parameter
        :param last_af: last affine parameter
        :return: composed affine parameter A3
        """
        cur_af = cur_af.view(cur_af.shape[0], 4, 3)
        last_af = last_af.view(last_af.shape[0],4,3)
        updated_af = Variable(torch.zeros_like(cur_af.data)).cuda()
        if self.dim==3:
            updated_af[:,:3,:] = torch.matmul(cur_af[:,:3,:],last_af[:,:3,:])
            updated_af[:,3,:] = cur_af[:,3,:] + torch.squeeze(torch.matmul(cur_af[:,:3,:], torch.transpose(last_af[:,3:,:],1,2)),2)
        updated_af = updated_af.contiguous().view(cur_af.shape[0],-1)
        return updated_af

    def gen_identity_ap(self):
        """
        get the idenityt affine parameter
        :return:
        """
        self.affine_identity = Variable(torch.zeros(12)).cuda()
        self.affine_identity[0] = 1.
        self.affine_identity[4] = 1.
        self.affine_identity[8] = 1.

    def sym_reg_loss(self, bias_factor=1.):
        """
        compute the symmetry loss
        s-t transform (a,b), t-s transform (c,d), then assume transform from t-s-t
        a(cy+d)+b = acy +ad+b =y
        then ac = I, ad+b = 0
        the l2 loss is taken to constrain the above two terms
        ||ac-I||_2^2 +  bias_factor *||ad+b||_2^2
        :param bias_factor: the factor on the translation term
        :return: the symmetry loss (average on batch)
        """

        ap_st, ap_ts  = self.affine_param

        ap_st = ap_st.view(-1, 4, 3)
        ap_ts = ap_ts.view(-1, 4, 3)
        ac = None
        ad_b = None
        ################################################ check if ad_b is right
        if self.dim == 3:
            ac = torch.matmul(ap_st[:, :3, :], ap_ts[:, :3, :])
            ad_b = ap_st[:, 3, :] + torch.squeeze(
                torch.matmul(ap_st[:, :3, :], torch.transpose(ap_ts[:, 3:, :], 1, 2)), 2)
        identity_matrix = self.affine_identity.view(4,3)[:3,:3]

        linear_transfer_part = torch.sum((ac-identity_matrix)**2)
        translation_part = bias_factor * (torch.sum(ad_b**2))

        sym_reg_loss = linear_transfer_part + translation_part
        if self.iter_count %10 ==0:
            print("linear_transfer_part:{}, translation_part:{}, bias_factor:{}".format(linear_transfer_part.cpu().data.numpy(), translation_part.cpu().data.numpy(),bias_factor))
        return sym_reg_loss/ap_st.shape[0]


    def sim_loss(self,loss_fn,warped,target):
        """
        compute the similarity loss
        :param loss_fn: the loss function
        :param output: the warped image
        :param target: the target image
        :return: the similarity loss average on batch
        """
        loss_fn = self.ncc if self.epoch < self.epoch_activate_extern_loss else loss_fn
        sim_loss = loss_fn(warped,target)
        return sim_loss / warped.shape[0]


    def scale_sym_reg_loss(self,sched='l2'):
        affine_param = self.affine_param
        if sched=='l2':
            loss = torch.sum((affine_param[0]-self.affine_identity)**2 + (affine_param[1]-self.affine_identity)**2 )\
                   / (affine_param[0].shape[0])
            return loss
        elif sched=='det':
            loss = 0.
            for j in range(2):
                for i in range(affine_param[j].shape[0]):
                    affine_matrix = affine_param[j][i,:9].contiguous().view(3,3)
                    loss += (torch.det(affine_matrix) -1.)**2
            return loss / (affine_param[0].shape[0])

    def scale_multi_step_reg_loss(self,sched='l2'):
        affine_param = self.affine_param
        if sched == 'l2':
            return torch.sum((self.affine_identity - affine_param) ** 2)\
                   / (affine_param.shape[0])
        elif sched == 'det':
            mean_det = 0.
            for i in range(affine_param.shape[0]):
                affine_matrix = affine_param[i, :9].contiguous().view(3, 3)
                mean_det += torch.det(affine_matrix)
            return mean_det / affine_param.shape[0]

    def get_factor_reg_scale(self):
        epoch_for_reg = self.epoch if self.epoch < self.epoch_activate_multi_step else self.epoch - self.epoch_activate_multi_step
        factor_scale = 10 if self.epoch < self.epoch_activate_multi_step else 1e-3
        static_epoch = 10 if self.epoch < self.epoch_activate_multi_step else 10
        min_threshold = 1e-3
        decay_factor = 3
        factor_scale = float(
            max(sigmoid_decay(epoch_for_reg, static=static_epoch, k=decay_factor) * factor_scale, min_threshold))
        return factor_scale



    def compute_overall_loss(self, loss_fn, output, target):
        sim_loss = self.sim_loss(loss_fn.get_loss,output, target)
        sym_on = self.epoch>= self.epoch_activate_sym
        self.affine_param = (self.affine_param[:self.n_batch], self.affine_param[self.n_batch:]) if sym_on else self.affine_param
        sym_reg_loss = self.sym_reg_loss(bias_factor=1.) if  sym_on else 0.
        scale_reg_loss = self.scale_sym_reg_loss(sched = 'l2') if sym_on else self.scale_multi_step_reg_loss(sched='l2')
        factor_scale = self.get_factor_reg_scale()
        factor_sym =10. if self.epoch>= self.epoch_activate_sym_loss else 0.
        sim_factor = 1.
        loss = sim_factor*sim_loss + factor_sym * sym_reg_loss + factor_scale * scale_reg_loss
        if self.iter_count%10==0:
            if self.epoch >= self.epoch_activate_sym:
                print('sim_loss:{}, factor_sym: {}, sym_reg_loss: {}, factor_scale {}, scale_reg_loss: {}'.format(
                    sim_loss.item(),factor_sym,sym_reg_loss.item(),factor_scale,scale_reg_loss.item())
                )
            else:
                print('sim_loss:{}, factor_scale {}, scale_reg_loss: {}'.format(
                    sim_loss.item(), factor_scale, scale_reg_loss.item())
                )
        return loss


    def get_loss(self):
        return self.loss



    def forward(self,moving, target):
        self.iter_count += 1
        if self.epoch_activate_multi_step>0:
            if self.epoch >= self.epoch_activate_multi_step:
                if self.step_record != self.step:
                    print(" the multi step in affine network activated, multi step num: {}".format(self.step_record))
                self.step = self.step_record
            else:
                self.step = 1
        if self.epoch < self.epoch_activate_sym:
            return self.multi_step_forward(moving, target, self.compute_loss)
        else:
            return self.sym_multi_step_forward(moving, target)





    def multi_step_forward(self,moving,target, compute_loss=True):

        output = None
        moving_cp = moving
        affine_param = None
        affine_param_last = None
        affine_map = None
        bilinear = [Bilinear(self.zero_boundary) for i in range(self.step)]
        self.loss = 0.
        for i in range(self.step):
            #affine_param = self.affine_gen(moving, target)
            if i == 0:
                affine_param = self.affine_gen(moving, target)
            else:
                affine_param = checkpoint(self.affine_gen, moving, target)
            if i > 0:
                affine_param = self.update_affine_param(affine_param, affine_param_last)
            affine_param_last = affine_param
            affine_map = self.gen_affine_map(affine_param)
            output = bilinear[i](moving_cp, affine_map)
            moving = output
            self.affine_param = affine_param
            if compute_loss and (i==self.step-1 or self.acc_multi_step_loss):
                self.loss +=self.compute_overall_loss(self.extern_loss,output, target)
        if compute_loss and self.acc_multi_step_loss:
            self.loss = self.loss / self.step
        return output, affine_map, affine_param


    def sym_multi_step_forward(self, moving, target):
        self.n_batch = moving.shape[0]
        moving_sym = torch.cat((moving, target), 0)
        target_sym = torch.cat((target, moving), 0)
        output, affine_map, affine_param = self.multi_step_forward(moving_sym, target_sym)
        return output[:self.n_batch],affine_map[:self.n_batch], affine_param[:self.n_batch]
    def get_extra_to_plot(self):
        return None, None




class MomentumNet(nn.Module):
    def __init__(self, low_res_factor,opt):
        super(MomentumNet,self).__init__()
        self.low_res_factor = low_res_factor
        using_complex_net = opt['using_complex_net']

        if using_complex_net:
            self.mom_gen = MomentumGen_resid(low_res_factor,bn=False)
            print("=================    resid version momentum network is used==============")
        else:
            self.mom_gen = MomentumGen_im(low_res_factor, bn=False)
            print("=================    im version momentum network is used==============")

    def forward(self,input):
        return self.mom_gen(input)


