import os
import csv
from PIL import Image, ImageDraw, ImageFont

# Load the base switch image
image_path = "HPE-5130-48-Port.png"

# Get a list of all CSV files in the current directory
csv_files = [f for f in os.listdir() if f.endswith(".csv")]

# Define the port regions manually (as already given)
ports = {
    1: (53, 54, 112, 102),
    2: (53, 119, 112, 165),
    3: (116, 54, 176, 102),
    4: (116, 119, 176, 165),
    5: (179, 54, 239, 102),
    6: (179, 119, 239, 165),
    7: (242, 54, 302, 102),
    8: (242, 119, 302, 165),
    9: (305, 54, 365, 102),
    10: (305, 119, 365, 165),
    11: (368, 54, 428, 102),
    12: (368, 119, 428, 165),
    13: (464, 54, 524, 102),
    14: (464, 119, 524, 165),
    15: (527, 54, 587, 102),
    16: (527, 119, 587, 165),
    17: (590, 54, 650, 102),
    18: (590, 119, 650, 165),
    19: (653, 54, 713, 102),
    20: (653, 119, 713, 165),
    21: (716, 54, 776, 102),
    22: (716, 119, 776, 165),
    23: (779, 54, 839, 102),
    24: (779, 119, 839, 165),
    25: (875, 54, 935, 102),
    26: (875, 119, 935, 165),
    27: (938, 54, 998, 102),
    28: (938, 119, 998, 165),
    29: (1001, 54, 1061, 102),
    30: (1001, 119, 1061, 165),
    31: (1064, 54, 1124, 102),
    32: (1064, 119, 1124, 165),
    33: (1127, 54, 1187, 102),
    34: (1127, 119, 1187, 165),
    35: (1190, 54, 1250, 102),
    36: (1190, 119, 1250, 165),
    37: (1286, 54, 1346, 102),
    38: (1286, 119, 1346, 165),
    39: (1349, 54, 1409, 102),
    40: (1349, 119, 1409, 165),
    41: (1412, 54, 1472, 102),
    42: (1412, 119, 1472, 165),
    43: (1475, 54, 1535, 102),
    44: (1475, 119, 1535, 165),
    45: (1538, 54, 1598, 102),
    46: (1538, 119, 1598, 165),
    47: (1601, 54, 1661, 102),
    48: (1601, 119, 1661, 165),
}

# Define VLAN to color mapping (RGB format)
vlan_colors = {
    298: (128, 0, 128),  # Purple
    90: (255, 165, 0),    # Orange
    192: (255, 0, 0),     # Red
    511: (255, 255, 0),   # Yellow
    1: (255, 255, 255),   # White
}

# Function to add VLAN key with color backgrounds and black border
def add_vlan_key(draw, start_y, image_width, vlan_colors):
    # Create a single line string for the key
    box_width = 100  # Width of the background box for each VLAN
    space_between_boxes = 10  # Space between each box

    # Try loading a font (fallback to default)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()

    # Calculate the width needed for the entire key line
    total_width = 0
    for vlan, color in vlan_colors.items():
        text_width, _ = font.getbbox(str(vlan))[2:4]  # Get width of the text
        total_width += box_width + space_between_boxes

    # Calculate x_position to center the key line
    x_position = (image_width - total_width) // 2
    y_position = start_y

    # Draw each VLAN number with a colored background
    for vlan, color in vlan_colors.items():
        # Draw the background (color box)
        draw.rectangle([x_position, y_position, x_position + box_width, y_position + 20], fill=color)

        # Draw a black border around the filled section
        draw.rectangle([x_position, y_position, x_position + box_width, y_position + 20], outline="black", width=2)

        # Draw the VLAN number on top of the background
        text = str(vlan)
        text_width, text_height = font.getbbox(text)[2:4]  # Get the width of the text
        text_x = x_position + (box_width - text_width) // 2  # Center the text
        text_y = y_position + (20 - text_height) // 2  # Center the text vertically
        draw.text((text_x, text_y), text, fill="black", font=font)

        # Move to the next position
        x_position += box_width + space_between_boxes

# Iterate over each CSV file in the directory
for csv_file_path in csv_files:
    print(f"Processing {csv_file_path}...")

    # Initialize VLAN mapping and Running status
    vlan_mapping = {}
    running_status = {}

    # Read and process each CSV file
    with open(csv_file_path, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)

        # Ensure we handle header and data properly
        for row in reader:
            try:
                switch = int(row["Switch"])  # Ensure it's not a header row
                port = int(row["Port"])
                vlan = int(row["VLAN"])
                running = row["Running"].strip().upper()  # Read "Running" column
            except ValueError:
                continue  # Skip rows with invalid values (like the header row)

            if switch not in vlan_mapping:
                vlan_mapping[switch] = {}
                running_status[switch] = {}

            vlan_mapping[switch][port] = vlan
            running_status[switch][port] = running == "UP"  # True if UP, False otherwise

    # Load the base switch image
    image = Image.open(image_path).convert("RGB")  # Ensure RGB mode
    pixels = image.load()  # Access the pixel data

    # Define the target color to replace (RGB for #333333)
    target_color = (51, 51, 51)

    # Create an image to combine all switch images
    final_image_width = image.width
    final_image_height = image.height * len(vlan_mapping) + 60  # Added space for key
    final_image = Image.new("RGB", (final_image_width, final_image_height), "white")

    # Process each switch and add to the final image
    y_offset = 0
    for switch_num, ports_vlan in vlan_mapping.items():
        # Copy the base image for each switch
        switch_image = image.copy()
        switch_pixels = switch_image.load()
        draw = ImageDraw.Draw(switch_image)

        # Process each port for the current switch
        for port_num, vlan_id in ports_vlan.items():
            if port_num in ports:
                x1, y1, x2, y2 = ports[port_num]
                new_color = vlan_colors.get(vlan_id, None)
                if new_color:
                    for x in range(x1, x2 + 1):
                        for y in range(y1, y2 + 1):
                            if switch_pixels[x, y] == target_color:
                                switch_pixels[x, y] = new_color

                # If the port is UP, draw a green circle
                if running_status[switch_num].get(port_num, False):
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Center of the port
                    radius = min((x2 - x1), (y2 - y1)) // 6  # Fixed-size circle
                    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(0, 255, 0))

        # Paste the switch image into the final image
        final_image.paste(switch_image, (0, y_offset))
        y_offset += image.height  # Move down for the next switch

    # Add VLAN key at the bottom
    draw_final = ImageDraw.Draw(final_image)
    add_vlan_key(draw_final, y_offset + 10, final_image_width, vlan_colors)

    # Generate output path based on the CSV file name
    output_path = os.path.splitext(csv_file_path)[0] + ".png"
    # Save the combined image
    final_image.save(output_path)
    print(f"All switch VLAN-colored diagram saved to {output_path}")
