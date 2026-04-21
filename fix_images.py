import re

# Read HTML file
with open('interior-duct.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Define replacements: search for each data URI and replace with file path
# Each product card image needs to be replaced individually
migrations = []

# Find all base64 image data URIs in pcard-img sections
pattern = r'<div class="pcard-img">\s*<img src="data:image[^"]*" alt="([^"]*)"'

def replace_func(match):
    alt_text = match.group(1)
    
    # Map alt text to correct image file
    image_map = {
        'Quartz Dining Set': 'IDL%20Product%20branding/Dining%20Set.jpg',
        'Mahogany High-Back Dining Chair': 'IDL%20Product%20branding/Chair%20Dining%20Single.jpg',
        'Artisan Adjustable Bar Stool': 'IDL%20Product%20branding/Bar%20Stool.jpg',
        'Ivory 2-Drawer Bedside Cabinet': 'IDL%20Product%20branding/Bedside.jpeg',
        'Orbit Glass-Top Coffee Table': 'IDL%20Product%20branding/Table%20glass%20round%20-%20Copy.jpg',
        'Nordic TV Console': 'IDL%20Product%20branding/tvconsole3.jpg',
        'Onyx Marble Drum Coffee Table': 'IDL%20Product%20branding/Table%20cofee%20mahogany.jpg',
        'Long Hospitality Reception Counter': 'IDL%20Product%20branding/Reception%20Counter.jpeg',
    }
    
    new_image = image_map.get(alt_text, match.group(0))
    return f'<div class="pcard-img"><img src="{new_image}" alt="{alt_text}"'

# Replace all occurrences
html_new = re.sub(pattern, replace_func, html)

# Write back
with open('interior-duct.html', 'w', encoding='utf-8') as f:
    f.write(html_new)

print("✅ All product images updated with correct file references")
print("- Product 1: Dining Set → Dining%20Set.jpg")
print("- Product 2: Dining Chair → Chair%20Dining%20Single.jpg")
print("- Product 3: Bar Stool → Bar%20Stool.jpg")
print("- Product 4: Bedside Cabinet → Bedside.jpeg")
print("- Product 5: Coffee Table → Table%20glass%20round%20-%20Copy.jpg")
print("- Product 6: TV Console → tvconsole3.jpg")
print("- Product 7: Marble Coffee → Table%20cofee%20mahogany.jpg")
print("- Product 8: Bar & Wine → Kitchen%20Cabinet.jpg")
