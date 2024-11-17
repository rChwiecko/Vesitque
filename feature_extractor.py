import torch
import numpy as np
import cv2
import torch.nn.functional as F
from sklearn.metrics.pairwise import cosine_similarity
from torchvision.models import efficientnet_b0
from torchvision.transforms import functional as TF
from torchvision import transforms

class FeatureExtractor:
    def __init__(self):
        # Use EfficientNet-B0 for faster inference
        self.model = efficientnet_b0(pretrained=True)
        self.model.eval()
        
        # Pre-define transform pipeline
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                              std=[0.229, 0.224, 0.225])
        ])
        
        self.similarity_threshold = 0.84
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.model.to(self.device)

    def extract_features(self, image, is_full_outfit=False):
        """Enhanced feature extraction with multiple perspectives"""
        try:
            img_np = np.array(image)
            features_list = []

            # 1. Original image features
            original_features = self._extract_global_features(image)
            if original_features is not None:
                features_list.append(original_features)

            # 2. Color features
            color_features = self._extract_color_features(img_np)
            if color_features is not None:
                features_list.append(color_features)

            if not features_list:
                return None

            # Combine features with weights
            weights = [0.7, 0.3]  # Prioritize CNN features
            combined_features = np.concatenate([
                f * w for f, w in zip(features_list, weights[:len(features_list)])
            ])
            
            return combined_features

        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None


    def calculate_similarity_multi_view(self, features, reference_features_list):
        """Calculate similarity against multiple reference views"""
        if not reference_features_list:
            return 0.0

        similarities = []
        for ref_features in reference_features_list:
            sim = self.calculate_similarity(features, ref_features)
            similarities.append(sim)

        # Return maximum similarity across all views
        return max(similarities)

    def _extract_global_features(self, image):
        """Extract global features using EfficientNet"""
        try:
            # Apply transform pipeline
            image_tensor = self.transform(image).unsqueeze(0)
            image_tensor = image_tensor.to(self.device)
            
            with torch.no_grad():
                features = self.model.features(image_tensor)
                features = F.adaptive_avg_pool2d(features, (1, 1))
                features = features.squeeze().cpu().numpy()
            
            return features
        except Exception:
            return None

    def _extract_color_features(self, img_np):
        """Extract simplified color features"""
        try:
            features = []
            
            # RGB histogram with fewer bins
            for channel in range(3):
                hist = cv2.calcHist([img_np], [channel], None, [32], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                features.extend(hist)
            
            # Add HSV histogram for better color representation
            hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            for channel in range(3):
                hist = cv2.calcHist([hsv], [channel], None, [32], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                features.extend(hist)
            
            return np.array(features)
        except Exception:
            return None

    def calculate_similarity(self, features1, features2):
        """Optimized similarity calculation"""
        if features1 is None or features2 is None:
            return 0.0
            
        min_length = min(len(features1), len(features2))
        features1 = features1[:min_length]
        features2 = features2[:min_length]
        
        # Simple normalization
        features1 = features1 / (np.linalg.norm(features1) + 1e-7)
        features2 = features2 / (np.linalg.norm(features2) + 1e-7)
        
        return cosine_similarity(features1.reshape(1, -1), features2.reshape(1, -1))[0][0]