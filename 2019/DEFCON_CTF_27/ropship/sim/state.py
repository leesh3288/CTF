#!/usr/bin/env python


import math
import random


def team_defcon_id_to_color(defcon_id):
    color_table = [ 0x800000,0x008000,0x808080,0x808000,0xFF0000,0x000080,0x00FF00,0x800080,
                    0xFFFF00,0x008080,0x0000FF,0xC0C0C0,0xFF00FF,0xC0DCC0,0x00FFFF,0xA6CAF0,
                    0xFFEBE0,0x202020]
    return [((color_table[defcon_id%len(color_table)] & (0xff<<v)) >> v)/255.0 for v in [16,8,0]]


class Location:
    def __init__(self, x=0.0, y=0.0, a=0.0):
        self.x = x
        self.y = y
        self.a = self.amod(a)

    @staticmethod
    def amod(a):
        t = math.fmod(a, 2.0*math.pi)
        if t<0.0:
            t+= 2.0*math.pi
        return t


    def distance(self, other):
        return math.sqrt(pow(self.x-other.x, 2) + pow(self.y-other.y, 2))

    def distance3(self, other, point):
        x1 = self.x
        y1 = self.y
        x2 = other.x
        y2 = other.y
        x3 = point.x
        y3 = point.y

        px = x2-x1
        py = y2-y1
        norm = px*px + py*py
        u =  ((x3 - x1) * px + (y3 - y1) * py) / float(norm)
        if u > 1:
            u = 1
        elif u < 0:
            u = 0
        x = x1 + u * px
        y = y1 + u * py
        dx = x - x3
        dy = y - y3

        dist = (dx*dx + dy*dy)**.5
        return dist


    def move(self, a=0.0, t=0.0):
        self.a = self.amod(self.a+a)
        self.x += t * math.cos(self.a)
        self.y += t * math.sin(self.a)

    def __str__(self):
        return "[x={:4.3f},y={:4.3f},a={:4.3f}]".format(self.x, self.y, self.a)


class Ship:
    def __init__(self):
        self.location = Location()
        self.fspeed = 0.0
        self.aspeed = 0.0


class Bullet:
    def __init__(self, location):
        self.location = location
        self.fspeed = 12.0 


class Team:
    def __init__(self, tid, defcon_id, team_name):
        self.tid = tid
        self.defcon_id = defcon_id
        self.team_name = team_name;
        self.last_shooting = -30
        self.last_shield = -10000
        self.shield = False
        self.lastkill_tick = 0
        self.died_tick = 0
        self.score = 0
        self.fscore = 0.0
        self.rank = 0
        self.bullets = []
        self.color = (1.0,1.0,1.0)
        self.ship = None
        self.color = team_defcon_id_to_color(defcon_id)


class State:
    def __init__(self, teams, boardradius, teamradius, defcon_round, seed, buildteams=True):
        self.tick = 0
        self.boardradius = boardradius
        self.events = []
        self.teams = {}
        self.defcon_round = defcon_round
        self.seed = seed
        self.moves = None
        if buildteams:
            defcon_ids = teams.keys()
            defcon_ids_list = list(defcon_ids)
            random.shuffle(defcon_ids_list)
            for tid, defcon_id in enumerate(defcon_ids_list):
                team_name = teams[defcon_id]
                t = Team(tid, defcon_id, team_name)
                t.ship = Ship()
                print(team_name, tid, defcon_id)
                t.ship.location.move(((math.pi*2.0)/(len(teams)))*tid, teamradius)
                t.ship.location.move(math.pi)
                self.teams[tid] = t


