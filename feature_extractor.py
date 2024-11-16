import torch
import numpy as np
import cv2
import torch.nn.functional as F
from sklearn.metrics.pairwise import cosine_similarity
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.transforms import functional as TF

class FeatureExtractor:
    def __init__(self):
        # Feature extraction model
        self.model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet50', pretrained=True)
        self.model.eval()
        
        # Object detection model for outfit segmentation
        self.detector = fasterrcnn_resnet50_fpn(pretrained=True)
        self.detector.eval()
        
        # Clothing categories for detection
        self.clothing_categories = [
            'top', 'pants', 'dress', 'shoes', 'jacket', 
            'skirt', 'hat', 'accessory'
        ]

    def detect_outfit_pieces(self, image):
        """Detect multiple clothing items in a single image"""
        img_tensor = TF.to_tensor(image)
        with torch.no_grad():
            predictions = self.detector([img_tensor])
        
        boxes = predictions[0]['boxes'].cpu().numpy()
        scores = predictions[0]['scores'].cpu().numpy()
        
        # Filter confident detections
        confident_detections = scores > 0.7
        return boxes[confident_detections]

    def extract_features(self, image, is_full_outfit=False):
        """Extract features with outfit awareness"""
        try:
            if is_full_outfit:
                # Detect individual pieces
                boxes = self.detect_outfit_pieces(image)
                
                # Extract features for each detected piece
                all_features = []
                img_np = np.array(image)
                
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box)
                    piece_img = img_np[y1:y2, x1:x2]
                    if piece_img.size == 0:
                        continue
                        
                    piece_features = self._extract_single_item_features(Image.fromarray(piece_img))
                    if piece_features is not None:
                        all_features.append(piece_features)
                
                if not all_features:
                    return self._extract_single_item_features(image)
                    
                # Combine features from all pieces
                return np.mean(all_features, axis=0)
            else:
                return self._extract_single_item_features(image)
                
        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None

    def _extract_single_item_features(self, image):
        """Extract features for a single clothing item"""
        image_tensor = torch.from_numpy(np.array(image))
        image_tensor = image_tensor.permute(2, 0, 1).float() / 255.0
        image_tensor = F.interpolate(image_tensor.unsqueeze(0), size=(224, 224))
        
        with torch.no_grad():
            features = self.model(image_tensor)
            
        # Add color histogram features
        img_np = np.array(image)
        hist_features = []
        for channel in range(3):
            hist = cv2.calcHist([img_np], [channel], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            hist_features.extend(hist)
            
        # Combine ResNet and color features
        return np.concatenate([
            features.squeeze().numpy(),
            np.array(hist_features) * 0.3
        ])

    def calculate_similarity(self, features1, features2):
        min_length = min(len(features1), len(features2))
        return cosine_similarity(
            features1[:min_length].reshape(1, -1),
            features2[:min_length].reshape(1, -1)
        )[0][0]