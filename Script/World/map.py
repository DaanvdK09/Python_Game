import pygame
import pytmx

class TileMap:
    def __init__(self, tmx_path, tile_size=64):
        self.tmx = pytmx.load_pygame(tmx_path)
        self.tmx_path = tmx_path
        self.tilewidth = tile_size
        self.tileheight = tile_size
        self.tile_size = tile_size
        self.width = 0
        self.height = 0
        self.collision_rects = []
        self.bush_shapes = []
        self.hospital_shapes = []
        self.house_shapes = []
        self.GrassGym_shapes = []
        self.IceGym_shapes = []
        self.FireGym_shapes = []
        self.exit_shapes = []
        self.trainer_starts = []
        self.objects = []
        self.multiplayer_gym_rect = None
        self.player_start = None
        self.professor_start = None
        self.nurse_joy_start = None
        self.shopkeeper_start = None
        self.counter_rect = None
        self.roof_rects = []

        if tmx_path:
            self.load_tmx(tmx_path)

        for obj_group in self.tmx.objectgroups:
            for obj in obj_group:
                self.objects.append(obj)
        print("Loaded TMX objects:", self.objects)

    def get_counter_rect(self):
        return self.counter_rect

    def get_roof_rects(self):
        return self.roof_rects

    def load_tmx(self, tmx_path):
        try:
            self.tmx = pytmx.load_pygame(tmx_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load TMX '{tmx_path}': {e}") from e

        self.tilewidth = getattr(self.tmx, "tilewidth", self.tile_size)
        self.tileheight = getattr(self.tmx, "tileheight", self.tile_size)
        self.tile_size = self.tilewidth
        self.width = getattr(self.tmx, "width", 0) * self.tilewidth
        self.height = getattr(self.tmx, "height", 0) * self.tileheight

        self.collision_rects = []
        self.bush_shapes = []
        self.nature_shapes = []
        self.hospital_shapes = []
        self.house_shapes = []
        self.GrassGym_shapes = []
        self.IceGym_shapes = []
        self.FireGym_shapes = []
        self.exit_shapes = []
        self.multiplayer_gym_rect = None
        self.roof_rects = []

        def _gid_to_int(gid):
            try:
                return int(gid)
            except Exception:
                return None

        def _safe_lower(val):
            return (val or "").lower()

        print(f"Layers found: {[getattr(layer, 'name', None) for layer in self.tmx.visible_layers]}")

        for layer in self.tmx.visible_layers:
            layer_name = (getattr(layer, "name", "") or "").lower()
            layer_props = getattr(layer, "properties", {}) or {}

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

            object_layers = []
            if hasattr(self.tmx, "objectgroups"):
                object_layers.extend(self.tmx.objectgroups)
            if hasattr(self.tmx, "layers"):
                object_layers.extend([l for l in self.tmx.layers if hasattr(l, "objects")])
            if hasattr(self.tmx, "visible_layers"):
                object_layers.extend([l for l in self.tmx.visible_layers if hasattr(l, "objects")])

            for layer_obj in object_layers:
                layer_name = _safe_lower(getattr(layer_obj, "name", None))
                for obj in layer_obj:
                    name = _safe_lower(getattr(obj, "name", None))
                    otype = _safe_lower(getattr(obj, "type", None))

                    # Bush detection
                    if name == "bush" or otype == "bush" or layer_name == "bushes":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.bush_shapes.append(polygon)
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.bush_shapes.append(r)

                    # Nature detection
                    if name == "nature" or otype == "nature" or layer_name == "nature":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.nature_shapes.append(polygon)
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.nature_shapes.append(r)

                    # Player start detection
                    if name == "player" or otype == "player":
                        self.player_start = (int(obj.x), int(obj.y))
                        print(f"Player start position set to: {self.player_start}")

                    # Professor npc detection
                    if name == "professor" or otype == "professor":
                        self.professor_start = (int(obj.x), int(obj.y))
                        print(f"Professor start position set to: {self.professor_start}")

                    # Multiplayer gym detection
                    if name == "multiplayergym" or otype == "multiplayergym":
                        self.multiplayer_gym_rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                        print(f"Multiplayer gym rect set to: {self.multiplayer_gym_rect}")

                    # Hospital detection
                    if name == "hospital" or otype == "hospital" or layer_name == "hospitals":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.hospital_shapes.append(polygon)
                            print(f"Added hospital polygon (object layer): {polygon}")
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.hospital_shapes.append(r)
                            print(f"Added hospital rect (object layer): {r}")

                    # Hospital NPC detection
                    if name == "nurse_joy" or otype == "nurse_joy":
                        if hasattr(obj, "points") and obj.points:
                            self.nurse_joy_start = (int(obj.x), int(obj.y))
                            print(f"Nurse Joy start position set to: {self.nurse_joy_start}")

                    if name == "shopkeeper" or otype == "shopkeeper":
                        if hasattr(obj, "points") and obj.points:
                            self.shopkeeper_start = (int(obj.x), int(obj.y))
                            print(f"Shopkeeper start position set to: {self.shopkeeper_start}")

                    # House detection
                    if name == "house" or otype == "house" or layer_name == "houses":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.house_shapes.append(polygon)
                            print(f"Added house polygon (object layer): {polygon}")
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.house_shapes.append(r)
                            print(f"Added house rect (object layer): {r}")

                    if name == "grassgym" or otype == "grassgym" or layer_name == "Gym":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.GrassGym_shapes.append(polygon)
                            print(f"Added Grass Gym polygon (object layer): {polygon}")
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.GrassGym_shapes.append(r)
                            print(f"Added Grass Gym rect (object layer): {r}")

                    if name == "icegym" or otype == "icegym" or layer_name == "Gym":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.IceGym_shapes.append(polygon)
                            print(f"Added Ice Gym polygon (object layer): {polygon}")
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.IceGym_shapes.append(r)
                            print(f"Added Ice Gym rect (object layer): {r}")

                    if name == "firegym" or otype == "firegym" or layer_name == "Gym":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.FireGym_shapes.append(polygon)
                            print(f"Added Fire Gym polygon (object layer): {polygon}")
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.FireGym_shapes.append(r)
                            print(f"Added Fire Gym rect (object layer): {r}")

                    if name == "trainer" or otype == "trainer":
                        self.trainer_starts.append((int(obj.x), int(obj.y), obj.properties.get("type", "grass")))
                        print(f"Trainer start position set to: {(int(obj.x), int(obj.y))} with type {obj.properties.get('type', 'grass')}")

                    # Counter detection
                    if name == "counter" or otype == "counter":
                        self.counter_rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                        print(f"Counter rect set to: {self.counter_rect}")

                    # Roof detection
                    if name == "roof" or otype == "roof":
                        r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                        self.roof_rects.append(r)
                        print(f"Added roof rect: {r}")

                    # Exit detection
                    if name == "exit" or otype == "exit" or layer_name == "exits":
                        if hasattr(obj, "points") and obj.points:
                            polygon = list(obj.points)
                            self.exit_shapes.append(polygon)
                            print(f"Added exit polygon (object layer): {polygon}")
                        else:
                            r = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                            self.exit_shapes.append(r)
                            print(f"Added exit rect (object layer): {r}")

        print(f"TileMap built {len(self.collision_rects)} collision rects, {len(self.bush_shapes)} bush shapes, {len(self.hospital_shapes)} hospital shapes, {len(self.house_shapes)} house shapes, and {len(self.exit_shapes)} exit shapes from '{tmx_path}'")
        print(f"Player start position: {self.player_start}")

    def get_solid_rects(self):
        return self.collision_rects

    def get_bush_rects(self):
        return self.bush_shapes
    
    def get_nature_shapes(self):
        return self.nature_shapes

    def get_hospital_rects(self):
        return self.hospital_shapes

    def get_house_rects(self):
        return self.house_shapes

    def get_GrassGym_rects(self):
        return self.GrassGym_shapes

    def get_IceGym_rects(self):
        return self.IceGym_shapes

    def get_FireGym_rects(self):
        return self.FireGym_shapes

    def get_exit_rects(self):
        return self.exit_shapes

    def get_multiplayer_gym_rect(self):
        return self.multiplayer_gym_rect

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.tmx:
            return

        self._draw_tiles(surface, offset_x, offset_y, predicate=None)

    def _draw_tiles(self, surface, offset_x=0, offset_y=0, predicate=None):
        if not self.tmx:
            return

        for layer in self.tmx.visible_layers:
            layer_name = (getattr(layer, "name", "") or "").lower()
            layer_props = getattr(layer, "properties", {}) or {}

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
                    tile_bottom = y * self.tileheight + self.tileheight
                    if predicate is not None:
                        try:
                            ok = predicate(tile_bottom, layer_name, layer_props)
                        except Exception:
                            ok = False
                    else:
                        ok = True

                    if not ok:
                        continue

                    if tile:
                        try:
                            extra_h = tile.get_height() - self.tileheight
                        except Exception:
                            extra_h = 0
                        if extra_h < 0:
                            extra_h = 0

                        surface.blit(
                            tile,
                            (x * self.tilewidth + offset_x,
                             y * self.tileheight + offset_y - extra_h)
                        )

    def draw_lower(self, surface, player_rect, offset_x=0, offset_y=0):
        if player_rect is None:
            return self._draw_tiles(surface, offset_x, offset_y, predicate=None)

        player_bottom = player_rect.bottom

        def is_split_layer(layer_name, layer_props):
            if layer_props.get("split") is True:
                return True
            ln = (layer_name or "").lower()
            keywords = ("build", "building", "object", "objects", "tree", "trees", "house", "roof", "bush", "top", "nature")
            for k in keywords:
                if k in ln:
                    return True
            return False

        def pred(tile_bottom, layer_name, layer_props):
            if not is_split_layer(layer_name, layer_props):
                return True
            return tile_bottom <= player_bottom

        self._draw_tiles(surface, offset_x, offset_y, predicate=pred)

    def draw_upper(self, surface, player_rect, offset_x=0, offset_y=0):
        if player_rect is None:
            return self._draw_tiles(surface, offset_x, offset_y, predicate=None)

        player_bottom = player_rect.bottom

        def is_split_layer(layer_name, layer_props):
            if layer_props.get("split") is True:
                return True
            ln = (layer_name or "").lower()
            keywords = ("build", "building", "object", "objects", "tree", "trees", "house", "roof", "bush", "top", "counter", "nature")
            for k in keywords:
                if k in ln:
                    return True
            return False

        def pred(tile_bottom, layer_name, layer_props):
            if "top" in (layer_name or "").lower() or "counter" in (layer_name or "").lower():
                return True
            if not is_split_layer(layer_name, layer_props):
                return False
            return tile_bottom > player_bottom

        self._draw_tiles(surface, offset_x, offset_y, predicate=pred)