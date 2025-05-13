from PIL import Image, ImageDraw, ImageFont
import os

def create_default_crop_image():
    # Create a new image with a white background
    width = 800
    height = 600
    background_color = (245, 245, 245)  # Light gray background
    image = Image.new('RGB', (width, height), background_color)
    
    # Get a drawing context
    draw = ImageDraw.Draw(image)
    
    # Draw a placeholder icon
    icon_size = 200
    icon_x = (width - icon_size) // 2
    icon_y = (height - icon_size) // 2
    
    # Draw a simple plant icon
    stem_color = (76, 175, 80)  # Green
    draw.rectangle([icon_x + icon_size//2 - 10, icon_y + icon_size//2, 
                   icon_x + icon_size//2 + 10, icon_y + icon_size], 
                  fill=stem_color)
    
    # Draw leaves
    leaf_color = (129, 199, 132)  # Light green
    draw.ellipse([icon_x + icon_size//2 - 60, icon_y + icon_size//2 - 40,
                  icon_x + icon_size//2 + 60, icon_y + icon_size//2 + 40],
                 fill=leaf_color)
    
    # Add text
    text = "No Image Available"
    text_color = (33, 33, 33)  # Dark gray
    
    # Calculate text position (centered)
    text_bbox = draw.textbbox((0, 0), text)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = icon_y + icon_size + 20
    
    # Draw the text
    draw.text((text_x, text_y), text, fill=text_color)
    
    # Save the image
    output_path = os.path.join('static', 'images', 'default-crop.jpg')
    image.save(output_path, 'JPEG', quality=95)
    print(f"Default crop image created at: {output_path}")

if __name__ == '__main__':
    create_default_crop_image() 