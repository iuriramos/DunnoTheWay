import sys
sys.path.append('/home/iuri/workspace/dunnotheway/dunnotheway')

import time
import requests
from common.utils import from_timestamp_to_datetime
from weather.models.convection_cell import ConvectionCell
# from flight.models.airport import Airport


class STSC:
    '''Class to communicate with STSC API'''
    UPDATE_INTERVAL_IN_SECS = 300 # 5 MINUTES

    def __init__(self):
        self._url = 'https://www.redemet.aer.mil.br/stsc/public/produto/dados'
        self._cells = set()
        self._bbox_to_cells = {}
        self._updated_at = 0 # timestamp
        self._has_changed = False

    # def cells_from_airports(self, departure_airport, destination_airport):
    #     bbox = Airport.bounding_box_related_to_airports(departure_airport, destination_airport)
    #     return self.cells_within_bounding_box(bbox)

    @property
    def has_changed(self):
        self.cells
        _has_changed = self._has_changed
        self._has_changed = False # careful with this!
        return _has_changed
    
    def cells_within_bounding_box(self, bbox, sorting_key=None, sorting_reverse=False):
        if bbox not in self._bbox_to_cells:
            cells = self._filter_cells_by_bounding_box(self.cells, bbox)
            cells = sorted(cells, key=sorting_key, reverse=sorting_reverse)
            self._bbox_to_cells[bbox] = cells
        return self._bbox_to_cells[bbox]

    def _filter_cells_by_bounding_box(self, cells, bbox):
        
        def cell_within_bbox(cell):
            return (bbox.min_latitude <= cell.latitude <= bbox.max_latitude and
                    bbox.min_longitude <= cell.longitude <= bbox.max_longitude)
        
        bbox_cells = []
        for cell in cells:
            if cell_within_bbox(cell):
                bbox_cells.append(cell)
        return bbox_cells

    @property
    def cells(self):
        now = time.time()
        if now - self._updated_at > self.UPDATE_INTERVAL_IN_SECS:
            if self._update_cells(): 
                # set new timestamp and empty cache
                self._bbox_to_cells = {}
                self._updated_at = now
                self._has_changed = True
        return self._cells

    def _update_cells(self):
        cells = set()
        
        try:
            events = self._get_request_response()
            for cell_id, event in events.items():
                try:
                    cell = self._create_cell(cell_id, event)
                    cells.add(cell)
                except KeyError:
                    return False
        except requests.exceptions.RequestException:
            return False
        
        # retrieved the cells successfully
        _has_changed = (self._cells != cells)
        self._cells = cells
        return _has_changed

    def _get_request_response(self):
        r = requests.get(self._url)
        return r.json()
        
    def _create_cell(self, cell_id, event):
            cell = event['0']
            return ConvectionCell(
                float(cell['Latitude']),
                float(cell['Longitude']),
                float(cell['Raio']),
                from_timestamp_to_datetime(time.time()))

if __name__ == '__main__':
    client = STSC()
    start = time.time()
    cells = client.cells
    end = time.time()
    print (cells)
    print('retrieval time (in seconds) -', end-start)
