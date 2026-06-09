class Thruster :
    def __init__(self, filepath):
        self.filepath = filepath
        self.impulse = 0
        self.mass = 0
    
    def getImpulse(self):
        return self.impulse
    
    def getMass(self):
        return self.getMass

    



class Rocket :
    from calculations import Thruster
    def __init__(self, mass, frontalArea, thruster):
        self.mass = mass
        self.frontalArea = frontalArea
        self.thruster = thruster

    def getAccel(self):
        return self.thruster

        
