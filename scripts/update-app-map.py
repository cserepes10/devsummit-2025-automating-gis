import time
import urllib3
import threading
from arcgis.gis import GIS
from datetime import datetime, timedelta
from GlendaleTools import glendale_tools as tools

def main():
    agol_login = tools.agol_creds()
    portal_login = tools.portal_creds()
    creds = [agol_login, portal_login]

    threads = []
    for i in range(len(creds)):
        if i == 1: 
            portal = True
        else: 
            portal = False
        thread = threading.Thread(target=update_descriptions, args=(creds[i], portal))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

def application_webmap_finder(map_id, item_list, gis, push_descriptions):
    for item in item_list:
        app_to_update = gis.content.get(item.id)
        if not app_to_update:
            continue

        app_json = app_to_update.get_data()
        if map_id in str(app_json):
            #description = f"{app_to_update.description}\n{push_descriptions}"
            description = f"{push_descriptions}"
            props = {
                "title": app_to_update.title,
                "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/a7857db7f6bc47dab80ab529a91a0a2e/data",
                "description": description,
                "overwrite": True
            }
            #print(description)
            try:
                app_to_update.update(item_properties=props)
                
            except:
                pass
def application_finder(map_id, gis, push_descriptions, query):
    item_types = ['Dashboard', 'Application', 'Web Mapping Application']
    for item_type in item_types:
        try:
            app_items = gis.content.search(query=query, item_type=item_type, max_items=1000)
            application_webmap_finder(map_id, app_items, gis, push_descriptions)
        except Exception as e:
            print(f"Error searching for {item_type}: {e}")

def group_layer_dealer(group_layers):
    return (
        f'<div style="padding: 10px; margin-top: 10px;">'
        f'<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);">'
        f'<a href="{group_layers["url"]}" target="_blank" style="text-decoration: none; color: #0078d4;">'
        f'<h5 style="margin: 0; font-size: 14px;">{group_layers["title"]}</h5>'
        f'<p style="margin: 5px 0; font-size: 12px; color: #666;">{group_layers["layerType"]}</p>'
        f'</a></div></div>'
    )

def layer_factory(data, web_map_item, portal):
    layer_description = []
    group_list = []

    for layer in data:
        if layer['layerType'] == 'GroupLayer':
            try:
                for grp_lyr in layer['layers']:
                    group_list.append(group_layer_dealer(grp_lyr))
                group_layers_described = (
                    f'<details style="border: 1px solid #ccc; padding: 10px; border-radius: 5px;">'
                    f'<summary style="cursor: pointer; font-size: 16px; font-weight: bold; padding: 10px; background-color: #0078d4; color: white; border-radius: 5px;">Group Layers</summary>'
                    f'<div style="padding: 10px; margin-top: 10px;">{"".join(group_list)}</div></details>'
                )
            except Exception as e:
                print(f"Error processing GroupLayer: {e}")

        else:
            try:
                if portal == True:
                    map_text = (
                        f'<div style="padding: 10px; margin-top: 10px;">'
                        f'<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);">'
                        f'<a href="https://gismaps.glendaleaz.com/gisportal/apps/mapviewer/index.html?webmap={web_map_item.id}" target="_blank" style="text-decoration: none; color: #0078d4;">'
                        f'<h5 style="margin: 0; font-size: 14px;">{web_map_item.title}</h5>'
                        f'<p style="margin: 5px 0; font-size: 12px; color: #666;">WebMap</p>'
                        f'</a></div></div>'
                    )
                else:
                    map_text = (
                        f'<div style="padding: 10px; margin-top: 10px;">'
                        f'<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);">'
                        f'<a href="https://cog-gis.maps.arcgis.com/apps/mapviewer/index.html?webmap={web_map_item.id}" target="_blank" style="text-decoration: none; color: #0078d4;">'
                        f'<h5 style="margin: 0; font-size: 14px;">{web_map_item.title}</h5>'
                        f'<p style="margin: 5px 0; font-size: 12px; color: #666;">WebMap</p>'
                        f'</a></div></div>'
                    )
                layer_text = (
                    f'<div style="padding: 10px; margin-top: 10px;">'
                    f'<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);">'
                    f'<a href="{layer["url"]}" target="_blank" style="text-decoration: none; color: #0078d4;">'
                    f'<h5 style="margin: 0; font-size: 14px;">{layer["title"]}</h5>'
                    f'<p style="margin: 5px 0; font-size: 12px; color: #666;">{layer["layerType"]}</p>'
                    f'</a></div></div>'
                )
                layer_description.append(layer_text)
            except Exception as e:
                print(f"Error processing layer: {e}")

    layers_described = (
        f'<details style="border: 1px solid #ccc; padding: 10px; border-radius: 5px;">'
        f'<summary style="cursor: pointer; font-size: 16px; font-weight: bold; padding: 10px; background-color: #0078d4; color: white; border-radius: 5px;">Web Map</summary>'
        f'<div style="padding: 10px; margin-top: 10px;">{"".join(map_text)}</div></details>'
        f'<details style="border: 1px solid #ccc; padding: 10px; border-radius: 5px;">'
        f'<summary style="cursor: pointer; font-size: 16px; font-weight: bold; padding: 10px; background-color: #0078d4; color: white; border-radius: 5px;">Layers</summary>'
        f'<div style="padding: 10px; margin-top: 10px;">{"".join(layer_description)}</div></details>'
    )

    push_descriptions = layers_described
    if group_list:
        push_descriptions += f'{group_layers_described}'

    return push_descriptions

def update_descriptions(creds, portal):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    today = (datetime.now()).timestamp() * 1000 
    thirty_days_ago = (datetime.now() - timedelta(days=365)).timestamp() * 1000  # Convert to milliseconds
    # Create the query for items modified in the last 30 days
    query = f"modified: [{thirty_days_ago} TO {today}]"
    gis = GIS(url=creds[0], username=creds[1], password=creds[2])

    web_maps = gis.content.search(query=query, item_type="Web Map", max_items=10000)
    #web_maps = gis.content.search(query='', item_type="Web Map", max_items=9999)
    if not web_maps:
        print("No Web Maps found.")
        return

    threads = []
    for web_map_item in web_maps:
        thread = threading.Thread(target=process_web_map, args=(web_map_item, gis, portal, query))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

def process_web_map(web_map_item, gis, portal, query):
    try:
        data = web_map_item.get_data().get('operationalLayers', [])
        push_descriptions = layer_factory(data, web_map_item, portal)
        application_finder(web_map_item.id, gis, push_descriptions, query)
    except Exception as e:
        print(f"Error processing web map {web_map_item.id}: {e}")
        with open(r'./out-files/maps-to-delete.csv', '+a') as f:
            f.write(f'{web_map_item.id}, {portal}\n')
            
if __name__ == "__main__":
    main()