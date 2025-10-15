import pygame
from pytmx.util_pygame import load_pygame

class TileMap:
    def __init__(self, tmx_path=None, tile_size=64):
        self.tmx = None
        self.tilewidth = tile_size
        self.tileheight = tile_size
        self.tile_size = tile_size
        self.width = 0
        self.height = 0
        self.collision_rects = []
        self.bush_rects = []
        self.player_start = None

        if tmx_path:
            self.load_tmx(tmx_path)

    def load_tmx(self, tmx_path):
        try:
            self.tmx = load_pygame(tmx_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load TMX '{tmx_path}': {e}") from e

        self.tilewidth = getattr(self.tmx, "tilewidth", self.tile_size)
        self.tileheight = getattr(self.tmx, "tileheight", self.tile_size)
        self.tile_size = self.tilewidth
        self.width = getattr(self.tmx, "width", 0) * self.tilewidth
        self.height = getattr(self.tmx, "height", 0) * self.tileheight

        self.collision_rects = []
        self.bush_rects = []

        def _gid_to_int(gid):
            try:
                return int(gid)
            except Exception:
                return None

        def _safe_lower(val):
            return (val or "").lower()

        print(f"Layers found: {[getattr(layer, 'name', None) for layer in self.tmx.visible_layers]}")

        for layer in self.tmx.visible_layers:
            layer_name = _safe_lower(getattr(layer, "name", None))
            layer_props = getattr(layer, "properties", {}) or {}

            # --- Tile-based layers (for collisions etc.) ---
            if hasattr(layer, "tiles"):
                is_collision_layer = layer_name == "collision" or layer_props.get("collision") is True

                for x, y, gid in layer.tiles():
                    gid_int = _gid_to_int(gid)
                    if gid_int is None:
                        if is_collision_layer:
                            r = pygame.Rect(
                                x * self.tilewidth, y * self.tileheight,
                                self.tilewidth, self.tileheight
                            )
                            self.collision_rects.append(r)
                        continue

                    if gid_int == 0:
                        continue

                    props = self.tmx.get_tile_properties_by_gid(gid_int) or {}
                    if props.get("collide") or props.get("blocked") or is_collision_layer:
                        r = pygame.Rect(
                            x * self.tilewidth, y * self.tileheight,
                            self.tilewidth, self.tileheight
                        )
                        self.collision_rects.append(r)

            # --- Object layers (for bushes, player, etc.) ---
            if hasattr(layer, "objects"):
                for obj in layer:
                    name = _safe_lower(getattr(obj, "name", None))
                    otype = _safe_lower(getattr(obj, "type", None))

                    # Bush detection
                    if name == "bush" or otype == "bush":
                        r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                        self.bush_rects.append(r)
                        print(f"🌿 Added bush rect: {r}")

                    # Player start detection
                    if name == "player" or otype == "player":
                        self.player_start = (int(obj.x), int(obj.y))
                        print(f"🧍 Player start position set to: {self.player_start}")

        print(f"TileMap built {len(self.collision_rects)} collision rects and {len(self.bush_rects)} bush rects from '{tmx_path}'")
        print(f"Player start position: {self.player_start}")

    def get_solid_rects(self):
        return self.collision_rects

    def get_bush_rects(self):
        return self.bush_rects

    def draw(self, surface, offset_x=0, offset_y=0):
        """Draw all non-collision layers."""
        if not self.tmx:
            return

        for layer in self.tmx.visible_layers:
            layer_name = (getattr(layer, "name", "") or "").lower()
            layer_props = getattr(layer, "properties", {}) or {}

            # Skip collision layers visually
            if layer_name == "collision" or layer_props.get("collision") is True:
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
                        surface.blit(
                            tile,
                            (x * self.tilewidth + offset_x, y * self.tileheight + offset_y)
                        )