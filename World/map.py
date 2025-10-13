import pygame
from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer

class TileMap:
    def __init__(self, tmx_path=None, tile_size=64):
        self.tmx = None
        self.tilewidth = tile_size
        self.tileheight = tile_size
        self.tile_size = tile_size
        self.width = 0
        self.height = 0
        self.collision_rects = []
        self.player_start = None
        if tmx_path:
            self.load_tmx(tmx_path)

    def load_tmx(self, tmx_path):
        self.tmx = load_pygame(tmx_path)
        self.tilewidth = self.tmx.tilewidth
        self.tileheight = self.tmx.tileheight
        self.tile_size = self.tilewidth
        self.width = self.tmx.width * self.tilewidth
        self.height = self.tmx.height * self.tileheight

        self.collision_rects = []

        def _gid_to_int(gid):
            try:
                return int(gid)
            except Exception:
                return None

        for layer in self.tmx.visible_layers:
            if hasattr(layer, "tiles"):
                is_collision_layer = getattr(layer, "name", "") and getattr(layer, "name", "").lower() == "collision"
                for x, y, gid in layer.tiles():
                    gid_int = _gid_to_int(gid)
                    if gid_int is None:
                        if is_collision_layer:
                            r = pygame.Rect(x * self.tilewidth, y * self.tileheight,
                                            self.tilewidth, self.tileheight)
                            self.collision_rects.append(r)
                        continue

                    if gid_int == 0:
                        continue

                    props = self.tmx.get_tile_properties_by_gid(gid_int) or {}
                    if props.get("collide") or props.get("blocked") or is_collision_layer:
                        r = pygame.Rect(x * self.tilewidth, y * self.tileheight,
                                        self.tilewidth, self.tileheight)
                        self.collision_rects.append(r)

            if hasattr(layer, "objects"):
                layer_name = getattr(layer, "name", "").lower() if getattr(layer, "name", None) else ""
                for obj in layer.objects:
                    if layer_name == "collision" or (getattr(obj, "name", "").lower() == "collision") or (getattr(obj, "type", "").lower() == "collision"):
                        r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                        self.collision_rects.append(r)

                    if (getattr(obj, "name", "").lower() == "player"
                            or getattr(obj, "type", "").lower() == "player"):
                        self.player_start = (int(obj.x), int(obj.y))

        for obj in getattr(self.tmx, "objects", []):
            if (getattr(obj, "name", "").lower() == "collision"
                    or getattr(obj, "type", "").lower() == "collision"):
                r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                self.collision_rects.append(r)
            if (getattr(obj, "name", "").lower() == "player"
                    or getattr(obj, "type", "").lower() == "player"):
                self.player_start = (int(obj.x), int(obj.y))

        print(f"TileMap: built {len(self.collision_rects)} collision rects from '{tmx_path}'")

    def get_solid_rects(self):
        return self.collision_rects

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.tmx:
            return
        for layer in self.tmx.visible_layers:
            layer_name = getattr(layer, "name", "") or ""
            layer_props = getattr(layer, "properties", {}) or {}
            if layer_name.lower() == "collision" or layer_props.get("collision") is True:
                continue
            if hasattr(layer, "tiles"):
                for x, y, gid in layer.tiles():
                    tile = None
                    if isinstance(gid, pygame.Surface):
                        tile = gid
                    else:
                        try:
                            tile = self.tmx.get_tile_image_by_gid(gid)
                        except Exception:
                            tile = None

                    if tile:
                        surface.blit(tile, (x * self.tilewidth + offset_x,
                                            y * self.tileheight + offset_y))