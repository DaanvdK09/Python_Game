import csv
import pygame
from constants import BG, WALL

class TileMap:
    def __init__(self, layout=None, tile_size=64, solid_ids=(1,)):
        self.tile_size = tile_size
        self.solid_ids = set(solid_ids)
        if layout is None:
            layout = [
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1],
                [1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1,1,1,1,0,0,0,0,0,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            ]
        self.layout = layout

        self.color_map = {
            0: (BG),   #floor
            1: (WALL) #wall
        }

    @classmethod
    def from_csv(cls, path, tile_size=48, solid_ids=(1,)):
        layout = []
        with open(path, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                layout.append([int(x) for x in row])
        return cls(layout=layout, tile_size=tile_size, solid_ids=solid_ids)

    @property
    def width(self):
        return len(self.layout[0]) * self.tile_size

    @property
    def height(self):
        return len(self.layout) * self.tile_size

    def draw(self, surface, offset_x=0, offset_y=0):
        """Draw tiles. offset_x/y can be used for camera later."""
        for y, row in enumerate(self.layout):
            for x, tid in enumerate(row):
                color = self.color_map.get(tid, (255,0,255))
                rect = pygame.Rect(x * self.tile_size + offset_x, y * self.tile_size + offset_y,
                                   self.tile_size, self.tile_size)
                pygame.draw.rect(surface, color, rect)

    def get_solid_rects(self):
        """Return list of pygame.Rect for solid tiles."""
        rects = []
        for y, row in enumerate(self.layout):
            for x, tid in enumerate(row):
                if tid in self.solid_ids:
                    rects.append(pygame.Rect(x * self.tile_size, y * self.tile_size,
                                             self.tile_size, self.tile_size))
        return rects