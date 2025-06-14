# Recipe Scanner

This application converts images of recipes into structured table format. It uses OCR (Optical Character Recognition) to extract text from images and processes it into a readable table format.

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR engine

### Installing Tesseract OCR

#### macOS
```bash
brew install tesseract
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr
```

#### Windows
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script:
```bash
python recipe_scanner.py
```

The application will:
1. Accept an image input (file or camera)
2. Process the image using OCR
3. Extract recipe information
4. Convert the data into a structured table format 