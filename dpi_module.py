NAME = "dpi_module"

import json

def load_structure_data(path_to_file, file_name):
    
    with open (path_to_file + "/" + file_name, "r", encoding='utf-8') as file: 
        data = json.load(file) # зависимость процента премии от грейда

    return data
