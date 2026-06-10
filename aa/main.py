import math
from calculations import Thruster, Rocket


motor = Thruster("hi")
r1 = Rocket(mass=100, frontalArea=30, thruster=motor)

print(motor.getModel())
print(r1.getTotalMass())



