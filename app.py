import json
import os
import re
import zipfile
import pprint

ELEMENT_MAP = {
    
    # Charts
    "barChart":                          "chart",
    "clusteredBarChart":                 "chart",
    "columnChart":                       "chart",
    "clusteredColumnChart":              "chart",
    "hundredPercentStackedBarChart":     "chart",
    "hundredPercentStackedColumnChart":  "chart",
    "lineChart":                         "chart",
    "areaChart":                         "chart",
    "stackedAreaChart":                  "chart",
    "hundredPercentStackedAreaChart":    "chart",
    "lineStackedColumnComboChart":       "chart",
    "lineClusteredColumnComboChart":     "chart",
    "ribbonChart":                       "chart",
    "waterfallChart":                    "chart",
    "funnel":                            "chart",
    "scatterChart":                      "chart",
    "pieChart":                          "chart",
    "donutChart":                        "chart",
    "treemap":                           "chart",
    "shapeMap":                          "chart",
    "azureMap":                          "chart",
    "decompositionTreeVisual":           "chart",
    "keyDriversVisual":                  "chart",
    "image":                             "chart",
    "tableEx":                           "chart",
    "pivotTable":                        "chart",
    "gauge":                             "chart",
    # 'shape':                             "textbox",

    'textbox':                           "textbox",

    # KPI / Single-value visuals
    "cardVisual":                        "kpi",
    "kpi":                               "kpi",
    "card":                              "kpi",

    # Filters
    "slicer":                            "filter",
    "advancedSlicerVisual":              "filter",
    "textSlicer":                        "filter",

}

# Your powerbi input file
file_path = os.path.join(os.getcwd(), 'powerbifile.pbix')
pp = pprint.PrettyPrinter(indent=4, sort_dicts=False)

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

    def extract_layout():
        sections = layout.get('sections', [])
        screens = {}
        width = height = 0
        for sec in sections:
            width = sec.get('width', 0)
            height = sec.get('height', 0)
            element_layout = {
                'kpi': [], 
                'filter': [],
                'chart': [],
                'textbox': [],
                'group': {}
            }
            
            # Preprocess the containers and seperate call the groups
            # groups = {}
            # for cont in sec.get('visualContainers', []):
            #     cont['config'] = 
            #     if 'singleVisualGroup' in cont['config']:
            #         groups[cont['config']['name']] = cont['config']

            for cont in sec.get('visualContainers', []):
                config = json.loads(cont.get('config', ""))
                if "singleVisualGroup" in config:
                    element_layout['group'][config['name']] = (
                        config['layouts'][0]['position']['x'],
                        config['layouts'][0]['position']['y'],
                        config['layouts'][0]['position']['width'],
                        config['layouts'][0]['position']['height'],
                        config.get('parentGroupName', '')
                    )
                else:
                    visual_type = config.get('singleVisual', {}).get('visualType', '')
                    visual_type = ELEMENT_MAP.get(visual_type, None)
                    if visual_type:
                        element_layout[visual_type].append((
                            config['layouts'][0]['position']['x'],
                            config['layouts'][0]['position']['y'],
                            config['layouts'][0]['position']['width'],
                            config['layouts'][0]['position']['height'],
                            config.get('parentGroupName', '')
                        ))
            screens[sec['displayName']] = element_layout
        return screens, width, height


    def extract_features(serach_keys, pattern):
        sections = layout.get('sections', [])
        colors = set()
        fonts = set()
        for sec in sections:
            for cont in sec.get('visualContainers', []):
                config = json.loads(cont.get('config', ""))
                curr_key = None
                def recurse(keys, obj, top_layer: bool, main_obj_key: str, pattern: str):
                    nonlocal curr_key
                    for key in keys:
                        # if top_layer:
                        if key in serach_keys[main_obj_key]:
                            curr_key = key
                        if isinstance(obj[key], str):
                            if curr_key and bool(re.match(pattern, obj[key].strip())):
                                colors.add(obj[key])
                        elif isinstance(obj[key], dict):
                            recurse(obj[key].keys(), obj[key], False, main_obj_key, pattern)
                        elif isinstance(obj[key], list):
                            for item in obj[key]:
                                recurse(item.keys(), item, False, main_obj_key, pattern)
                        curr_key = None
                        
                objects = config.get('singleVisual', {}).get('objects', {})
                recurse(objects.keys(), objects, True, 'objects', pattern)
                
                objects = config.get('singleVisual', {}).get('vcObj6ects', {})
                recurse(objects.keys(), objects, True, 'vcObjects', pattern)
                # font_pattern = r".*"

        return colors
        # print("Fonts found :", fonts)
    
    color_pattern = r"^[ '\"]*#[0-9a-fA-F]{6}[ '\"]*$"
    font_pattern = r".*"
    print("Colors: ", extract_features(color_keys, color_pattern))
    print("Fonts: ", extract_features(font_family_keys, font_pattern))

    def generate_layout_html(screens, canvas_width, canvas_height, output_path="layout_preview.html"):
        STYLES = {
            'chart':   ('Chart',   '#4e8ef7', '#1a3a6b'),
            'kpi':     ('KPI',     '#f7a14e', '#6b3a1a'),
            'filter':  ('Filter',  '#4ef7a1', '#1a6b3a'),
            'textbox': ('Textbox', '#f7e94e', '#6b5f1a'),
        }

        page_names = list(screens.keys())

        def build_canvas(element_layout):
            groups = element_layout.get('group', {})

            # Map group -> child groups and group -> child elements
            child_groups   = {gid: [] for gid in groups}
            child_elements = {gid: [] for gid in groups}
            root_group_ids = []

            for gid, (*_, parent_gid) in groups.items():
                if parent_gid and parent_gid in groups:
                    child_groups[parent_gid].append(gid)
                else:
                    root_group_ids.append(gid)

            # Bucket elements into their immediate group or root canvas
            root_elements = []
            for el_type, rects in element_layout.items():
                if el_type == 'group':
                    continue
                label, bg, border = STYLES.get(el_type, (el_type, '#aaaaaa', '#555555'))
                for x, y, w, h, group_id in rects:
                    el_div = (
                        f'<div class="element {el_type}" '
                        f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
                        f'background:{bg}33;border:2px solid {border};">'
                        f'<span>{label}</span></div>'
                    )
                    if group_id and group_id in child_elements:
                        child_elements[group_id].append(el_div)
                    else:
                        root_elements.append(el_div)

            def render_group(gid, depth=0):
                gx, gy, gw, gh, _ = groups[gid]
                inner = "\n".join(
                    [render_group(cid, depth + 1) for cid in child_groups[gid]]
                    + child_elements[gid]
                )
                return (
                    f'<div class="group-container" data-depth="{depth}" '
                    f'style="left:{gx}px;top:{gy}px;width:{gw}px;height:{gh}px;">'
                    f'\n{inner}\n</div>'
                )

            blocks = [render_group(gid) for gid in root_group_ids] + root_elements
            return "\n".join(blocks)

        tab_buttons = "\n".join(
            f'<button class="tab-btn{" active" if i == 0 else ""}" onclick="showPage({i})">{name}</button>'
            for i, name in enumerate(page_names)
        )

        canvases = "\n".join(
            f'<div class="page-canvas{"" if i == 0 else " hidden"}" id="page-{i}" style="width:{canvas_width}px;height:{canvas_height}px;">'
            f'\n{build_canvas(screens[name])}\n</div>'
            for i, name in enumerate(page_names)
        )

        legend_items = "".join(
            f'<div class="legend-item"><span class="swatch" style="background:{bg};border-color:{border};"></span>{label}</div>'
            for _, (label, bg, border) in STYLES.items()
        )

        html = f"""<!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <title>Layout Preview</title>
            <style>
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                background: #1e1e1e;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 24px 24px 48px;
                font-family: sans-serif;
            }}
            h2 {{ color: #ddd; margin: 0 0 16px; font-size: 18px; }}
            small {{ font-size: 13px; color: #888; }}

            /* Legend */
            .legend {{ display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; justify-content: center; }}
            .legend-item {{ display: flex; align-items: center; gap: 6px; color: #ccc; font-size: 13px; }}
            .swatch {{ width: 14px; height: 14px; border-radius: 3px; border: 2px solid; display: inline-block; flex-shrink: 0; }}

            /* Tabs */
            .tabs {{
                display: flex;
                gap: 4px;
                margin-bottom: 0;
                align-self: flex-start;
                margin-left: calc(50% - {canvas_width // 2}px);
            }}
            .tab-btn {{
                padding: 8px 18px;
                border: 1px solid #555;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                background: #2e2e2e;
                color: #aaa;
                cursor: pointer;
                font-size: 13px;
                transition: background 0.15s, color 0.15s;
            }}
            .tab-btn:hover {{ background: #3a3a3a; color: #eee; }}
            .tab-btn.active {{ background: #2a2a2a; color: #fff; border-color: #666; }}

            /* Canvas */
            .page-canvas {{
                position: relative;
                background: #2a2a2a;
                border: 1px solid #666;
                overflow: visible;
            }}
            .page-canvas.hidden {{ display: none; }}

            /* Groups */
            .group-container {{
                position: absolute;
                border: 1px dashed #888;
                border-radius: 6px;
            }}
            body.hide-groups .group-container {{
                border-color: transparent;
            }}

            /* Groups-only mode */
            body.groups-only .element {{ display: none; }}
            body.groups-only .group-container .group-container {{ visibility: hidden; }}
            body.groups-only .group-container[data-depth="0"] {{
                border: 2px solid #aaa;
                border-radius: 6px;
                background: #ffffff18;
            }}

            /* Elements */
            .element {{
                position: absolute;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
            }}
            .element span {{
                font-size: 11px;
                font-weight: 600;
                color: #fff;
                text-shadow: 0 1px 3px #000;
                pointer-events: none;
                user-select: none;
            }}
            </style>
            </head>
            <body>
            <h2>Power BI Layout Preview &nbsp;<small>{canvas_width} × {canvas_height} px</small></h2>
            <div class="legend">{legend_items}</div>
            <div style="display:flex;align-items:center;justify-content:space-between;width:{canvas_width}px;margin-bottom:8px;">
              <div class="tabs" style="margin-left:0;">
              {tab_buttons}
              </div>
              <div style="display:flex;gap:8px;">
                <button id="toggle-groups" onclick="toggleGroups()" style="padding:6px 14px;border:1px solid #666;border-radius:6px;background:#2e2e2e;color:#ccc;cursor:pointer;font-size:12px;">Hide Groups</button>
                <button id="toggle-groups-only" onclick="toggleGroupsOnly()" style="padding:6px 14px;border:1px solid #666;border-radius:6px;background:#2e2e2e;color:#ccc;cursor:pointer;font-size:12px;">Groups Only</button>
              </div>
            </div>
            {canvases}
            <script>
            function showPage(idx) {{
                document.querySelectorAll('.page-canvas').forEach((el, i) => {{
                    el.classList.toggle('hidden', i !== idx);
                }});
                document.querySelectorAll('.tab-btn').forEach((btn, i) => {{
                    btn.classList.toggle('active', i === idx);
                }});
            }}
            function toggleGroups() {{
                const hidden = document.body.classList.toggle('hide-groups');
                document.getElementById('toggle-groups').textContent = hidden ? 'Show Groups' : 'Hide Groups';
            }}
            function toggleGroupsOnly() {{
                const on = document.body.classList.toggle('groups-only');
                document.getElementById('toggle-groups-only').textContent = on ? 'Show All' : 'Groups Only';
                document.getElementById('toggle-groups-only').style.color = on ? '#fff' : '#ccc';
                document.getElementById('toggle-groups-only').style.borderColor = on ? '#aaa' : '#666';
                // Disable the hide-groups toggle while groups-only is active
                document.getElementById('toggle-groups').disabled = on;
                document.getElementById('toggle-groups').style.opacity = on ? '0.4' : '1';
            }}
            </script>
            </body>
            </html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Layout HTML saved to: {output_path}")

    layout_data, canvas_width, canvas_height = extract_layout()
    # print(layout_data)
    generate_layout_html(layout_data, canvas_width, canvas_height)
        
else:
    print("No Layout found")