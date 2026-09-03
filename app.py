import os
import zipfile
import json

# Your powerbi input file
file_path = os.path.join(os.getcwd(), 'powerbifile.pbit')

# Open the .pbit file directly as a ZIP archive
try:
    with zipfile.ZipFile(file_path, 'r') as pbit_zip:
        
        # The Layout file is usually located in the 'Report' folder inside the archive
        # You can use pbit_zip.namelist() to see all files if the path changes
        layout_bytes = pbit_zip.read('Report/Layout')
        
        # Power BI JSON files are almost always encoded in UTF-16-LE
        layout_string = layout_bytes.decode('utf-16-le')
        
        # Parse the JSON string into a Python dictionary
        layout = json.loads(layout_string)
        
        print("Successfully loaded Layout into a dictionary!")
        
        # Example: Print the top-level keys to verify
        print("Top-level keys:", layout.keys())

except FileNotFoundError:
    print(f"Error: Could not find the file at {file_path}")
except KeyError:
    print("Error: 'Report/Layout' was not found inside the .pbit file.")
except json.JSONDecodeError:
    print("Error: Could not parse the Layout file as JSON. The encoding might be different.")

if layout:
    color_keys = {
        'objects': set([
            'color',
            'fill',
            'fontColor',
            'barColor',
            'barBorderColor',
            'lineColor',
            'strokeColor',
            'markerColor',
            'labelColor',
            'dataLabelColor',
            'outlineColor',
            'borderColor',
            'backgroundColor',
            'backColorSecondary',
            'fillColor',
            'areaColor',
            'increaseFill',
            'decreaseFill',
            'totalFill',
            'goalFontColor',
            'distanceFontColor',
            'secTitleColor',
        ]),
        'vcObjects': set([
            'fontColor',
            'background',
            'color',
        ]),
    }

    font_family_keys = {
        'objects': set([
            'fontFamily',
            'titleFontFamily',
            'goalFontFamily',
            'distanceFontFamily',
            'secFontFamily',
            'secTitleFontFamily',
        ]),
        'vcObjects': set([
            'fontFamily',
        ]),
    }
    sections = layout.get('sections', [])
    colors = set()
    for sec in sections:
        for cont in sec.get('visualContainers', []):
            config = json.loads(cont.get('config', ""))
            objects = config.get('singleVisual', {}).get('objects', {})
            def recurse(keys, obj):
                for key in keys:
                    if isinstance(obj[key], str):
                        if key in color_keys['objects']:
                            colors.add(obj[key])
                    elif isinstance(obj[key], dict):
                        recurse(obj[key].keys(), obj[key])
                    elif isinstance(obj[key], list):
                        for item in obj[key]:
                            recurse(item.keys(), item)
                    
            recurse(objects.keys(), objects)

    print("Colours found :", colors)

        
else:
    print("No Layout found")