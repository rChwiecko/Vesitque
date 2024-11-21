import json
import base64
from pathlib import Path
from PIL import Image
from io import BytesIO
import streamlit as st


class Marketplace:
    def __init__(self):
        self.db_path = Path("market_place_database.json")
        self.database = self.load_database()

    def load_database(self):
        """Load the marketplace database or initialize it if missing."""
        default_db = {"items": []}

        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    db = json.load(f)
                    # Ensure the "items" key exists
                    if "items" not in db:
                        db["items"] = []
                    return db
            else:
                # Create the database file if it doesn't exist
                with open(self.db_path, 'w') as f:
                    json.dump(default_db, f)
                return default_db
        except Exception as e:
            st.error(f"Error loading database: {str(e)}")
            return default_db

    def save_database(self):
        """Save updates to the marketplace database."""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.database, f, indent=4)
        except Exception as e:
            st.error(f"Error saving database: {str(e)}")

    def get_all_items(self):
        """Retrieve all items from the marketplace database."""
        return self.database.get("items", [])

    def remove_item(self, item_id):
        """Remove an item from the marketplace database by its ID."""
        try:
            self.database["items"] = [
                item for item in self.database["items"] if item["id"] != item_id
            ]
            self.save_database()
            return True
        except Exception as e:
            st.error(f"Error removing item: {str(e)}")
            return False

    def base64_to_image(self, base64_string):
        """Convert a base64 string back to a PIL Image."""
        try:
            image_data = base64.b64decode(base64_string)
            return Image.open(BytesIO(image_data))
        except Exception as e:
            st.error(f"Error converting image: {str(e)}")
            return None
