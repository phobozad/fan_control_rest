
import bottle

from fan_control import FanController

class App:
    def __init__(self, dataPin):
        self.FanController = FanController(dataPin)

        self.Server = bottle.Bottle()
        self._setup_routes()

    def _setup_routes(self):
        route_map = [
                {"method": "GET", "path": "/", "handler": self._index_page},
                {"method": "POST", "path": "/api/command/<address:int>/<command>", "handler": self._send_command_handler}
        ]

        for route in route_map:
            self.Server.route(route['path'], method=route['method'], callback=route['handler'])

    def _index_page(self):
        return("Hi :) \n Fan Controller API")

    def _send_command_handler(self, address: int, command: str):

        result = self.FanController.send_command(address, command)

        if not result:
            bottle.response.status = 400
            bottle.response.content_type = "application/json"
            return "{'error': 'Invalid address or command provided'}\n"

        bottle.response.status = 204
        return
