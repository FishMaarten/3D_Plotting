import math

class Vertex:
    def __init__(self, x:float=0, y:float=0, z:float=0):
        self.x, self.y, self.z = float(x),float(y),float(z)
        self.xyz = (self.x, self.y, self.z)
        
    def __repr__(self): return str(self.xyz)
    def __add__(self, other):
        return Vertex(self.x +other.x, self.y +other.y, self.z +other.z)
    def __sub__(self, other):
        return Vertex(self.x -other.x, self.y -other.y, self.z -other.z)
    def scale(self, scalar):
        return Vertex(self.x /scalar, self.y /scalar, self.z /scalar)
    @classmethod
    def z_axis(cls, height): return Vertex(0,0,height)

class Mesh:
    def __init__(self, verts=[], edges=[], faces=[]):
        if type(verts[0]) != Vertex:
            for idx, vertex in enumerate(verts):
                verts[idx] = Vertex(*vertex)
        self.verts, self.edges, self.faces = verts, edges, faces
        self.tuple = (self.verts, self.edges, self.faces)
        self.data = ([v.xyz for v in self.verts], self.edges, self.faces)
    def __str__(self):
        return "\n".join(["verts: " + ", ".join([str(v) for v in self.verts]),
                          "edges: " + ", ".join([str(e) for e in self.edges]),
                          "faces: " + ", ".join([str(f) for f in self.faces])])
class Grid(Mesh):
    def __init__(self, heightmap:{}):
        verts = []
        edges = []
        faces = []
        size_x, size_y = len(heightmap["0"]), len(heightmap)
        for y, row in heightmap.items():
            for x, height in enumerate(row):
                length = len(heightmap) # WIDTH HEIGHT !!!
                idx = int(y) * size_x + x
                verts.append(Vertex(x, int(y), height))
                if x < size_x -1 and int(y) < size_y -1:
                    faces.append([idx, idx+1, idx+size_x +1, idx+size_x])
        Mesh.__init__(self, verts, edges, faces)

class Rectangle(Mesh):
    def __init__(self, width:float=1, height:float=1, center=Vertex()):
        self.width, self.height = width, height
        self.diagonal = math.sqrt(width**2 + height**2)
        verts=[Vertex(center.x-width/2, center.y-height/2, 0),
               Vertex(center.x+width/2, center.y-height/2, 0),
               Vertex(center.x+width/2, center.y+height/2, 0),
               Vertex(center.x-width/2, center.y+height/2, 0)]
        edges=[(0,1),(1,2),(2,3),(3,0)]
        faces=[[0,1,2,3]]   
        Mesh.__init__(self, verts, edges, faces)

class Square(Rectangle):
    def __init__(self, size:float=1, center=Vertex()):
        Rectangle.__init__(self, size, size, center)

class Ngon(Mesh):
    def __init__(self, verts=[]):
        edges = [(idx, idx+1) for idx, v in enumerate(verts[:-1])]
        edges.append((len(verts)-1, 0))
        faces=[[i for i in range(len(verts))]]
        Mesh.__init__(self, verts, edges, faces)

class Circle(Ngon):
    def __init__(self, radius:float=1, center=Vertex(), count:int=32):
        verts = []
        delta = 2 * math.pi / count 
        theta = 0.0
        for i in range(count):
            theta += delta
            verts.append(Vertex(radius * math.cos(theta), radius * math.sin(theta)))
        Ngon.__init__(self, verts)

class Hexagon(Circle):
    def __init__(self, length:float=1, center=Vertex()):
        Circle.__init__(self, length, center, 6)

class Prism(Mesh):
    def __init__(self, mesh:Mesh, height:float=1):
        z_trans = Vertex(0,0,height)
        verts, edges, faces = mesh.tuple
        vert_count = len(verts)
        verts.extend([vert+z_trans for vert in verts])
        edges.extend([(idx, idx+1) for idx in range(vert_count, vert_count*2 -1)])
        edges.append((vert_count*2-1, vert_count))
        faces.append([idx for idx in range(vert_count, vert_count*2)])
        faces.extend([idx, idx+1, idx+vert_count+1, idx+vert_count] for idx in range(vert_count -1))
        faces.append([vert_count -1, 0, vert_count, vert_count*2 -1])
        Mesh.__init__(self, verts, edges, faces)

class Cube(Prism):
    def __init__(self, size:float=1):
        Prism.__init__(self, Square(size), size)

class Cylinder(Prism):
    def __init__(self, circle=Circle(), height:float=1):
        Prism.__init__(self, circle, height)

class Pyramid(Mesh):
    def __init__(self, base:Mesh=Square(), size:float=1, origin=Vertex()):
        verts, edges, faces = base.tuple
        vert_count = len(verts)
        diagonal = base.diagonal
        height = math.sqrt(size**2 - (diagonal/2)**2)
        verts.append(Vertex(0, 0, height))
        edges.extend([(idx, vert_count) for idx in range(vert_count -1)])
        edges.append((vert_count-1, vert_count))
        faces.extend([[idx, idx+1, vert_count]for idx in range(vert_count -1)])
        faces.append([vert_count-1, 0, vert_count])
        Mesh.__init__(self, verts, edges, faces)

if __name__ == "__main__":
    data = {0: [1,2,3,4],
            1: [1,2,3,4],
            2: [1,2,3,4],
            3: [1,2,3,4]}
    test = Grid(data)
    print(test)
    pass
