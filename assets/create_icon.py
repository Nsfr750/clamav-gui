from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create a 256x256 image with a blue background
    img = Image.new('RGB', (256, 256), color=(0, 90, 171))  # Blue background
    d = ImageDraw.Draw(img)
    
    # Add text to the icon
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 100)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw "CAV" in white
    d.text((50, 70), "CAV", fill=(255, 255, 255), font=font)
    
    # Save as ICO and PNG
    img.save("assets/icon.ico", "ICO", sizes=[(256, 256)])
    img.save("assets/icon.png", "PNG")

if __name__ == "__main__":
    if not os.path.exists("assets"):
        os.makedirs("assets")
    create_icon()
