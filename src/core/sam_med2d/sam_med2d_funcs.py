import cv2
import numpy as np

import torch
from matplotlib import pyplot as plt

from src.core.sam_med2d.segment_anything.predictor_sammed import SammedPredictor


def show_mask(mask, ax, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30/255, 144/255, 255/255, 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)

def show_points(coords, labels, ax, marker_size=375):
    pos_points = coords[labels==1]
    neg_points = coords[labels==0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='black', linewidth=1.25)

def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', facecolor=(0,0,0,0), lw=2))


def point_segmentation(model,input_points,input_labels,image_array):
    predictor = SammedPredictor(model)
    image = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
    predictor.set_image(image)
    # 使用SAM_predictor返回覆盖、置信度及logits
    masks, scores, logits = predictor.predict(
        point_coords=np.array(input_points),
        point_labels=np.array(input_labels),
        multimask_output=True,
    )
    print(masks.shape)
    plt.figure(figsize=(10, 10))
    plt.imshow(image)
    show_mask(masks, plt.gca())
    show_points(np.array(input_points), np.array(input_labels), plt.gca())
    plt.axis('off')
    plt.show()
    # save_image_path = "."+image_path.split(".")[1] + "_segmentation" + ".png"
    # plt.savefig(save_image_path)
    #-----------------------------------------
    temp = 0
    for mask in masks:
        if isinstance(mask, torch.Tensor):
            temp += mask.cpu().numpy()
        else:
            temp += mask
    return temp



def single_box_segmentation(model, box_points, image_array):
    predictor = SammedPredictor(model)
    image = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
    predictor.set_image(image)
    input_box = np.array([box_points[0],box_points[1],box_points[2],box_points[3]])
    masks, _, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=input_box,
        multimask_output=True,
    )
    print(masks.shape)
    plt.figure(figsize=(10, 10))
    plt.imshow(image)
    show_mask(masks[0], plt.gca())
    show_box(input_box, plt.gca())
    plt.axis('off')
    plt.show()

    return masks[0]


def multiple_box_segmentation(model, box_points, image_array, args):
    predictor = SammedPredictor(model)
    image = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
    predictor.set_image(image)
    # 多个标签框
    input_boxes = torch.tensor(np.array(box_points), device=predictor.device)
    transformed_boxes = predictor.apply_boxes_torch(input_boxes, image.shape[:2], (args.image_size, args.image_size))
    masks, _, _ = predictor.predict_torch(
        point_coords=None,
        point_labels=None,
        boxes=transformed_boxes,
        multimask_output=True,
    )
    # print(transformed_boxes.shape)
    print(masks.shape)
    #
    plt.figure(figsize=(10, 10))
    plt.imshow(image)
    for mask in masks:
        show_mask(mask.cpu().numpy(), plt.gca(), random_color=True)
    for box in input_boxes:
        show_box(box.cpu().numpy(), plt.gca())
    plt.axis('off')
    plt.show()
    # # save_image_path = "." + image_path.split(".")[1] + "_segmentation" + ".png"
    # # plt.savefig(save_image_path)
    # dims = masks.shape
    temp = 0
    for mask in masks:
        temp = temp + mask.cpu().numpy()

    print(temp.shape)
    return temp[0]
