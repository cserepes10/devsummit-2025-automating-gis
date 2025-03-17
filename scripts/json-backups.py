import json
import urllib3
import threading
from queue import Queue
from arcgis.gis import GIS
from datetime import datetime
from GlendaleTools import glendale_tools as tools
def main():
    agol_login = tools.agol_creds()
    portal_creds = tools.portal_creds()
    creds = [agol_login, portal_creds]
    for i in range(len(creds)):
        backup_to_json(creds[i])
        hosted_data_backup(creds[i])

def backup_to_json(creds):
    #login to portal
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    gis = GIS(creds[0], creds[1], creds[2])
    #declare what you are item you are searching for. 
    item_list = ['dashboards', 'Web Map', 'Web Mapping Application', 'Web Experience']
    #destination folder name.
    folder_list = ['dashboard-backups', 'webmap-backups', 'webapp-backups', 'exp-backups']
    for a in range(len(item_list)):
        print('starting to find all the ' + item_list[a] + ' in your portal')
        #set max # of items returned from portal
        max = 9999
        #query all owners in portal, get itemid, limit search to integer stored in MAX_ITEMS_RETURNED .
        web_items = gis.content.search(query='owner:*', item_type=item_list[a], max_items = max)
        for b in range(len(web_items)):
            try:
                web_item_name = web_items[b]
                item_id= web_item_name.itemid
                item_2_json = gis.content.get(item_id) 
                json_data = item_2_json.get_data(try_json=True)
                with open (f'.\json-backups\{folder_list[a]}\{web_item_name.title}.json', "w") as file_handle: #Edit the folder location
                    file_handle.write(json.dumps(json_data))
            except Exception as e:
                tools.email_admin('jason-backups.py', error=e)

def export_and_download(jobs, gis, hosted_data_folder):
    while not jobs.empty():
        try:
            layer_item_id= jobs.get()
            
            string_time = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Get the item from ArcGIS Online
            item = gis.content.get(layer_item_id)
            print(item.tags)
            
            # Export the item to a file geodatabase
            export = item.export(f'{layer_item_id}_{string_time}', 'File Geodatabase')
            print(export.id)
            
            # Download the exported file geodatabase
            export_item = gis.content.get(export.id)
            export_item.download(save_path=hosted_data_folder)
            export_item.delete()

            print(f"Successfully exported and downloaded {layer_item_id}")
        except Exception as e:
            print(f"Error exporting or downloading {layer_item_id}: {str(e)}")
        finally:
            jobs.task_done()

def hosted_data_backup(creds):
    gis = GIS(creds[0], creds[1], creds[2])
    threads = []
    layer_item_ids = []
    max = 9999
    hosted_data_folder = r'.\hosted-data-folder'
    feature_collection = gis.content.search(query="Hosted Service", item_type="Feature Layer Collection", max_items=max)
    jobs = Queue()
    
    # Populate the job queue
    for item in feature_collection:
        try:
            print('building the layer_item_ids list')
            current_item_id = item.itemid
            layer_item_ids.append(current_item_id)
        except Exception as e:
            print('could not get layer item id')
            tools.email_admin('hosted_data_backup.py', e)
            continue
    
    for layer_item_id in layer_item_ids:
        jobs.put((layer_item_id))
    
    # Start worker threads
    for k in range(4):
        thread = threading.Thread(target=export_and_download, args=(jobs, gis, hosted_data_folder))
        threads.append(thread)
        thread.start()
    
    # Wait for all jobs to be completed
    jobs.join()
    
    # Ensure all threads complete
    for thread in threads:
        thread.join()



if __name__ == "__main__":
    main()