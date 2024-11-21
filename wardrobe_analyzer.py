import asyncio
from PIL import Image
from classifier import classify_outfit
import io
class WardrobeDescriber:
    def __init__(self, wardrobe_tracker):
        self.wardrobe_tracker = wardrobe_tracker
        
    async def add_description_to_item(self, item_id, collection="items"):
        """Add AI-generated description to an existing wardrobe item"""
        # Find the item in the database
        item = None
        for existing_item in self.wardrobe_tracker.database[collection]:
            if existing_item['id'] == item_id:
                item = existing_item
                break
                
        if not item:
            raise ValueError(f"Item with ID {item_id} not found in {collection}")
        
        # Get the base image
        if 'image' not in item:
            raise ValueError("Item has no image")
            
        # Convert base64 to PIL Image
        image = self.wardrobe_tracker.base64_to_image(item['image'])
        if not image:
            raise ValueError("Failed to load item image")
        
        # Get the AI description using classify_outfit
        try:
            description = await self.analyze_item(image)
            
            # Add or update the description in the item
            item['ai_analysis'] = description
            
            # Save the updated database
            self.wardrobe_tracker.save_database()
            return True
            
        except Exception as e:
            print(f"Error analyzing item: {e}")
            return False
            
    async def analyze_item(self, image):
        """Get AI analysis for a single image"""
        # Get the classification
        description = await asyncio.create_task(classify_outfit(image))
        return description
        
    async def analyze_all_items(self):
        """Add descriptions to all items that don't have them"""
        for collection in ["items", "outfits"]:
            for item in self.wardrobe_tracker.database[collection]:
                if 'ai_analysis' not in item:
                    await self.add_description_to_item(item['id'], collection)
                    
    def get_item_description(self, item_id, collection="items"):
        """Retrieve the AI description for an item"""
        for item in self.wardrobe_tracker.database[collection]:
            if item['id'] == item_id:
                return item.get('ai_analysis')
        return None