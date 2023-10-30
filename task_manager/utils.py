### library
class Point:
  def __init__(self, x=0, y=0):
    self.x = x
    self.y = y
  def get_str(self):
    return str(self.x)+","+str(self.y)
