import random

class Sensor(object):

    def __init__(self, value, error=0):
        self.value = value
        self.error = error

    def set(self, value):
        self.value = value + random.gauss(0, self.error)

    def update(self, latest_measurement):
        pass

    def get(self):
        return self.value


class DeltaSensor(Sensor):

    def __init__(self, value, error=0):
        Sensor.__init__(self, value, error)
        self.last = value

    def update(self, latest_measurement):
        self.set(latest_measurement - self.last)
        self.last = latest_measurement


class Sensors(object):

    def __init__(self, ship, base_error=0):
        self.ship = ship
        self.x_vel = DeltaSensor(ship.pos[0], base_error)
        self.y_vel = DeltaSensor(ship.pos[1], base_error)
        self.rot = DeltaSensor(ship.rot, base_error)

    def update(self):
        self.x_vel.update(self.ship.pos[0])
        self.y_vel.update(self.ship.pos[1])
        self.rot.update(self.ship.rot)
