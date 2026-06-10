import math
import json

class Thruster :
    def __init__(self, filepath):
        self.filepath = filepath
        self.impulse = 10
        self.mass = 10
    
    def getImpulse(self):
        return self.impulse
    
    def getMass(self):
        return self.mass
    
    def getModel(self):
        return self.filepath


class NoseCone :
    def __init__(self, shapeType, material, height):
        self.shapeType = shapeType
        self.material = material
        self.height = height
        with open("materials.json", "r") as f:
            materials_db = json.load(f)
        

        density = materials_db.get(self.material, 680.0)
        

        slant_height = math.sqrt(self.radius**2 + self.height**2)
        surface_area = math.pi * self.radius * slant_height
        volume = surface_area * self.wall_thickness
        

        self.mass = density * volume
       

    def getDrag(self):
        return 0
    
    def getMass(self):
        return self.mass

class BodyTube :
    def __init__(self, material, height, radius, wallThickness):
        self.material = material
        self.height = height
        self.radius = radius
        self.wallThickness = wallThickness

        with open("materials.json", "r") as f:
            materials_db = json.load(f)
            
        density = materials_db.get(self.material, 680.0)
        
        r_outer = self.radius
        r_inner = r_outer - self.wallThickness
        volume = math.pi * (r_outer**2 - r_inner**2) * self.height

        self.mass = density * volume

    def getDrag(self):
        return 0
    
    def getMass(self):
        return self.mass
    
class Fins :
    def __init__(self, material, count, thickness, root_chord, tip_chord, semi_span, isSanded):
        self.material = material.lower()
        self.count = count                    
        self.thickness = thickness              
        self.root_chord = root_chord            
        self.tip_chord = tip_chord              
        self.semi_span = semi_span              
        self.isSanded = isSanded
        
        with open("materials.json", "r") as f:
            materials_db = json.load(f)
            
        density = materials_db.get(self.material, 160.0)
        
        single_fin_surface_area = 0.5 * (self.root_chord + self.tip_chord) * self.semi_span
        total_volume = (single_fin_surface_area * self.thickness) * self.count
        
        self.mass = density * total_volume
    



class Rocket :
    def __init__(self, mass, thruster, noseCone, bodyTube, fins):
        self.mass = mass
        self.thruster = thruster
        self.noseCone = noseCone
        self.bodyTube = bodyTube
        self.fins = fins

    def getTotalMass(self):
        return self.mass + self.thruster.getMass() + self.noseCone.getMass() + self.bodyTube.getMass() + self.fins.getMass()

    def getAccel(self):
        return self.thruster

        
