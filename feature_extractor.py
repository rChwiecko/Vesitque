import torch
import numpy as np
import cv2
import torch.nn.functional as F
from sklearn.metrics.pairwise import cosine_similarity

class FeatureExtractor:
    def __init__(self):
        self.model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet50', pretrained=True)
        self.model.eval()

    def extract_features(self, image):
        """Extract features with color histogram augmentation"""
        try:
            # ResNet features
            image_tensor = torch.from_numpy(np.array(image))
            image_tensor = image_tensor.permute(2, 0, 1).float() / 255.0
            image_tensor = F.interpolate(image_tensor.unsqueeze(0), size=(224, 224))
            
            with torch.no_grad():
                features = self.model(image_tensor)
                
            # Add color histogram features
            img_np = np.array(image)
            hist_features = []
            for channel in range(3):  # RGB channels
                hist = cv2.calcHist([img_np], [channel], None, [256], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                hist_features.extend(hist)
                
            # Combine ResNet and color features
            combined_features = np.concatenate([
                features.squeeze().numpy(),
                np.array(hist_features) * 0.3  # Weight for color features
            ])
            
            return combined_features
        except Exception as e:
            return None

    def calculate_similarity(self, features1, features2):
        """Calculate cosine similarity between two feature sets"""
        min_length = min(len(features1), len(features2))
        return cosine_similarity(
            features1[:min_length].reshape(1, -1),
            features2[:min_length].reshape(1, -1)
        )[0][0]
    
    