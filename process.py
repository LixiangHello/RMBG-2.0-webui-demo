import os
import torch
import streamlit as st
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation


@st.cache_resource
def load_model(model_id_or_path="briaai/RMBG-2.0", precision=0, device="cpu"):
    model = AutoModelForImageSegmentation.from_pretrained(
        model_id_or_path, trust_remote_code=True
    )
    torch.set_float32_matmul_precision(["high", "highest"][precision])
    model.to(device)
    _ = model.eval()

    # Data settings
    image_size = (1024, 1024)
    transform_image = transforms.Compose(
        [
            transforms.Resize(image_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    return model, transform_image


def process(image: Image.Image) -> Image.Image:
    if "RMBG-2.0" not in os.listdir("."):
        os.system(
            "modelscope download --model AI-ModelScope/RMBG-2.0 --local_dir RMBG-2.0 --exclude *.onnx *.bin"
        )
    device = 'cpu' if torch.cuda.is_available() else 'cuda'
    precision = 0
    model, transform = load_model("RMBG-2.0", precision=precision, device=device)
    image = image.convert("RGB").copy()
    input_images = transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        preds = model(input_images)[-1].sigmoid().cpu()
        pred = preds[0].squeeze()
    pred_pil = transforms.ToPILImage()(pred)
    mask = pred_pil.resize(image.size)
    image.putalpha(mask)

    return mask, image
