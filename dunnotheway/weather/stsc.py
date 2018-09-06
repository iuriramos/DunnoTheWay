import time
import requests
from convection_cell import ConvectionCell


class STSC:
    '''Class to communicate with STSC API'''
    UPDATE_INTERVAL_IN_SECS = 300 # 5 MINUTES

    def __init__(self):
        self._url = 'https://www.redemet.aer.mil.br/stsc/public/produto/dados'
        self._cells = set()
        self._bbox_to_cells = {}
        self._updated_at = 0 # timestamp

    @property
    def convection_cells(self):
        self._update_cells()
        return list(self._cells) 

    def convection_cells_within_bounding_box(self, bbox):
        self._update_cells()
        if bbox not in self._bbox_to_cells:
            cells = self._filter_cells_by_bounding_box(self._cells, bbox)
            cells = sorted(cells, key=lambda cell: (cell.longitude, cell.latitude))
            self._bbox_to_cells[bbox] = cells
        return self._bbox_to_cells[bbox]
    
    def _filter_cells_by_bounding_box(self, cells, bbox):
        min_latitude, max_latitude, min_longitude, max_longitude = bbox
        
        def cell_within_bbox(cell):
            return (min_latitude <= cell.latitude <= max_latitude and
                    min_longitude <= cell.longitude <= max_longitude)
        bbox_cells = []
        for cell in cells:
            if cell_within_bbox(cell):
                bbox_cells.append(cell)
        return bbox_cells

    def _update_cells(self):
        now = time.time()
        if now - self._updated_at > self.UPDATE_INTERVAL_IN_SECS:        
            try:
                events = self._get_request_response()
                for cell_id, event in events.items():
                    try:
                        cell = self._create_cell(cell_id, event)
                        self._cells.add(cell)
                    except KeyError:
                        pass # TODO: Log Error Message
                # set new timestamp and empty cache
                self._updated_at = now
                self._bbox_to_cells = {}
            except requests.exceptions.RequestException:
                pass # TODO: Log Error Message

    def _get_request_response(self):
        r = requests.get(self._url)
        return r.json()
        
    def _create_cell(self, cell_id, event):
            cell = event['0']
            return ConvectionCell(
                float(cell['Latitude']),
                float(cell['Longitude']),
                float(cell['Raio']))

if __name__ == '__main__':
    client = STSC()
    start = time.time()
    _ = client.convection_cells
    end = time.time()
    print('retrieval time (in seconds) -', end-start)
