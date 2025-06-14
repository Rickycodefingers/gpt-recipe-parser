import cv2
import easyocr
import pandas as pd
import numpy as np
import os
from typing import Tuple, List, Dict

class RecipeScanner:
    def __init__(self):
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(['en'])
        # Initialize recipe components
        self.ingredients = []
        self.instructions = []
        self.title = ""

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess the image for better OCR results."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply thresholding to preprocess the image
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        # Apply dilation to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        gray = cv2.dilate(gray, kernel, iterations=1)
        return gray

    def extract_text(self, image_path: str) -> str:
        """Extract text from the image using EasyOCR."""
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")
        # Preprocess the image
        processed_image = self.preprocess_image(image)
        # Perform OCR
        results = self.reader.readtext(processed_image)
        # Combine all detected text
        text = ' '.join([result[1] for result in results])
        return text

    def parse_recipe(self, text: str) -> Dict:
        """Parse the extracted text into recipe components."""
        lines = text.split('\n')
        recipe_data = {
            'title': '',
            'ingredients': [],
            'instructions': []
        }
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Try to identify sections
            lower_line = line.lower()
            if 'ingredients' in lower_line:
                current_section = 'ingredients'
                continue
            elif 'instructions' in lower_line or 'directions' in lower_line:
                current_section = 'instructions'
                continue
            elif not recipe_data['title'] and current_section is None:
                recipe_data['title'] = line
                continue
            # Add content to appropriate section
            if current_section == 'ingredients':
                recipe_data['ingredients'].append(line)
            elif current_section == 'instructions':
                recipe_data['instructions'].append(line)
        return recipe_data

    def create_table(self, recipe_data: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Convert recipe data into a pandas DataFrame."""
        # Create ingredients table
        ingredients_df = pd.DataFrame({
            'Ingredient': recipe_data['ingredients']
        })
        # Create instructions table
        instructions_df = pd.DataFrame({
            'Step': range(1, len(recipe_data['instructions']) + 1),
            'Instruction': recipe_data['instructions']
        })
        return ingredients_df, instructions_df

    def process_recipe(self, image_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Process a recipe image and return structured tables."""
        # Extract text from image
        text = self.extract_text(image_path)
        # Parse recipe components
        recipe_data = self.parse_recipe(text)
        # Create tables
        ingredients_df, instructions_df = self.create_table(recipe_data)
        return ingredients_df, instructions_df

def main():
    scanner = RecipeScanner()
    # Example usage
    image_path = input("Enter the path to your recipe image: ")
    try:
        ingredients_df, instructions_df = scanner.process_recipe(image_path)
        print("\nRecipe Title:", scanner.title)
        print("\nIngredients:")
        print(ingredients_df.to_string(index=False))
        print("\nInstructions:")
        print(instructions_df.to_string(index=False))
        # Save to CSV files
        ingredients_df.to_csv('ingredients.csv', index=False)
        instructions_df.to_csv('instructions.csv', index=False)
        print("\nTables have been saved to 'ingredients.csv' and 'instructions.csv'")
    except Exception as e:
        print(f"Error processing recipe: {str(e)}")

if __name__ == "__main__":
    main() 