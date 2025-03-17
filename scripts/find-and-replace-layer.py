import arcpy
import PySimpleGUI as sg
from GlendaleTools import glendale_tools as tools
from arcgis.gis import GIS
from arcgis.map import Map


#portal_url, username, password = tools.portal_creds()
gis = GIS(tools.portal_creds()[0], tools.portal_creds()[1], tools.portal_creds()[2])

def main():
    """
    Main function to search and replace layers in web maps and web mapping applications.
    """
    print(f"Logged into {arcpy.GetActivePortalURL()} as {gis.properties['user']['username']}")

    # Get user inputs for the services using PySimpleGUI
    sg.LOOK_AND_FEEL_TABLE['CustomTheme'] = {
        'BACKGROUND': '#FFFFFF',
        'TEXT': '#000000',
        'INPUT': '#FFFFFF',
        'TEXT_INPUT': '#ee5238',
        'SCROLL': '#FFFFFF',
        'BUTTON': ('#FFFFFF', '#ee5238'),
        'PROGRESS': sg.DEFAULT_PROGRESS_BAR_COLOR,
        'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0
        }
    sg.theme('CustomTheme')
    image = r'.\exchange.png'
    layout = [
        [sg.Image(image)],
        [sg.Text('URL TO REPLACE:')],
        [sg.InputText(key='-TARGET-')],
        [sg.Text('NEW URL:')],
        [sg.InputText(key='-NEW-')],
        [sg.Submit(), sg.Cancel()]
    ]

    window = sg.Window('Service Replacement', layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Cancel':
            break
        elif event == 'Submit':
            target_service = values['-TARGET-']
            new_service = values['-NEW-']
            if not target_service or not new_service:
                sg.popup_error('Both target service and new service must be specified.')
            else:
                window.close()
                search_and_replace_web_maps(target_service, new_service)
                search_and_replace_web_apps(target_service, new_service)
                sg.popup('Search and replace complete!')
                break

    window.close()

def search_and_replace_web_maps(target_service, new_service):
    """
    Searches for layers in web maps that match the target service and replaces them with the new service.
    """
    layer_out_file = r".\out-files\layer-out-file.txt"
    with open(layer_out_file, "a+") as out_file:
        out_file.write('#######STARTING THE SEARCH######\n')
        print(f'Searching web maps in {arcpy.GetActivePortalURL()}')
        web_maps = gis.content.search(query="", item_type="Web Map", max_items=10000)
        print(web_maps)
        for item in web_maps:
            #print(item)
            gis_item = gis.content.get(item.id)
            web_map = Map(item=gis_item)
            print(web_map.content.layers)
            try:
                layers = web_map.content.layers
                print(layers)
                updated = False
                layer_finder = ['VectorTileLayer', 'FeatureLayer', 'MapImageLayer']
                for layer in layers:
                    try:
                        if layer['layerType'] in layer_finder and target_service.lower() in layer.styleUrl.lower():
                            layer.styleUrl = new_service
                            updated = True
                            print(f"Updated {item.title} | {layer.styleUrl}")
                        elif target_service.lower() == layer.url.lower():
                            layer.url = new_service
                            updated = True
                            print(f"Updated {item.title} | {layer.url}")
                    except Exception as e:
                        print(f"Error processing layer: {str(e)}")
                if updated:
                    web_map.update()
                    out_file.write(f"Updated web map: {item.title} \n")
            except:
                print('big fail')
            
            
        
        print('Web map search and replace complete')

def search_and_replace_web_apps(target_service, new_service):
    """
    Searches for layers in web mapping applications that match the target service and replaces them with the new service.
    """
    print(f'Searching web app configured searches in {arcpy.GetActivePortalURL()}')
    web_apps = gis.content.search(query='', item_type='Web Mapping Application', max_items=10000)
    
    for app in web_apps:
        try:
            app_data = app.get_data()
            widgets = app_data.get('widgetOnScreen', {}).get('widgets', []) + app_data.get('widgetPool', {}).get('widgets', [])
            updated = False
            
            for widget in widgets:
                if 'uri' in widget and widget['uri'] == 'widgets/Search/Widget':
                    for source in widget['config']['sources']:
                        if target_service.lower() in source['url'].lower() and 'searchFields' in source:
                            source['url'] = new_service
                            updated = True
                            search_fields = ", ".join(source['searchFields'])
                            print(f"Updated {app.title} | {source['url']} | Searching on: {search_fields}")
            
            if updated:
                app.update(data=app_data)
        except Exception as e:
            arcpy.AddWarning(f"Error processing app: {str(e)}")
    
    print('Web app search and replace complete')

if __name__ == '__main__':
    main()
