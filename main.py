from collections import defaultdict
from pyglet.image import load, ImageGrid, Animation
from pyglet.window import key
import pyglet
import cocos
import cocos.layer
import cocos.sprite
from cocos.director import director
import cocos.collision_model as cm
import cocos.euclid as eu
import cocos.tiles
import cocos.particle_systems as ps
import pygame.mixer

import random
import math
import cocos.particle_systems as ps


# 2017103734 소프트웨어 융합 원종서
class Obstacle(cocos.sprite.Sprite):
    def __init__(self, img, x, y, r=0):
        super(Obstacle, self).__init__(img)
        self.rotation = r
        self.position = eu.Vector2(x, y)
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)

    def update(self, dt):
        pass


class Dead(ps.Explosion):
    def __init__(self, x, y, n=0):
        super(Dead, self).__init__(fallback=False)
        self.position = eu.Vector2(x, y)
        self.life = 0.25
        self.duration = 0.05
        self.blend_additive = False
        self.speed = 50
        self.life_var = 0.1
        if n == 0:
            color = ps.Color(0, 0.5, 0, 1)
        elif n == 1:
            color = ps.Color(0.5, 0, 0, 1)
        self.start_color_var = ps.Color(0, 0, 0, 0)
        self.start_color = color
        self.end_color = color
        self.end_color_var = ps.Color(0, 0, 0, 0)
        self.dt = 0

    def update(self, elasped):
        self.dt += elasped
        if (self.dt > 2):
            self.kill()


class Actor(cocos.sprite.Sprite):

    def __init__(self, img, x, y):
        super(Actor, self).__init__(img)

        self.position = eu.Vector2(x, y)

        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)

    def update(self, dt):
        pass

    def move(self, offset):
        pass


class Item(Actor):
    def __init__(self, x, y, n):
        img = self.setType(n)
        super(Item, self).__init__(img, x, y)
        self.scale = 0.5
        self.cshape = cm.AARectShape(self.position, self.width * 0.7, self.height * 0.7)

    def setType(self, n):
        if n == 1:
            self.itemType = 1
            img = "asset/Chest1.png"
        if n == 2:
            self.itemType = 2
            img = "asset/Chest2.png"
        return img


class Zombie(Actor):

    def __init__(self, x, y, player):
        animation = self.load_animation('asset/Zombie.png')
        super(Zombie, self).__init__(animation, x, y)
        self.scale = 0.3
        self.cshape = cm.AARectShape(self.position,
                                     self.width * 0.2,
                                     self.height * 0.2)
        self.setTarget(player)
        self.speed = 80
        self.bump = False
        self.pre_pos = self.position

    def setTarget(self, player):
        self.target = player

    def load_animation(self, imgage):
        seq = ImageGrid(load(imgage), 17, 1)
        return Animation.from_image_sequence(seq, 0.02)

    def update(self, elapsed):
        x, y = self.target.x - self.x, self.target.y - self.y
        angle = math.atan2(x, y)
        self.rotation = math.degrees(angle) - 90
        rot = math.radians(self.rotation + 90)
        vec = eu.Vector2(math.sin(rot) * self.speed * elapsed, math.cos(rot) * self.speed * elapsed)
        self.move(vec)

    def move(self, offset):
        if self.bump is True:
            self.position = self.pre_pos
            self.cshape.center = self.pre_pos
            self.bump = False
        else:
            self.pre_pos = self.position
            self.position += offset
            self.cshape.center += offset

    def collide(self, other):
        if type(other) == Obstacle:
            self.bump = True
        elif type(other) == Player:
            self.bump = True

    def kill(self):
        if self in self.parent.zombies:
            drop = random.randint(0, 20)
            if drop == 1:
                self.parent.add(Item(self.x, self.y, 1))
            elif drop == 2:
                self.parent.add(Item(self.x, self.y, 2))
            super().kill()
            self.parent.add(Dead(self.x, self.y))
            sound_zombieDown.play()
            self.parent.zombies.remove(self)


class Player(Actor):
    KEYS_PRESSED = defaultdict(int)

    def __init__(self, x, y):
        self.anim_set = []
        self.setAnim()
        super(Player, self).__init__(self.anim_set[0][0], x, y)
        self.image = self.anim_set[0][0]
        self.hold = 0
        self.scale = 0.3
        self.image_anchor_x = 140
        self.image_anchor_y = 100
        self.cshape = cm.AARectShape(self.position, self.width * 0.3, self.height * 0.2)
        self.bullets = []
        self.bump = False
        self.pre_pos = eu.Vector2(0, 0)
        self.speed = 130
        self.aim = eu.Vector2(0, 0)
        self.anim_states = 0
        self.frate = 1
        self.dt = 0
        self.dvec = eu.Vector2(0, 0)
        self.hp = 100
        self.gp = 1
        self.gp_count = 0
        self.gun = 0
        self.rifle = 0
        self.shotgun = 0

    def load_anim(self, image, r, c, t):
        seq = ImageGrid(load(image), r, c)
        return Animation.from_image_sequence(seq, t)

    def setAnim(self):
        self.anim_set.append([self.load_anim("asset/handgun_idle.png", 1, 20, 0.05),
                              self.load_anim("asset/handgun_move.png", 1, 20, 0.01),
                              self.load_anim("asset/handgun_shoot.png", 1, 3, 0.05)])
        self.anim_set.append(
            [self.load_anim("asset/rifle_idle.png", 1, 20, 0.05), self.load_anim("asset/rifle_walk.png", 1, 20, 0.01),
             self.load_anim("asset/rifle_shoot.png", 1, 3, 0.05)])
        self.anim_set.append([self.load_anim("asset/shotgun_idle.png", 1, 20, 0.05),
                              self.load_anim("asset/shotgun_move.png", 1, 20, 0.01),
                              self.load_anim("asset/shotgun_shoot.png", 1, 3, 0.05)])

    def update(self, elapsed):

        # 회전
        scroller.set_focus(self.x, self.y)
        m_x, m_y = scroller.screen_to_world(self.aim.x, self.aim.y)
        x, y = m_x - self.x, m_y - self.y
        angle = math.atan2(x, y)
        self.rotation = math.degrees(angle)

        self.gp_count += elapsed

        # 움직임
        pressed = Player.KEYS_PRESSED
        moveLR = pressed[key.D] - pressed[key.A]
        moveUD = pressed[key.W] - pressed[key.S]
        vecX = moveLR
        vecY = moveUD
        if vecY != 0 and vecY != 0:
            vecX *= 0.7
            vecY *= 0.7
        self.vec = eu.Vector2(vecX, vecY)
        self.move(self.vec * self.speed * elapsed)

        # 애니메이션
        anim = 0
        if self.hold == 1 and self.dt < 0.19:
            anim = 2
        elif vecX != 0 or vecY != 0:
            anim = 1
        else:
            anim = 0
        if anim != self.anim_states:
            self.anim_states = anim
            self.image = self.anim_set[self.gun][anim]

        # 사격
        self.dt += elapsed
        if self.dt > self.frate and self.hold == 1:
            self.fire()
        # 총
        if pressed[key._1] == 1:
            self.gun = 0
            self.frate = 1
            self.parent.hud.update_guntype("Pistol")
            self.image = self.anim_set[self.gun][anim]
        elif pressed[key._2] == 1:
            self.gun = 1
            self.frate = 0.2
            self.parent.hud.update_guntype("Rifle")
            self.image = self.anim_set[self.gun][anim]
        elif pressed[key._3] == 1:
            self.gun = 2
            self.frate = 1
            self.parent.hud.update_guntype("Shotgun")
            self.image = self.anim_set[self.gun][anim]

    def fire(self):

        if self.gun == 0:
            sound_pistol.play()
            self.bullets.append(Shoot(self.x, self.y, self.rotation))
            self.parent.add(self.bullets[-1])
        elif self.gun == 1 and self.rifle > 0:
            sound_rifle.play()
            self.bullets.append(RifleBullet(self.x, self.y, self.rotation))
            self.parent.add(self.bullets[-1])
            self.rifle -= 1
            self.parent.hud.update_magazine(self.rifle, self.shotgun)
        elif self.gun == 2 and self.shotgun > 0:
            sound_shotgun.play()
            self.bullets.append(ShotgunBullet(self.x, self.y, self.rotation, 30))
            self.parent.add(self.bullets[-1])
            self.bullets.append(ShotgunBullet(self.x, self.y, self.rotation, -30))
            self.parent.add(self.bullets[-1])
            self.bullets.append(ShotgunBullet(self.x, self.y, self.rotation, 10))
            self.parent.add(self.bullets[-1])
            self.bullets.append(ShotgunBullet(self.x, self.y, self.rotation, -10))
            self.parent.add(self.bullets[-1])
            self.bullets.append(ShotgunBullet(self.x, self.y, self.rotation, 20))
            self.parent.add(self.bullets[-1])
            self.bullets.append(ShotgunBullet(self.x, self.y, self.rotation, -20))
            self.parent.add(self.bullets[-1])
            self.bullets.append(ShotgunBullet(self.x, self.y, self.rotation, 0))
            self.parent.add(self.bullets[-1])
            self.shotgun -= 1
            self.parent.hud.update_magazine(self.rifle, self.shotgun)
        self.dt = 0

    def move(self, offset):
        if self.x < 10 or self.x > 1910 or self.y < 10 or self.y > 1270:
            self.bump = True

        if self.bump is True:
            pre_x = self.pre_pos[0]
            pre_y = self.pre_pos[1]
            self.position += eu.Vector2(pre_x - self.x, pre_y - self.y) * 2
            self.cshape.center = self.position
            self.bump = False
        else:
            self.pre_pos = self.position
            self.position += offset
            self.cshape.center += offset

    def collide(self, other):
        if type(other) == Obstacle:
            self.bump = True
        elif type(other) == Zombie and self.gp_count > self.gp:
            sound_hurt.play()
            self.gp_count = 0
            self.hp -= 10
            if self.hp <= 0:
                self.parent.youDied()
            self.parent.hud.update_lives(self.hp)
            self.bump = True
            self.parent.add(Dead(self.x, self.y, 1))
        elif type(other) == Item:
            if other.itemType == 1:
                sound_item1.play()
                self.rifle += 50
            elif other.itemType == 2:
                sound_item2.play()
                self.shotgun += 16
            self.parent.hud.update_magazine(self.rifle, self.shotgun)
            other.kill()


class Shoot(Actor):
    def __init__(self, x, y, r, dis=50):
        sinR = math.sin(math.radians(r))
        cosR = math.cos(math.radians(r))
        newx = x + sinR * dis
        newy = y + cosR * dis
        super(Shoot, self).__init__("asset/bullet2.png", newx, newy)
        self.scale = 0.5
        self.cshape = cm.AARectShape(self.position, self.width / 2, self.height / 2)
        self.rotation = r
        self.bullet_speed = 700
        rad = math.radians(r)
        self.vec = eu.Vector2(math.sin(rad), math.cos(rad))

    def collide(self, other):
        if type(other) == Zombie:
            other.kill()
            if self in self.parent.get_children():
                self.kill()

    def move(self, offset):
        self.position += offset
        self.cshape.center += offset

    def update(self, elapsed):
        self.move(self.vec * self.bullet_speed * elapsed)

    def on_exit(self):
        self.parent.player.bullets.remove(self)
        super(Shoot, self).on_exit()


class RifleBullet(Shoot):
    def __init__(self, x, y, r):
        spread = random.randint(-2, 2)
        aix = r + spread
        super(RifleBullet, self).__init__(x, y, aix, 50)
        self.image = load("asset/bullet1.png")

    def collide(self, other):
        if type(other) == Zombie:
            other.kill()


class ShotgunBullet(Shoot):
    def __init__(self, x, y, r, spread):
        spread += random.randint(-2, 2)
        aix = r + spread
        super(ShotgunBullet, self).__init__(x, y, aix, 75)
        self.image = load("asset/bullet3.png")
        self.dis = 0
        self.bullet_speed = 400
        self.max_dis = 400

    def move(self, offset):

        self.position += offset
        self.cshape.center += offset

    def update(self, elapsed):
        self.move(self.vec * self.bullet_speed * elapsed)
        self.dis += self.bullet_speed * elapsed
        if (self.dis > self.max_dis):
            self.kill()

    def collide(self, other):
        if type(other) == Zombie:
            other.kill()


class GameLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True

    def on_key_press(self, k, _):
        Player.KEYS_PRESSED[k] = 1

    def on_key_release(self, k, _):
        Player.KEYS_PRESSED[k] = 0

    def on_mouse_motion(self, x, y, dx, dy):

        self.player.aim = eu.Vector2(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):

        self.player.aim = eu.Vector2(x, y)

    def on_mouse_press(self, x, y, buttons, mod):
        self.player.hold = 1

    def on_mouse_release(self, x, y, buttons, mod):
        self.player.hold = 0

    def __init__(self, hud):
        super(GameLayer, self).__init__()
        director.window.set_mouse_cursor(default_cursor)
        w, h = 1920, 1280
        self.player = Player(100, 100)
        self.add(self.player, z=1)
        self.hud = hud
        self.hud.update_magazine(self.player.rifle, self.player.shotgun)
        self.hud.update_guntype('Pistol')
        self.hud.update_lives(self.player.hp)
        self.width = w
        self.height = h
        self.schedule(self.update)
        self.dt = -3
        self.timer = 0
        self.setObj()
        self.zombies = []
        self.genRate = 1
        cell = 1.25 * 50
        self.collman = cm.CollisionManagerGrid(0, w, 0, h,
                                               cell, cell)

    def setObj(self):
        self.add(Obstacle("asset/obj1.png", 500, 400))
        self.add(Obstacle("asset/obj4.png", 300, 1050))
        self.add(Obstacle("asset/obj4.png", 600, 1100))
        self.add(Obstacle("asset/obj4.png", 900, 150))
        self.add(Obstacle("asset/obj4.png", 1100, 300))
        self.add(Obstacle("asset/obj3.png", 300, 700))
        self.add(Obstacle("asset/obj2.png", 1400, 900))
        self.add(Obstacle("asset/obj2.png", 1600, 500))
        self.add(Obstacle("asset/obj1.png", 900, 900))

    def update(self, elapsed):
        self.timer += elapsed
        self.hud.update_Sec(round(self.timer / 3, 2))  # 이유는 모르겠지만 schedule의 dt가 실제 시간의 1/3임 버그인 듯해서 나누어
        self.collman.clear()
        for _, node in self.children:
            if type(node) != Dead:
                self.collman.add(node)

        for bullet in self.player.bullets:
            self.collide(bullet)

        for bullet in self.player.bullets:
            self.collide(bullet)
            if not self.collman.knows(bullet):
                self.remove(bullet)

        for zombie in self.zombies:
            self.collide(zombie)
        self.collide(self.player)

        for _, node in self.children:
            node.update(elapsed)

        self.dt += elapsed
        self.gen_Zombies()

    def collide(self, node):
        if node is not None:
            for other in self.collman.iter_colliding(node):
                node.collide(other)

    def gen_Zombies(self):
        if self.genRate < self.dt:
            rand = random.randint(0, 3)
            if rand == 0:
                self.zombies.append(Zombie(random.randint(0, self.width), self.height, self.player))
                self.add(self.zombies[-1])
            if rand == 1:
                self.zombies.append(Zombie(random.randint(0, self.width), 0, self.player))
                self.add(self.zombies[-1])
            if rand == 2:
                self.zombies.append((Zombie(0, random.randint(0, self.height), self.player)))
                self.add(self.zombies[-1])
            if rand == 3:
                self.zombies.append(Zombie(self.width, random.randint(0, self.height), self.player))
                self.add(self.zombies[-1])
            self.dt = 0

    def youDied(self):
        self.remove(self.player)
        self.unschedule(self.update)
        self.hud.show_game_over()


class BackgroundLayer(cocos.layer.ScrollableLayer):

    def __init__(self):
        bg = cocos.tiles.load("asset/map.tmx")

        self.layer1 = bg["ground"]


class HUD(cocos.layer.Layer):
    def __init__(self):
        super(HUD, self).__init__()
        w, h = cocos.director.director.get_window_size()
        self.handgun_magazine_text = cocos.text.Label('Pistol: inf', font_size=18)
        self.handgun_magazine_text.position = (w - 200, 80)
        self.rifle_magazine_text = cocos.text.Label('', font_size=18)
        self.rifle_magazine_text.position = (w - 200, 60)
        self.shotgun_magazine_text = cocos.text.Label('', font_size=18)
        self.shotgun_magazine_text.position = (w - 200, 40)
        self.lives_text = cocos.text.Label('', font_size=30)
        self.lives_text.position = (50, 50)
        self.guntype_text = cocos.text.Label('', font_size=18)
        self.guntype_text.position = (w - 200, h - 60)
        self.time_text = cocos.text.Label('', font_size=25)
        self.time_text.position = (50, h - 60)
        self.add(self.handgun_magazine_text)
        self.add(self.rifle_magazine_text)
        self.add(self.shotgun_magazine_text)
        self.add(self.lives_text)
        self.add(self.guntype_text)
        self.add(self.time_text)

    def update_magazine(self, r, s):
        self.rifle_magazine_text.element.text = 'Rifle: %s' % (r)
        self.shotgun_magazine_text.element.text = 'Shotgun: %s' % (s)

    def update_lives(self, lives):
        self.lives_text.element.text = 'HP: %s' % lives

    def update_guntype(self, guntype):
        self.guntype_text.element.text = 'Now: %s' % guntype

    def update_Sec(self, sec):
        self.time_text.element.text = '%0.2f Sec' % sec

    def show_game_over(self):
        w, h = cocos.director.director.get_window_size()
        game_over = cocos.text.Label('Game Over', font_size=50,
                                     anchor_x='center',
                                     anchor_y='center')
        game_over.position = w * 0.5, h * 0.5
        self.add(game_over)


if __name__ == "__main__":
    pygame.mixer.init()
    bgm = pygame.mixer.Sound('asset/bgm.wav')
    bgm.set_volume(0.3)
    bgm.play(-1)
    sound_shotgun = pygame.mixer.Sound('asset/shotgun2.wav')
    sound_shotgun.set_volume(0.5)
    sound_pistol = pygame.mixer.Sound('asset/handgun.mp3')
    sound_pistol.set_volume(0.7)
    sound_rifle = pygame.mixer.Sound('asset/rifle.ogg')
    sound_rifle.set_volume(0.3)
    sound_zombieDown = pygame.mixer.Sound('asset/ZombieDown.wav')
    sound_hurt = pygame.mixer.Sound('asset/hurt.ogg')
    sound_hurt.set_volume(1.5)
    sound_item1 = pygame.mixer.Sound('asset/item1.aiff')
    sound_item2 = pygame.mixer.Sound('asset/item2.wav')
    cursor = pyglet.image.load('asset/aim.png')
    cursor.anchor_x = cursor.width // 2
    cursor.anchor_y = cursor.height // 2
    default_cursor = pyglet.window.ImageMouseCursor(cursor, 0, 0)

    cocos.director.director.init(caption='Cocos Invaders',
                                 width=1000, height=650)
    bg_layer = BackgroundLayer()
    hud_layer = HUD()
    game_layer = GameLayer(hud_layer)
    scroller = cocos.layer.ScrollingManager()
    scroller.add(bg_layer.layer1)
    scroller.add(game_layer)

    main_scene = cocos.scene.Scene(game_layer)
    main_scene.add(game_layer, z=1)
    main_scene.add(hud_layer, z=2)
    main_scene.add(scroller, z=0)

    cocos.director.director.run(main_scene)