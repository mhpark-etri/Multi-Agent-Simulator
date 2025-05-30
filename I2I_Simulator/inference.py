import os
import argparse
from PIL import Image
import torch
from torchvision import transforms
from torchmetrics.detection.mean_ap import MeanAveragePrecision
from models import CycleGAN_Turbo, load_ground_truth, save_image_with_boxes
import glob
from ultralytics import YOLO
from torch.cuda.amp import autocast

# set parameters
PROMPT = "driving in a real-world environment"
DIRECTION = "a2b"
I2I_MODEL_PATH = "./checkpoints/i2i_checkpoint.pkl"
DET_MODEL_PATH = "yolov8n.pt"
DEVICE = "cuda"
no_bbox = True

INPUT_DIR = "./sample"
OUTPUT_DIR = "./output"
WIDTH = 1024
HEIGHT = 512


# initialize the model
i2i_model = CycleGAN_Turbo(pretrained_path=I2I_MODEL_PATH).to(DEVICE)
i2i_model.eval()
i2i_model.unet.enable_xformers_memory_efficient_attention()

det_model = YOLO(DET_MODEL_PATH)
map_calculator = MeanAveragePrecision(iou_thresholds=[0.5])

input_images = sorted(glob.glob(INPUT_DIR + '/*.png'))
os.makedirs(OUTPUT_DIR, exist_ok=True)

transform_pipeline = transforms.Compose([
    transforms.Resize((HEIGHT, WIDTH)),
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5])
])

for i in input_images:
    input_image = Image.open(i).convert('RGB')
    # translate the image
    with torch.no_grad():
        x_t = transform_pipeline(input_image).unsqueeze(0).to(DEVICE)
        with autocast():
        	output = i2i_model(x_t, direction=DIRECTION, caption=PROMPT)

    output_pil = transforms.ToPILImage()(output[0].cpu() * 0.5 + 0.5)
    output_pil = output_pil.resize((WIDTH, HEIGHT), Image.LANCZOS)

    # save the output image
    bname = os.path.basename(i)
    # output_pil.save(os.path.join(OUTPUT_DIR, bname))
    
    # Detection
    #ground_truth_path = os.path.join(INPUT_DIR, bname.replace('.png', '.txt'))
    detection_results = det_model(output_pil)
    pred_boxes = detection_results[0].boxes
    #ground_truth = load_ground_truth(ground_truth_path, WIDTH, HEIGHT)
    
    save_image_with_boxes(
        output_pil,
        boxes=pred_boxes.xyxy.cpu().numpy(),
        labels=pred_boxes.cls.cpu().numpy(),
        scores=pred_boxes.conf.cpu().numpy(),
        output_path=os.path.join(OUTPUT_DIR, bname.replace('.png', '_with_boxes.png'))
    )
    
    if not no_bbox:
        preds = [{"boxes": torch.tensor(pred_boxes.xyxy).cpu(), "scores": torch.tensor(pred_boxes.conf).cpu(), "labels": torch.tensor(pred_boxes.cls, dtype=torch.int64).cpu()}]
        targets = ground_truth

        # Compute IoU and mAP
        map_score = map_calculator(preds, targets)
        
        print(f"Image Name: {bname}, mAP@0.5: {map_score['map_50']}")
        
    

