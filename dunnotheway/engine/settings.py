import json
import os

from common.settings import BASE_DIR


# load config file
CONFIG_PATH = os.path.join(BASE_DIR, 'engine', 'config.json')
with open(CONFIG_PATH) as f:
    config = json.load(f)


NUMBER_ENTRIES_PER_SECTION = config['NUMBER_ENTRIES_PER_SECTION'] # NUMBER OF POINTS PER SECTIONS 
NUMBER_SECTIONS = config['NUMBER_SECTIONS'] # NUMBER OF SECTIONS TO BUILD REPORT

MIN_NUMBER_SAMPLES = config["MIN_NUMBER_SAMPLES"]
MAXIMUM_DISTANCE_BETWEEN_SAMPLES = config["MAXIMUM_DISTANCE_BETWEEN_SAMPLES"]
