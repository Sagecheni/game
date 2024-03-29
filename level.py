import pygame
from settings import *
from player import Player
from overlay import Overlay
from sprites import *
from pytmx.util_pygame import load_pygame
from support import *
from transition import Transition
from soil import SoilLayer, SoilTile
from sky import Rain, Sky
from menu import Menu


class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        # sprite组
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()  # 可碰撞的组
        self.tree_sprites = pygame.sprite.Group()  # 树组
        self.interaction_sprites = pygame.sprite.Group()  # 可交互的组

        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
        self.setup()
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)

        # 商店
        self.menu = Menu(self.player, self.toggle_shop)
        self.shop_active = False

        # 天气
        self.rain = Rain(self.all_sprites)
        self.raining = randint(0, 10) > 7  # 随机是否下雨
        self.soil_layer.raining = self.raining
        self.sky = Sky()

        # 音乐
        self.success = pygame.mixer.Sound('./audio/success.wav')
        self.success.set_volume(0.3)
        self.music = pygame.mixer.Sound('./audio/music.mp3')
        self.music.play(loops=-1)

    def player_add(self, item):
        self.player.item_inventory[item] += 1

    def reset(self):
        # 植物成长
        self.soil_layer.update_plants()

        # 土壤变化
        self.soil_layer.remove_water()
        self.raining = randint(0, 10) > 7
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()
        # 树和苹果
        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_sprites.sprites():
                apple.kill()
            tree.create_fruit()
        # 天气
        self.sky.start_color = [255, 255, 255]

    def setup(self):
        tmx_data = load_pygame('./data/map.tmx')

        # 房子
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])

        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['main'])
        # 围栏
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])

        # 水塘
        water_frames = import_folder('./graphics/water')
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Water((x * TILE_SIZE, y * TILE_SIZE), water_frames, self.all_sprites)
        # 树
        for obj in tmx_data.get_layer_by_name('Trees'):
            Tree(
                pos=(obj.x, obj.y),
                surf=obj.image,
                groups=[self.all_sprites, self.collision_sprites, self.tree_sprites],
                name=obj.name,
                player_add=self.player_add)
        # 花
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        # 外围碰撞
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)

        # 玩家
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(
                    pos=(obj.x, obj.y),
                    group=self.all_sprites,
                    collision_sprites=self.collision_sprites,
                    tree_sprites=self.tree_sprites,
                    interaction=self.interaction_sprites,
                    soil_layer=self.soil_layer,
                    toggle_shop=self.toggle_shop)

            if obj.name == 'Bed':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)

            if obj.name == 'Trader':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)

        Generic(
            pos=(0, 0),
            surf=pygame.image.load('./graphics/world/ground.png').convert_alpha(),
            groups=self.all_sprites,
            z=LAYERS['ground'])

    def run(self, dt):
        self.display_surface.fill('black')
        self.all_sprites.customize_draw(self.player)

        if self.shop_active:
            self.menu.update()
        else:
            self.all_sprites.update(dt)
            self.plant_collision()

        # 天气
        self.overlay.display()
        if self.raining and not self.shop_active:
            self.rain.update()
        self.sky.display(dt)

        # 睡觉的变化
        if self.player.sleep:
            self.transition.play()

    def plant_collision(self):  # 收获植物
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    self.player_add(plant.plant_type)
                    plant.kill()
                    Particle(plant.rect.topleft, plant.image,
                             self.all_sprites,
                             z=LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

    def toggle_shop(self):
        self.shop_active = not self.shop_active


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

    def customize_draw(self, player):
        # 偏移量，使得camera始终居中
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        # 摄像机的移动
        for layer in LAYERS.values():
            for sprite in sorted(self.sprites(),
                                 key=lambda sprite: sprite.rect.centery):  # sorted 用于cover一些东西,实现一个东西能够遮盖角色的效果
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)
