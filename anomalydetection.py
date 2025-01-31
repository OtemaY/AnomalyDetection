# -*- coding: utf-8 -*-
"""AnomalyDetection.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1aty4Nh2DadGwLN7Butl81_mIFAK00jqc

## Anomaly Detection

This notebook is used for anomaly detection using the Anomalib library and MVTec Dataset. The model used is the Efficient Ad model whose backbone is of EfficientNet.
"""

!pip install anomalib[full] --extra-index-url https://pypi.org/simple

# Uninstall the conflicting packages
!pip uninstall -y anomalib ollama

# Reinstall anomalib without the faulty dependencies
!pip install anomalib[full] --extra-index-url https://pypi.org/simple --no-deps

# Manually install missing dependencies except 'ollama'
!pip install torch torchvision torchaudio pytorch-lightning
!pip install opencv-python-headless matplotlib scikit-learn

!pip install matplotlib==3.7.1 # Install matplotlib 3.7.1, previous version may not work correctly
# import matplotlib
# matplotlib.use('agg')  # or 'Agg' depending on your system

# Import required packages
from anomalib.data import MVTec
from anomalib.engine import Engine
from anomalib.models import EfficientAd

"""# Training"""

# 2. Create a dataset
# MVTec is a popular dataset for anomaly detection
datamodule = MVTec(
    root="./datasets/MVTec",  # Path to download/store the dataset
    # category="bottle",  # MVTec category to use
    category="metal_nut",
    train_batch_size=1,  # Number of images per training batch
    eval_batch_size=32,  # Number of images per validation/test batch
    num_workers=8,  # Number of parallel processes for data loading
)

# 3. Initialize the model
# EfficientAd is a good default choice for beginners
model = EfficientAd()

# 4. Create the training engine
engine = Engine(max_epochs=5)  # Train for 5 epochs

# 5. Train the model
engine.fit(datamodule=datamodule, model=model)

"""# Inference"""

#  Perform inference on a trained model using the Anomalib Python API.


# 1. Import required modules
from pathlib import Path

from anomalib.data import PredictDataset


# 3. Prepare test data
# You can use a single image or a folder of images
dataset = PredictDataset(
    path=Path("./datasets/MVTec/metal_nut/test"),
    image_size=(256, 256),
)

# 4. Get predictions
predictions = engine.predict(
    model=model,
    dataset=dataset,
    ckpt_path="/content/results/EfficientAd/MVTec/metal_nut/latest/weights/lightning/model.ckpt",
)

if predictions is not None:
    for i, prediction in enumerate(predictions[:5]):  # Print first 5 predictions
        print(f"Prediction {i+1}: {prediction.keys()}")

# 5. Access the results
if predictions is not None:
    for prediction in predictions:
        # Access the image, anomaly map, label, and score
        image = prediction["image"]

        # Check if 'anomaly_map' key exists before accessing it
        anomaly_map = prediction.get("anomaly_maps", None)

        pred_label = prediction["pred_labels"]
        pred_score = prediction["pred_scores"]

        # Print details, handling potential missing 'anomaly_map'
        print(f"Predicted Label: {pred_label}, Score: {pred_score}")
        if anomaly_map is not None:
            print("Anomaly map shape:", anomaly_map.shape) # Optional: print anomaly map shape
        else:
            print("Anomaly map not found in prediction.")

"""# Evaluation"""

ground_truths = []  # Store actual labels

dataloader = datamodule.test_dataloader()  # Assuming test_dataloader is available

for batch in dataloader:
    labels = batch["label"].numpy()  # Adjust based on your dataset structure
    ground_truths.extend(labels)

from sklearn.metrics import accuracy_score, classification_report

# Convert predictions to a NumPy array
import numpy as np
predicted_labels = np.array([pred["pred_labels"][0] for pred in predictions])  # Extract first label from each prediction

# Compute Accuracy
accuracy = accuracy_score(ground_truths, predicted_labels)
print(f"Accuracy: {accuracy:.4f}")

# Detailed classification report
print(classification_report(ground_truths, predicted_labels))

from sklearn.metrics import roc_auc_score, precision_recall_fscore_support

# Extract anomaly scores
predicted_scores = np.array([pred["pred_scores"][0] for pred in predictions])  # Extract first score per sample

# Compute AUC-ROC
auc_score = roc_auc_score(ground_truths, predicted_scores)
print(f"AUC-ROC Score: {auc_score:.4f}")

# Compute Precision, Recall, and F1-score (thresholding at 0.5)
threshold = 0.5  # Adjust if needed
binary_preds = (predicted_scores > threshold).astype(int)
precision, recall, f1, _ = precision_recall_fscore_support(ground_truths, binary_preds, average="binary")
print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1-Score: {f1:.4f}")

import torch
from sklearn.metrics import jaccard_score

def calculate_iou(mask_pred, mask_gt):
    mask_pred = torch.tensor(mask_pred).flatten()
    mask_gt = torch.tensor(mask_gt).flatten()
    intersection = (mask_pred * mask_gt).sum()
    union = (mask_pred + mask_gt).sum()
    return (intersection / (union + 1e-8)).item()

# Compute IoU for first 10 predictions
iou_scores = [calculate_iou(pred["pred_masks"], gt) for pred, gt in zip(predictions[:10], ground_truths[:10])]
mean_iou = sum(iou_scores) / len(iou_scores)
print(f"Mean IoU: {mean_iou:.4f}")

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(2, 5, figsize=(15, 6))

for i in range(5):
    # Extract image and remove batch dimension
    image = predictions[i]["image"]
    image = np.squeeze(image)  # Remove batch dimension (1, 3, 256, 256) → (3, 256, 256)

    # If image has 3 channels, transpose to (256, 256, 3) for imshow
    if image.shape[0] == 3:
        image = np.transpose(image, (1, 2, 0))  # Convert from (C, H, W) to (H, W, C)

    # Convert anomaly map
    anomaly_map = predictions[i]["anomaly_maps"]
    anomaly_map = np.squeeze(anomaly_map)  # Remove unnecessary dimensions

    # Display original image
    axes[0, i].imshow(image)  # No need for cmap if image is RGB
    axes[0, i].set_title("Original Image")

    # Display anomaly map
    axes[1, i].imshow(anomaly_map, cmap="jet")
    axes[1, i].set_title("Anomaly Map")

plt.show()

