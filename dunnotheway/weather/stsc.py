import time
import requests

class ConvectionCells:
    '''Class representation of a Convection Cell'''
    def __init__(self, id, latitude, longitude, radius):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        # self.timestamp = timestamp

    def __hash__(self):
        return hash((self.latitude, self.longitude, self.radius))

    def __eq__(self, other):
        return (self.latitude == other.latitude and
                self.longitude == other.longitude and
                self.radius == other.radius)
    
    def __repr__(self):
        return 'ConvectionCell({0}, {1}, {2})'.format(
            self.latitude, self.longitude, self.radius)

class STSC:
    '''Class to communicate with STSC API'''

    def __init__(self):
        self._url = 'https://www.redemet.aer.mil.br/stsc/public/produto/dados'
        self._convection_cells = set()

    @property
    def convection_cells(self):
        try:
            self._update_convection_cells()
        except requests.exceptions.RequestException:
            pass # TODO: Log Error Message
        return self._convection_cells 

    def _update_convection_cells(self):
        events = self._get_request_response()
        for cell_id, event in events.items():
            try:
                cell = self._create_convection_cell(cell_id, event)
                self._convection_cells.add(cell)
            except KeyError:
                pass # TODO: Log Error Message
                
    def _get_request_response(self):
        r = requests.get(self._url)
        return r.json()
        
    def _create_convection_cell(self, cell_id, event):
            cell = event['0']
            return ConvectionCells(cell_id, 
                        float(cell['Latitude']),
                        float(cell['Longitude']),
                        float(cell['Raio']))

if __name__ == '__main__':
    client = STSC()
    start = time.time()
    _ = client.convection_cells
    end = time.time()
    print('retrieval time (in seconds) -', end-start)
