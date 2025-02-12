import os
import csv
import argparse
from PIL import Image, ImageDraw, ImageFont

# --- Command-Line Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Process switch CSV file using a specified base image, ports, and VLAN colors configuration."
)
parser.add_argument(
    "--image",
    required=True,
    help="Path to the base switch image file (e.g., '48 PORTS.png')."
)
parser.add_argument(
    "--ports",
    required=True,
    help="Path to the ports CSV file (e.g., 'configcsvs/48ports.csv')."
)
parser.add_argument(
    "--vlan_colors",
    default=os.path.join("configcsvs", "vlan_colors.csv"),
    help="Path to the VLAN colors CSV file (default: 'configcsvs/vlan_colors.csv')."
)
parser.add_argument(
    "--switch_csv",
    required=True,
    help="Path to the CSV file containing switch port details (e.g., 'switch_details.csv')."
)
args = parser.parse_args()

# --- Set file paths from command-line arguments ---
IMAGE_PATH = args.image
PORTS_FILE = args.ports
VLAN_COLORS_FILE = args.vlan_colors
SWITCH_CSV_FILE = args.switch_csv

# --- READ PORTS FROM CSV ---
# The ports CSV is expected to have a header: Port,x1,y1,x2,y2
ports = {}
with open(PORTS_FILE, mode="r", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        port = int(row["Port"])
        x1 = int(row["x1"])
        y1 = int(row["y1"])
        x2 = int(row["x2"])
        y2 = int(row["y2"])
        ports[port] = (x1, y1, x2, y2)

# --- READ VLAN COLORS FROM CSV ---
# The VLAN colors CSV is expected to have a header: vlan,r,g,b
vlan_colors = {}
with open(VLAN_COLORS_FILE, mode="r", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        vlan_val = row["vlan"]
        try:
            key = int(vlan_val)
        except ValueError:
            key = vlan_val
        r = int(row["r"])
        g = int(row["g"])
        b = int(row["b"])
        vlan_colors[key] = (r, g, b)

# Verifies the Base Switch Image
if not os.path.isfile(IMAGE_PATH):
    raise FileNotFoundError(f"Base image file '{IMAGE_PATH}' not found.")

# Checks if Switch column has a number
def extract_numeric_switch(switch_name):
    numeric_part = ''.join(filter(str.isdigit, switch_name))
    return int(numeric_part) if numeric_part else None

print(f"Processing {SWITCH_CSV_FILE}...")

vlan_mapping = {}    # Mapping: switch -> { port: vlan }
running_status = {}  # Mapping: switch -> { port: True/False }

with open(SWITCH_CSV_FILE, mode="r", newline="") as csvfile:
    reader = csv.reader(csvfile)
    first_row = next(reader)
    if first_row == ["Switch", "Port", "Running", "VLAN"]:
        has_headers = True
    else:
        has_headers = False
        csvfile.seek(0)  # Reset file pointer to re-read data

    reader = csv.DictReader(csvfile) if has_headers else csv.reader(csvfile)
    for row in reader:
        try:
            if has_headers:
                switch_name = row["Switch"]
                switch = extract_numeric_switch(switch_name)
                port = int(row["Port"])
                running = row["Running"].strip().upper()
                vlan = int(row["VLAN"])
            else:
                switch_name = row[0]
                switch = extract_numeric_switch(switch_name)
                port = int(row[1])
                running = row[2].strip().upper()
                vlan = int(row[3])
            if switch is None:
                continue
            if switch not in vlan_mapping:
                vlan_mapping[switch] = {}
                running_status[switch] = {}
            vlan_mapping[switch][port] = vlan
            running_status[switch][port] = (running == "UP")
        except ValueError:
            continue

# Open the Base Switch Image
image = Image.open(IMAGE_PATH).convert("RGB")
target_color = (51, 51, 51)  # The color in the image to be replaced (e.g., dark gray)

final_image_width = image.width
final_image_height = image.height * len(vlan_mapping) + 60 + 50
final_image = Image.new("RGB", (final_image_width, final_image_height), "white")

y_offset = 0
for switch_num, ports_vlan in vlan_mapping.items():
    switch_image = image.copy()
    switch_pixels = switch_image.load()
    draw = ImageDraw.Draw(switch_image)
    for port_num, vlan_id in ports_vlan.items():
        if port_num in ports:
            x1, y1, x2, y2 = ports[port_num]
            new_color = vlan_colors.get(vlan_id, None)
            if new_color:
                for x in range(x1, x2 + 1):
                    for y in range(y1, y2 + 1):
                        if switch_pixels[x, y] == target_color:
                            switch_pixels[x, y] = new_color
            if running_status[switch_num].get(port_num, False):
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                radius = min((x2 - x1), (y2 - y1)) // 6
                draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(0, 255, 0))
    final_image.paste(switch_image, (0, y_offset))
    y_offset += image.height

# Build Legend Dictionary for the Key
legend = {}
patch_color = (255, 192, 203)
for vlan_id, color in vlan_colors.items():
    if color == patch_color:
        legend["PATCH"] = patch_color
    else:
        legend[vlan_id] = color

# Draw the VLAN Key and Switch CSV Name at the Bottom
key_y_offset = final_image_height - 55  # Vertical offset for the key
draw_final = ImageDraw.Draw(final_image)
try:
    # Try loading Arial with a size of 32; adjust the size as needed.
    font = ImageFont.truetype("arial.ttf", 32)
except IOError:
    font = ImageFont.load_default()

key_spacing = 200   # Horizontal spacing between each key element

# Compute initial x-offset so that the keys are centered (or pushed right)
num_keys = len(legend)
total_legend_width = num_keys * key_spacing
key_x_offset = (final_image_width - total_legend_width) // 2

# Draw the switch CSV file name above the key
switch_csv_name = os.path.basename(SWITCH_CSV_FILE)
# Set a vertical position for the switch label above the key; adjust as desired.
switch_label_y = key_y_offset - 45
# Use font.getbbox() to get text dimensions.
bbox = font.getbbox(switch_csv_name)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
switch_x = (final_image_width - text_width) // 2
draw_final.text((switch_x, switch_label_y), switch_csv_name, fill="black", font=font)

# Draw the Legend (VLAN Key)
for key_label, color in legend.items():
    rect_x1, rect_y1 = key_x_offset - 15, key_y_offset
    rect_x2, rect_y2 = key_x_offset + 120, key_y_offset + 43
    draw_final.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill=color, outline="black", width=2)
    draw_final.text((key_x_offset, key_y_offset + 5), str(key_label), fill="black", font=font)
    key_x_offset += key_spacing

output_path = os.path.splitext(SWITCH_CSV_FILE)[0] + ".png"
final_image.save(output_path)
print(f"Saved VLAN-colored diagram to {output_path}")

# Example command-line usage:
# python switch_ports.py --image "48 PORTS.png" --ports "configcsvs/48ports.csv" --switch_csv "CServerRoom.csv"
