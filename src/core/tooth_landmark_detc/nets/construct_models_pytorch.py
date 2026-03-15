# -*- coding: utf-8 -*-
"""
Created on 02/06/2022

@author: XLP
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np


class Downsample_Conv2d_2(nn.Module):
    def __init__(self, in_size, out_size, is_batchnorm, is_drop):
        super(Downsample_Conv2d_2, self).__init__()
        self.is_drop = is_drop

        if is_batchnorm:
            self.conv1 = nn.Sequential(
                nn.Conv2d(in_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.Conv2d(out_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.BatchNorm2d(out_size),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
            )
        else:
            self.conv1 = nn.Sequential(
                nn.Conv2d(in_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.Conv2d(out_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
            )
        if is_drop:
            self.dropout1 = nn.Dropout(p=0.6)

    def forward(self, inputs):
        outputs = self.conv1(inputs)
        if self.is_drop:
            outputs = self.dropout1(outputs)
        return outputs


class Downsample_Conv2d_3(nn.Module):
    def __init__(self, in_size, out_size, is_batchnorm, is_drop):
        super(Downsample_Conv2d_3, self).__init__()
        self.is_drop = is_drop

        if is_batchnorm:
            self.conv1 = nn.Sequential(
                nn.Conv2d(in_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.Conv2d(out_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.Conv2d(out_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.BatchNorm2d(out_size),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
            )
        else:
            self.conv1 = nn.Sequential(
                nn.Conv2d(in_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.Conv2d(out_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.Conv2d(out_size, out_size, kernel_size=3, stride=1, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
            )
        if is_drop:
            self.dropout1 = nn.Dropout(p=0.6)

    def forward(self, inputs):
        outputs = self.conv1(inputs)
        if self.is_drop:
            outputs = self.dropout1(outputs)
        return outputs


class Upsample_Block(nn.Module):
    def __init__(self, in_size, up_dim):
        super(Upsample_Block, self).__init__()
        self.conv1 = nn.Conv2d(in_size, up_dim, kernel_size=3, stride=1, padding=1)
        self.upsample = nn.UpsamplingBilinear2d(scale_factor=2)

    def forward(self, inputs1, inputs2):
        outputs1 = self.conv1(inputs1)
        outputs2 = torch.cat([outputs1, inputs2], 1)
        outputs2 = self.upsample(outputs2)

        return outputs2


class ChannelAttention_Block(nn.Module):
    def __init__(self, out_size, ratio):
        super(ChannelAttention_Block, self).__init__()
        self.out_size = out_size
        self.weight1 = nn.Parameter(torch.Tensor(out_size, int(out_size / ratio)), requires_grad=True)
        self.bias1 = nn.Parameter(torch.Tensor(int(out_size / ratio)), requires_grad=True)
        self.weight2 = nn.Parameter(torch.Tensor(int(out_size / ratio), out_size), requires_grad=True)
        self.bias2 = nn.Parameter(torch.Tensor(out_size), requires_grad=True)
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1. / math.sqrt(self.weight1.size(1))
        self.weight1.data.uniform_(-stdv, stdv)
        self.bias1.data.uniform_(-stdv, stdv)
        stdv = 1. / math.sqrt(self.weight2.size(1))
        self.weight2.data.uniform_(-stdv, stdv)
        self.bias2.data.uniform_(-stdv, stdv)

    def forward(self, inputs):
        x = torch.mean(inputs, 3)
        x = torch.mean(x, 2)
        x = torch.matmul(x, self.weight1) + self.bias1
        x = torch.matmul(x, self.weight2) + self.bias2
        x = x.reshape(-1, self.out_size, 1, 1)
        outputs = inputs * x
        return outputs


class Unet_Al_Seg(nn.Module):
    def __init__(self, feature_scale=1, up_dim=32, n_classes=2, in_channels=1, is_batchnorm=True, is_drop=True):
        super(Unet_Al_Seg, self).__init__()
        self.is_drop = is_drop

        filters = [64, 128, 256, 512, 512]
        filters = [int(x / feature_scale) for x in filters]
        # ============= downsample =====================================
        """ conv1 """
        self.conv1 = Downsample_Conv2d_2(in_channels, filters[0], is_batchnorm, is_drop)
        """ conv2 """
        self.conv2 = Downsample_Conv2d_2(filters[0], filters[1], is_batchnorm, is_drop)
        """ conv3 """
        self.conv3 = Downsample_Conv2d_3(filters[1], filters[2], is_batchnorm, is_drop)
        """ conv4 """
        self.conv4 = Downsample_Conv2d_3(filters[2], filters[3], is_batchnorm, is_drop)
        """ conv5 """
        self.conv5 = Downsample_Conv2d_3(filters[3], filters[4], is_batchnorm, is_drop)
        # ============= downsample =====================================
        self.conv5_up = nn.Sequential(
            nn.Conv2d(filters[4], up_dim, kernel_size=3, stride=1, padding=1),
            nn.UpsamplingBilinear2d(scale_factor=2),
        )
        self.conv4_up = Upsample_Block(filters[3], up_dim)
        self.conv3_up = Upsample_Block(filters[2], up_dim)
        self.conv2_up = Upsample_Block(filters[1], up_dim)
        self.conv1_up = Upsample_Block(filters[0], up_dim)
        # ============classify==================================
        self.channel_attenion1 = ChannelAttention_Block(out_size=up_dim * 5, ratio=2)
        if is_drop:
            self.dropout1_class = nn.Dropout(p=0.5)
        self.conv1_class = nn.Conv2d(up_dim * 5, up_dim * 5 // 2, kernel_size=3, stride=1, padding=1)
        if is_drop:
            self.dropout2_class = nn.Dropout(p=0.5)
        self.conv2_class = nn.Conv2d(up_dim * 5 // 2, n_classes, kernel_size=3, stride=1, padding=1)

    def forward(self, inputs):
        conv1 = self.conv1(inputs)
        conv2 = self.conv2(conv1)
        conv3 = self.conv3(conv2)
        conv4 = self.conv4(conv3)
        conv5 = self.conv5(conv4)
        conv5_up = self.conv5_up(conv5)
        conv4_up = self.conv4_up(conv4, conv5_up)
        conv3_up = self.conv3_up(conv3, conv4_up)
        conv2_up = self.conv2_up(conv2, conv3_up)
        conv1_up = self.conv1_up(conv1, conv2_up)
        output = self.channel_attenion1(conv1_up)
        if self.is_drop:
            output = self.dropout1_class(output)
        output = self.conv1_class(output)
        if self.is_drop:
            output = self.dropout2_class(output)
        output = self.conv2_class(output)
        output = F.softmax(output, 1)
        return output


class BinaryDiceLoss(nn.Module):
    def __init__(self):
        super(BinaryDiceLoss, self).__init__()

    def forward(self, pred, gt):
        N = gt.size()[0]
        smooth = 1.0e-5
        inputs = pred[:, 1, :, :]
        targets = gt[:, 1, :, :]
        inse = inputs * targets
        inse = inse.sum(1).sum(1)
        l = inputs.sum(1).sum(1)
        r = targets.sum(1).sum(1)
        dice = (2.0 * inse + smooth) / (l + r + smooth)
        loss = 1 - dice.sum() / N

        return loss


class BinaryDiceLoss_MultiObj(nn.Module):
    def __init__(self):
        super(BinaryDiceLoss_MultiObj, self).__init__()

    def forward(self, pred_list, gt_list):
        Diceloss_all = 0
        Num = len(pred_list)
        for ii in range(Num):
            pred = pred_list[ii]
            gt = gt_list[ii]

            N = gt.size()[0]
            smooth = 1.0e-5
            inputs = pred[:, 1, :, :]
            targets = gt[:, 1, :, :]
            inse = inputs * targets
            inse = inse.sum(1).sum(1)
            l = inputs.sum(1).sum(1)
            r = targets.sum(1).sum(1)
            dice = (2.0 * inse + smooth) / (l + r + smooth)
            loss = 1 - dice.sum() / N

            Diceloss_all = Diceloss_all + loss

        return Diceloss_all



class CrossEntropyLoss_MultiObj(nn.Module):
    def __init__(self):
        super(CrossEntropyLoss_MultiObj, self).__init__()

    def forward(self, pred_list, gt_list, wt_list):
        CEloss_all = 0
        Num = len(pred_list)
        smooth = 1.0e-5
        for ii in range(Num):
            pred = pred_list[ii]
            gt = gt_list[ii]
            wt = wt_list[ii]
            N = gt.size()[0]
            cost = gt * torch.log(pred + smooth)
            cost = cost.sum(1)*wt
            cost = -cost.sum(1).sum(1).sum()/N
            CEloss_all = CEloss_all + cost
        return CEloss_all


class Unet_ToothSeg_LandmarkDet_Prior(nn.Module):
    def __init__(self, feature_scale=1, up_dim=32, n_classes_th=2, n_classes_ld = 3, in_channels=1, is_batchnorm=True, is_drop=True):
        super(Unet_ToothSeg_LandmarkDet_Prior, self).__init__()
        self.is_drop = is_drop
        filters = [64, 128, 256, 512, 512]
        filters = [int(x / feature_scale) for x in filters]
        # ============= downsample =====================================
        """ conv1 """
        self.conv1 = Downsample_Conv2d_2(in_channels, filters[0], is_batchnorm, is_drop)
        """ conv2 """
        self.conv2 = Downsample_Conv2d_2(filters[0], filters[1], is_batchnorm, is_drop)
        """ conv3 """
        self.conv3 = Downsample_Conv2d_3(filters[1], filters[2], is_batchnorm, is_drop)
        """ conv4 """
        self.conv4 = Downsample_Conv2d_3(filters[2], filters[3], is_batchnorm, is_drop)
        """ conv5 """
        self.conv5 = Downsample_Conv2d_3(filters[3], filters[4], is_batchnorm, is_drop)
        # ============= downsample =====================================
        self.conv5_up = nn.Sequential(
            nn.Conv2d(filters[4], up_dim, kernel_size=3, stride=1, padding=1),
            nn.UpsamplingBilinear2d(scale_factor=2),
        )
        self.conv4_up = Upsample_Block(filters[3], up_dim)
        self.conv3_up = Upsample_Block(filters[2], up_dim)
        self.conv2_up = Upsample_Block(filters[1], up_dim)
        self.conv1_up = Upsample_Block(filters[0], up_dim)
        # ============classify landmark==================================
        self.channel_attenion_ld = ChannelAttention_Block(out_size=up_dim * 5, ratio=2)
        if is_drop:
            self.dropout1_class_ld = nn.Dropout(p=0.5)
        self.conv1_class_ld = nn.Conv2d(up_dim * 5 + 1, up_dim * 5 // 2, kernel_size=3, stride=1, padding=1)
        if is_drop:
            self.dropout2_class_ld = nn.Dropout(p=0.5)
        self.conv2_class_ld = nn.Conv2d(up_dim * 5 // 2, n_classes_ld, kernel_size=3, stride=1, padding=1)
        # ============classify Tooth==================================
        self.channel_attenion_th = ChannelAttention_Block(out_size=up_dim * 5, ratio=2)
        if is_drop:
            self.dropout1_class_th = nn.Dropout(p=0.5)
        self.conv1_class_th = nn.Conv2d(up_dim * 5 + 1, up_dim * 5 // 2, kernel_size=3, stride=1, padding=1)
        if is_drop:
            self.dropout2_class_th = nn.Dropout(p=0.5)
        self.conv2_class_th = nn.Conv2d(up_dim * 5 // 2, n_classes_th, kernel_size=3, stride=1, padding=1)

    def forward(self, inputs, dist_al):
        # =========Downsample====================
        conv1 = self.conv1(inputs)
        conv2 = self.conv2(conv1)
        conv3 = self.conv3(conv2)
        conv4 = self.conv4(conv3)
        conv5 = self.conv5(conv4)
        # =========Upsample=======================
        conv5_up = self.conv5_up(conv5)
        conv4_up = self.conv4_up(conv4, conv5_up)
        conv3_up = self.conv3_up(conv3, conv4_up)
        conv2_up = self.conv2_up(conv2, conv3_up)
        conv1_up = self.conv1_up(conv1, conv2_up)
        # =========Segment landmark========================
        output_ld = self.channel_attenion_ld(conv1_up)
        output_ld = torch.cat([output_ld, dist_al], 1)
        if self.is_drop:
            output_ld = self.dropout1_class_ld(output_ld)
        output_ld = self.conv1_class_ld(output_ld)
        if self.is_drop:
            output_ld = self.dropout2_class_ld(output_ld)
        output_ld = self.conv2_class_ld(output_ld)
        output_ld = F.softmax(output_ld, 1)
        # =========Segment tooth========================
        output_th = self.channel_attenion_th(conv1_up)
        output_th = torch.cat([output_th, dist_al], 1)
        if self.is_drop:
            output_th = self.dropout1_class_th(output_th)
        output_th = self.conv1_class_th(output_th)
        if self.is_drop:
            output_th = self.dropout2_class_th(output_th)
        output_th = self.conv2_class_th(output_th)
        output_th = F.softmax(output_th, 1)

        return output_th, output_ld



import torchvision.models as models
backbone = 'resnet50'

class DecoderBlock(nn.Module):
    """
    U-Net中的解码模块

    采用每个模块一个stride为1的3*3卷积加一个上采样层的形式

    上采样层可使用'deconv'、'pixelshuffle', 其中pixelshuffle必须要mid_channels=4*out_channles

    定稿采用pixelshuffle

    BN_enable控制是否存在BN，定稿设置为True
    """
    def __init__(self, in_channels, mid_channels, out_channels, upsample_mode='pixelshuffle', BN_enable=True):
        super().__init__()
        self.in_channels = in_channels
        self.mid_channels = mid_channels
        self.out_channels = out_channels
        self.upsample_mode = upsample_mode
        self.BN_enable = BN_enable
    
        self.conv = nn.Conv2d(in_channels=in_channels, out_channels=mid_channels, kernel_size=3, stride=1, padding=1, bias=False)

        if self.BN_enable:
            self.norm1 = nn.BatchNorm2d(mid_channels)
        self.relu1 = nn.ReLU(inplace=False)
        self.relu2 = nn.ReLU(inplace=False)

        if self.upsample_mode=='deconv':
            self.upsample = nn.ConvTranspose2d(in_channels=mid_channels, out_channels = out_channels,

                                                kernel_size=3, stride=2, padding=1, output_padding=1, bias=False)
        elif self.upsample_mode=='pixelshuffle':
            self.upsample = nn.PixelShuffle(upscale_factor=2)
        if self.BN_enable:
            self.norm2 = nn.BatchNorm2d(out_channels)

    def forward(self,x):
        x=self.conv(x)
        if self.BN_enable:
            x=self.norm1(x)
        x=self.relu1(x)
        x=self.upsample(x)
        if self.BN_enable:
            x=self.norm2(x)
        x=self.relu2(x)
        return x

class Resnet_Unet(nn.Module):
    """
    定稿使用resnet50作为backbone

    BN_enable控制是否存在BN，定稿设置为True
    """
    def __init__(self, BN_enable=True, resnet_pretrain=False, in_channels= 1, out_channels= 1):
        super().__init__()
        self.BN_enable = BN_enable
        self.in_channels = in_channels
        self.out_channels = out_channels
        # encoder部分
        # ====================================================
        # 使用resnet34或50预定义模型，由于单通道入，因此自定义第一个conv层，同时去掉原fc层
        # 剩余网络各部分依次继承
        # 经过测试encoder取三层效果比四层更佳，因此降采样、升采样各取4次
        if backbone=='resnet34':
            resnet = models.resnet34(pretrained=resnet_pretrain)
            filters=[64,64,128,256,512]
        elif backbone=='resnet50':
            resnet = models.resnet50(pretrained=resnet_pretrain)
            filters=[64,256,512,1024,2048]
        # ======================================================
        self.firstconv = nn.Conv2d(in_channels=self.in_channels, out_channels=64, kernel_size=7, stride=2, padding=3, bias=False)
        self.firstbn = resnet.bn1
        self.firstrelu = resnet.relu
        self.firstmaxpool = resnet.maxpool
        self.encoder1 = resnet.layer1
        self.encoder2 = resnet.layer2
        self.encoder3 = resnet.layer3

        # decoder部分
        self.center = DecoderBlock(in_channels=filters[3], mid_channels=filters[3]*4, out_channels=filters[3], BN_enable=self.BN_enable)
        self.decoder1 = DecoderBlock(in_channels=filters[3]+filters[2], mid_channels=filters[2]*4, out_channels=filters[2], BN_enable=self.BN_enable)
        self.decoder2 = DecoderBlock(in_channels=filters[2]+filters[1], mid_channels=filters[1]*4, out_channels=filters[1], BN_enable=self.BN_enable)
        self.decoder3 = DecoderBlock(in_channels=filters[1]+filters[0], mid_channels=filters[0]*4, out_channels=filters[0], BN_enable=self.BN_enable)
        if self.BN_enable:
            self.final = nn.Sequential(
                nn.Conv2d(in_channels=filters[0],out_channels=32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32), 
                nn.ReLU(inplace=False),
                nn.Conv2d(in_channels=32, out_channels=self.out_channels, kernel_size=1),
                nn.Sigmoid()
                )
        else:
            self.final = nn.Sequential(
                nn.Conv2d(in_channels=filters[0],out_channels=32, kernel_size=3, padding=1),
                nn.ReLU(inplace=False),
                nn.Conv2d(in_channels=32, out_channels=self.out_channels, kernel_size=1),
                nn.Sigmoid()
                )

    def forward(self,x):
        x = self.firstconv(x)
        x = self.firstbn(x)
        x = self.firstrelu(x)
        x_ = self.firstmaxpool(x)

        e1 = self.encoder1(x_)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)

        center = self.center(e3)

        d2 = self.decoder1(torch.cat([center,e2],dim=1))
        d3 = self.decoder2(torch.cat([d2,e1], dim=1))
        d4 = self.decoder3(torch.cat([d3,x], dim=1))

        return self.final(d4)


# model=Downsample_Conv2d_3(in_size=3, out_size=64, is_batchnorm=True, is_drop=True)
# model=Upsample_Block(in_size=128, up_dim=32)
# model= ChannelAttention_Block(out_size=32, ratio=2)
# model = Unet_Al_Seg(feature_scale=1, up_dim = 32, n_classes=2, in_channels = 1, is_batchnorm=True, is_drop=True)
# print(summary(model, input_size=[(1,320,320)], batch_size=2, device="cpu"))
# loss_dice = BinaryDiceLoss()
# a = np.random.randn(5, 2, 10,10)>0
# b = np.random.randn(5, 2, 10,10)>0
# inputs = torch.tensor(a, dtype=torch.float32)
# targets = torch.tensor(1- a, dtype=torch.float32)
# loss = loss_dice(inputs, targets)
# print(loss.cpu().detach().item())

# model = Resnet_Unet(BN_enable=True, resnet_pretrain=False, in_channels= 1, out_channels= 2)
# print(summary(model, input_size=[(1,320,320)], batch_size=2, device="cpu"))
