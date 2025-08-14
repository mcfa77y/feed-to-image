"""
XKCD Comic Image Generator Plugin

This plugin fetches XKCD comics and generates formatted images with:
- Resized comic image
- Alt text displayed at the bottom
- QR code linking to the original comic
- Customizable dimensions

Usage:
    python __main__.py [WIDTHxHEIGHT] [comic_number]
    
Examples:
    python __main__.py 800x600 353
    python __main__.py 353
    python __main__.py
"""

import math
import random
import sys
from typing import Tuple, Optional

import qrcode
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from fonts.ttf import Roboto

# Configuration constants
DEFAULT_IMAGE_WIDTH = 600
DEFAULT_IMAGE_HEIGHT = 448
FOOTER_MARGIN_PIXELS = 10
OUTPUT_DIRECTORY = "build"
DEFAULT_FONT_SIZE = 18
COMIC_BOTTOM_MARGIN = 100
QR_CODE_SIZE = 2
QR_CODE_BORDER = 2
QR_CODE_BOTTOM_OFFSET = 20
DEFAULT_LINE_SPACING = 1.1

# Initialize font and dimensions
default_font = ImageFont.truetype(Roboto, DEFAULT_FONT_SIZE)
canvas_width = DEFAULT_IMAGE_WIDTH
canvas_height = DEFAULT_IMAGE_HEIGHT


def render_text_in_rectangle(
    canvas: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    text_color: Tuple[int, int, int],
    rectangle_bounds: Tuple[int, int, int, int],
    horizontal_alignment: str = 'left',
    vertical_alignment: str = 'top',
    line_spacing_multiplier: float = DEFAULT_LINE_SPACING
) -> Optional[Tuple[int, int, int, int]]:
    """
    Render text within a specified rectangle, automatically scaling font size to fit.
    
    Args:
        canvas: PIL ImageDraw object to draw on
        text: Text content to render
        font: Font object to use for rendering
        text_color: RGB color tuple for text
        rectangle_bounds: (left, top, right, bottom) rectangle coordinates
        horizontal_alignment: 'left' or 'center' text alignment
        vertical_alignment: 'top' or 'center' text alignment
        line_spacing_multiplier: Multiplier for line height spacing
        
    Returns:
        Tuple of actual text bounds (left, top, right, bottom) or None if text doesn't fit
    """
    rect_width = rectangle_bounds[2] - rectangle_bounds[0]
    rect_height = rectangle_bounds[3] - rectangle_bounds[1]

    # Iteratively reduce font size until text fits in rectangle
    current_font = font
    while current_font.size > 0:
        line_height = int(current_font.size * line_spacing_multiplier)
        max_lines_possible = math.floor(rect_height / line_height)
        text_lines = []

        # Break text into lines that fit within the rectangle width
        remaining_words = text.split(" ")

        while len(text_lines) < max_lines_possible and len(remaining_words) > 0:
            current_line_words = []

            # Add words to current line until width limit is reached
            while (len(remaining_words) > 0 and 
                   current_font.getbbox(" ".join(current_line_words + [remaining_words[0]]))[2] <= rect_width):
                current_line_words.append(remaining_words.pop(0))

            if current_line_words:  # Only add non-empty lines
                text_lines.append(" ".join(current_line_words))
            else:
                break  # Word too long for line, need smaller font

        # Check if all text fits
        if len(text_lines) <= max_lines_possible and len(remaining_words) == 0:
            # Calculate starting Y position based on vertical alignment
            if vertical_alignment == 'top':
                start_y = int(rectangle_bounds[1])
            else:  # center alignment
                total_text_height = len(text_lines) * line_height
                start_y = int(rectangle_bounds[1] + (rect_height / 2) - (total_text_height / 2) - (line_height - current_font.size) / 2)

            # Track actual text bounds
            text_bounds = [rectangle_bounds[2], start_y, rectangle_bounds[0], start_y + len(text_lines) * line_height]

            # Render each line
            current_y = start_y
            for line_text in text_lines:
                line_width = current_font.getbbox(line_text)[2]
                
                # Calculate X position based on horizontal alignment
                if horizontal_alignment == 'center':
                    line_x = int(rectangle_bounds[0] + (rect_width / 2) - (line_width / 2))
                else:  # left alignment
                    line_x = rectangle_bounds[0]
                    
                # Update bounds tracking
                text_bounds[0] = min(text_bounds[0], line_x)
                text_bounds[2] = max(text_bounds[2], line_x + line_width)
                
                # Draw the line
                canvas.text((line_x, current_y), line_text, text_color, font=current_font)
                current_y += line_height

            return tuple(text_bounds)

        # Try smaller font size
        current_font = ImageFont.truetype(current_font.path, current_font.size - 1)
    
    return None  # Text doesn't fit even at smallest font size


def parse_command_line_arguments() -> Tuple[int, int, Optional[int]]:
    """
    Parse command line arguments for dimensions and comic number.
    
    Returns:
        Tuple of (width, height, comic_number)
        comic_number is None for latest comic
    """
    target_width = DEFAULT_IMAGE_WIDTH
    target_height = DEFAULT_IMAGE_HEIGHT
    comic_number = None
    
    if len(sys.argv) > 1:
        # Check if first argument contains dimensions
        if "x" in sys.argv[1]:
            try:
                target_width, target_height = [int(dimension) for dimension in sys.argv[1].split("x")]
                # Comic number would be in second argument if present
                if len(sys.argv) > 2:
                    comic_number = int(sys.argv[2])
            except ValueError:
                print("Invalid dimension format. Use WIDTHxHEIGHT (e.g., 800x600)")
                sys.exit(1)
        else:
            # First argument is comic number
            try:
                comic_number = int(sys.argv[1])
            except ValueError:
                print("Invalid comic number. Must be an integer.")
                sys.exit(1)
    
    return target_width, target_height, comic_number

def create_comic_url(comic_number: Optional[int] = None) -> str:
    if comic_number is not None:        
        return f"https://www.asofterworld.com/index.php?id={comic_number}"
    else:
        # random number between 1 and 1242
        comic_number = random.randint(1, 1242)
        return f"https://www.asofterworld.com/index.php?id={comic_number}"

def fetch_comic_metadata(comic_number: Optional[int] = None) -> dict:
    """
    Fetch comic metadata from the HTML page.
    
    Args:
        comic_number: Specific comic number, or None for random
        
    Returns:
        Dictionary containing comic metadata
    """
    comic_url = create_comic_url(comic_number)
    
    try:
        response = requests.get(comic_url)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract comic image and metadata
        comic_img_element = soup.select_one('#comicimg > img')
        if not comic_img_element:
            raise ValueError("Could not find comic image element")
        
        img_src = comic_img_element.get('src')
        title = comic_img_element.get('title', '')
        
        # Extract comic number from URL or use the passed/generated one
        if comic_number is None:
            # Extract from URL if it was randomly generated
            import re
            match = re.search(r'id=(\d+)', comic_url)
            comic_num = int(match.group(1)) if match else None
        else:
            comic_num = comic_number
        
        return {
            'img': img_src,
            'title': title,
            'num': comic_num,
            'alt': title,  # Using title as alt text as specified
            'url': comic_url
        }
        
    except requests.RequestException as error:
        print(f"Error fetching comic data: {error}")
        sys.exit(1)
    except Exception as error:
        print(f"Error parsing comic metadata: {error}")
        sys.exit(1)


def download_comic_image(image_url: str) -> Image.Image:
    """
    Download and open the comic image from URL.
    
    Args:
        image_url: URL of the comic image
        
    Returns:
        PIL Image object
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        return Image.open(response.raw)
    except requests.RequestException as error:
        print(f"Error downloading comic image: {error}")
        sys.exit(1)


def calculate_comic_dimensions(original_image: Image.Image, canvas_width: int, canvas_height: int) -> Tuple[int, int, int, int]:
    """
    Calculate the dimensions and position for the comic image on the canvas.
    
    Args:
        original_image: The original comic image
        canvas_width: Target canvas width
        canvas_height: Target canvas height
        
    Returns:
        Tuple of (resized_width, resized_height, offset_x, offset_y)
    """
    original_width, original_height = original_image.size
    available_height = canvas_height - COMIC_BOTTOM_MARGIN
    
    # Calculate scaling ratio to fit image within available space
    width_ratio = canvas_width / original_width
    height_ratio = available_height / original_height
    scaling_ratio = min(width_ratio, height_ratio, 1.0)  # Don't upscale
    
    # Calculate new dimensions
    new_width = int(original_width * scaling_ratio)
    new_height = int(original_height * scaling_ratio)
    
    # Center the image
    offset_x = int((canvas_width - new_width) / 2)
    offset_y = int((available_height - new_height) / 2)
    
    return new_width, new_height, offset_x, offset_y


def create_qr_code(comic_url: str) -> Image.Image:
    """
    Generate a QR code for the comic URL.
    
    Args:
        comic_url: URL to encode in QR code
        
    Returns:
        PIL Image of the QR code
    """
    qr_generator = qrcode.QRCode(
        version=1,
        box_size=QR_CODE_SIZE,
        border=QR_CODE_BORDER
    )
    qr_generator.add_data(comic_url)
    qr_generator.make(fit=True)
    
    return qr_generator.make_image(fill_color="black", back_color="white").get_image()


def generate_filename_suffix(comic_metadata: dict, canvas_width: int, canvas_height: int) -> str:
    """
    Generate appropriate filename suffix based on comic and dimensions.
    
    Args:
        comic_metadata: Comic metadata dictionary
        canvas_width: Canvas width
        canvas_height: Canvas height
        
    Returns:
        Filename suffix string
    """
    # Use comic number if available, otherwise "daily"
    comic_identifier = str(comic_metadata.get("num", "daily"))
    
    # Add dimensions if different from default
    dimension_suffix = ""
    if (canvas_width, canvas_height) != (DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT):
        dimension_suffix = f"-{canvas_width}x{canvas_height}"
    
    return f"{dimension_suffix}-{comic_identifier}"


def main():
    """
    Main function to generate XKCD comic image.
    """
    global canvas_width, canvas_height
    
    # Parse command line arguments
    canvas_width, canvas_height, comic_number = parse_command_line_arguments()
    
    # Fetch comic metadata
    comic_metadata = fetch_comic_metadata(comic_number)
    print(f"Processing comic #{comic_metadata.get('num')}: {comic_metadata.get('title')}")
    
    # Download comic image
    comic_image = download_comic_image(comic_metadata.get("img"))
    
    # Calculate comic dimensions and position
    comic_width, comic_height, comic_x, comic_y = calculate_comic_dimensions(
        comic_image, canvas_width, canvas_height
    )
    
    # Resize comic if necessary
    if (comic_width, comic_height) != comic_image.size:
        comic_image = comic_image.resize((comic_width, comic_height))
    
    # Create QR code
    comic_url = f"https://www.asofterworld.com/index.php?id={comic_metadata.get('num')}/"
    qr_code_image = create_qr_code(comic_url)
    qr_width, qr_height = qr_code_image.size
    
    # Calculate QR code position (bottom right)
    qr_x = canvas_width - qr_width - FOOTER_MARGIN_PIXELS
    qr_y = canvas_height - qr_height - FOOTER_MARGIN_PIXELS - QR_CODE_BOTTOM_OFFSET
    
    # Calculate text area (bottom left, next to QR code)
    text_area_x = FOOTER_MARGIN_PIXELS
    text_area_y = qr_y
    text_area_width = qr_x - FOOTER_MARGIN_PIXELS - text_area_x
    text_area_height = qr_height
    
    # Create output canvas
    output_canvas = Image.new("RGB", (canvas_width, canvas_height), color=(255, 255, 255))
    drawing_context = ImageDraw.Draw(output_canvas)
    
    # Paste comic image
    output_canvas.paste(comic_image, (comic_x, comic_y, comic_x + comic_width, comic_y + comic_height))
    
    # Paste QR code
    output_canvas.paste(qr_code_image, (qr_x, qr_y, qr_x + qr_width, qr_y + qr_height))
    
    # Render alt text
    alt_text = comic_metadata.get("alt", "")
    if alt_text:
        render_text_in_rectangle(
            drawing_context,
            alt_text,
            default_font,
            (0, 0, 0),  # Black text
            (text_area_x, text_area_y, text_area_x + text_area_width, text_area_y + text_area_height)
        )
    
    # Render website attribution
    render_text_in_rectangle(
        drawing_context,
        "www.asofterworld.com",
        default_font,
        (0, 0, 0),  # Black text
        (qr_x, qr_y + qr_height, qr_x + qr_width, qr_y + qr_height + QR_CODE_BOTTOM_OFFSET)
    )
    
    # Save output image
    filename_suffix = generate_filename_suffix(comic_metadata, canvas_width, canvas_height)
    output_filename = f"{OUTPUT_DIRECTORY}/softer_world{filename_suffix}.jpg"
    output_canvas.save(output_filename)
    
    print(f"Generated image saved as: {output_filename}")


if __name__ == "__main__":
    main()

