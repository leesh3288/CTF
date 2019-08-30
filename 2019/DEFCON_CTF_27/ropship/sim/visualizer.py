#!/usr/bin/env python

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import os
import math
import pygame
import io
import base64
import sys
import random
import time
import pickle
import subprocess
import json
import gzip
from PIL import Image

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


ICON = b'iBL{Q4GJ0x0000DNk~Le0000W0000W2m=5B07RsU#sB~U{ZLF)Mb)fW)U#UCvsuNiQPQ$m)3aF9vRKozS<SIi)3aF9vRTrzS<|yv)3aF4w^`G&TGO*w)3aF8vslx!S=F>x)3R98vsl!$Sktpu(z968vsluzSJSgu)3R98vRTrzS=6&w)3R98vsux#TG6vt)3I98vsluzSk$sv(zII9v0Bo!Skkgt(zIFt006uoH`B9OydgIP0|UGyH`B6Nv6oT?1qCxNCDN@|2L}dAL^05$RbyB@0RaI}NHfNDN4_#Sc4tD+r&YZtIL2;8%dJ?>p;WyrImm%Z4-X8$M?7j>KF+ULF)bs_nNiWJRumKv6%`TDvRS@0I#x|KCL|rxu~`BF0?waPwwqJNa77FZ3K$m?#;8`9gH6I#Kgx?u!A?HELOjWYOCcZ`(6CrXKrfAXNiHiQJvb}Pmr=q~KQ%EX&Ye=xs#Y8u78w~7!=_chL_ExtP{d<GD<~kxcu237Qf^^DPDU~$A{)IfIlrS-$*Wg5G$);hPNa=c9vv9WlTU_pNXdsxA08O2lv2JoIy*Kg#cM=+Y(zmjEtP;v%8gFKSwO{UM8|qa$9qUaJuN^wD}!=J3JM3qTtN~M4qsI|z)C%+kWf-eG-g{ozdbv}XGDE%MX8Zdy(&0iRy&e@OPYmE!dgMhl~8eGLCcU&#&So*W<w|@9=|_3xgj^hUO`w-H^-@0T~j%riB7*dI=Y`!xSmwfuUNdGRLFfwL_RLTP(Hy-K7%YV$%suH5)s5;LQy6rvLiOZq*hx|IHe~wzBxM3rd5D&MiUbczM@r$c1XaZR*!s2qKi+QC^QfX35Y8(&6`rrpj5|vNo^`Dwjwqz8yY$wA9H0vjw>>=nNz<zI>>-ZcW6V3cu83(C~RLpdTK<IDl;}79YrG}tCCSaAt7ceD|{<2ql-@^7ZzYCDHIJ1NI@_m6cltTE*KCGF&rFtD=)@$M<^K>aAH8LB{rBUGs>%1N+l%*1O%dOMXZWWd{jHGC^iiC0nY#c00DGTPE!Ct=GbNc0004EOGiWihy@);00009a7bBm000XU000XU0RWnu7ytkO2XskIMF-;s69_N@uCvHG00008bVXQnLvL+uWo~o;_RN;Q00054Nkl<ZILmcYJ!=AC48C8KJhcU@&_RUS-NCIK1%E&n5p;6s)T1~Qmuu0bgHWV!&{cX}{0r_K{1?r~z3SO(@b1i;<Vl{qNfaFkkQ3!VR4GV_>O=&2(!V}>O!RDT`;RJnAwN)`lE={Fkg!Ms*M?=goQbh>2cW~Cum0`9!|*dPzp%+Uz!}jjWD)yH!n+e@w3*wA1OcI4;i365w&S&8tzkHs0z1Gbkz=#72+G{4q=EpRDnQ_A5KywIWoVM=W#N(FeUOz1jd*ngz!9E=vO>T(T7SUH0r!Y{JXl)E*NJsJ4^@FB5{-s3WQ3aYh~C*8y#H^IA6ePzz~8iYC@9A95mj?2QiKA-V-S`?mH5(oux+(~R%=`IBDNxpONW!1XjdLBAF3tRDs827gXA6;K1+gYU<=LA1cg=?8HuM;|MCroR!hL#iFR2X<>@*}%KW|+dc!9I-e|^RV0K#cg&Qn*vXBHTI*ineXe_ofkJiZ>mqvd`kNtZA8Ob$|ct08Cv9|8TYK`IA@MLj>)x+`nRIOHN|0<W)T<Vp}`|tYy0&(fTd)^wM!~g&Q07*qoM6N<$f&'


BOARDSIZE = 1000.0
EXTRASIZE = 250.0


verticies_ship = (
    (-10,-10,0),
    (-10,10,0),
    (18,0,0)
    )

edges_ship = (
    (0,1),
    (1,2),
    (2,0)
    )


def Cube():
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3dv(verticies[vertex])
    glEnd()


def draw_text(value, font=GLUT_BITMAP_8_BY_13, offset=(0,0)):
    glPushMatrix();
    glRasterPos2d(*offset);
    for character in value:
        glutBitmapCharacter(font, ord(character));
    glPopMatrix();


def draw_circle(radius, segments=250, line_width=1.0):
    glLineWidth(line_width);
    glBegin(GL_LINE_LOOP)
    for vertex in range(0, segments):
        angle  = float(vertex) * 2.0 * math.pi / segments
        glVertex3dv((math.cos(angle)*radius, math.sin(angle)*radius,0.0))
    glEnd();
    glLineWidth(1.0);

def draw_score(state, nstates=None):
    glColor3d(0.05, 0.05, 0.10)
    glBegin(GL_POLYGON)
    score_area_vertices = ((BOARDSIZE/2.0+20, BOARDSIZE/2.0),
                        (BOARDSIZE/2.0+EXTRASIZE, BOARDSIZE/2.0), 
                        (BOARDSIZE/2.0+EXTRASIZE, -BOARDSIZE/2.0),
                        (BOARDSIZE/2.0+20, -BOARDSIZE/2.0))
    score_area_edges = ((0,1),(1,2),(2,3),(3,0))
    for edge in score_area_edges:
        for vertex in edge:
            glVertex2dv(score_area_vertices[vertex])
    glEnd()

    glColor3d(1, 1, 1)
    glPushMatrix()
    glTranslated(BOARDSIZE/2.0+30, BOARDSIZE/2.0-40, 0.0)
    draw_text("=== RANKING ===", font=GLUT_BITMAP_HELVETICA_18)
    scored_team = sorted([(team.team_name[:16], team.fscore, team.score) for i, team in state.teams.items()], key=lambda x:-x[1])
    for i, (name, fscore, score) in enumerate(scored_team):
        glTranslated(0, -30, 0.0)
        glPushMatrix()
        draw_text("%s)" % str(i+1))
        glTranslated(22, 0, 0.0)
        draw_text(name[:]) 
        glTranslated(EXTRASIZE-100, 0.0, 0.0)
        draw_text(str(score))
        glPopMatrix()
    glPopMatrix()

    glPushMatrix()
    glTranslated(BOARDSIZE/2.0+30, BOARDSIZE/2.0-40 - 550, 0.0)
    draw_text("=== STATE ===", font=GLUT_BITMAP_HELVETICA_18)
    glTranslated(0, -30, 0.0)
    glPushMatrix()
    if nstates is not None:
        draw_text("tick: %s/%s" % (str(state.tick),str(nstates)))
    else:
        draw_text("tick: %s" % str(state.tick))
    glPopMatrix()
    glTranslated(0, -20, 0.0)
    glPushMatrix()
    draw_text("defcon_round: %s" % str(state.defcon_round))
    glPopMatrix()
    glTranslated(0, -30, 0.0)
    glPushMatrix()
    for e in state.events:
        draw_text(e)
        glTranslated(0, -20, 0.0)
    glPopMatrix()
    glTranslated(0, -60, 0.0)
    for tid, team in state.teams.items():
        if state.moves == None:
            continue
        draw_text("%-3d %-3d: %s" % (tid, team.defcon_id, state.moves[team.tid]))
        glTranslated(0, -15, 0.0)
    glPopMatrix()


def show(state, images_folder=None, nstates=None):
    for event in pygame.event.get():
        if event.type==pygame.QUIT or (event.type==pygame.KEYDOWN and event.key==ord('q')):
            print("Terminating...")
            pygame.quit()
            sys.exit(0)

    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    glColor3d(1, 1, 1)
    draw_circle(state.boardradius)

    for i, team in state.teams.items():
        if team.ship == None:
            continue
        l = team.ship.location
        glPushMatrix()
        glTranslated(l.x, l.y, 0.0)
        glRotated(math.degrees(l.a), 0.0, 0.0, 1.0)
        glColor3d(*team.color)
        glBegin(GL_POLYGON)
        for edge in edges_ship:
            for vertex in edge:
                glVertex3dv(verticies_ship[vertex])
        glEnd()
        
        glColor3d(1, 1, 1)
        if(     l.x<(-BOARDSIZE/2.0+20) or l.x>(BOARDSIZE/2.0-20) or
                l.y<(-BOARDSIZE/2.0+20) or l.y>(BOARDSIZE/2.0-20)):
            text_offset = (20,22)
        elif l.a > 0.0 and l.a < math.pi/2.0*1.1:
            text_offset = (-5,-15)
        else:
            text_offset = (-15,10)
        draw_text((team.team_name)[:16], offset=text_offset) 
        if team.shield:
            draw_circle(10.0+3.5, segments=25, line_width=3.0)
        glPopMatrix()
        


    for i, team in state.teams.items():
        if team.ship == None:
            continue
        glColor3d(*team.color)
        for b in team.bullets:
            glPushMatrix()
            glTranslated(b.location.x, b.location.y, 0.0)
            glRotated(random.randint(0, 44), 0.0, 0.0, 1.0)
            glBegin(GL_POLYGON)
            bsize = 8
            glVertex3dv([-bsize,bsize,0])
            glVertex3dv([bsize,bsize,0])
            glVertex3dv([bsize,-bsize,0])
            glVertex3dv([-bsize,-bsize,0])
            glEnd()
            glRotated(45.0, 0.0, 0.0, 1.0)
            glBegin(GL_POLYGON)
            glVertex3dv([-bsize,bsize,0])
            glVertex3dv([bsize,bsize,0])
            glVertex3dv([bsize,-bsize,0])
            glVertex3dv([-bsize,-bsize,0])
            glEnd()
            glPopMatrix()

    draw_score(state, nstates)

    if images_folder is not None:
        data = glReadPixels(0, 0, BOARDSIZE+EXTRASIZE, BOARDSIZE, GL_RGB, GL_UNSIGNED_BYTE, outputType=None)
        image = Image.frombytes("RGB", (int(BOARDSIZE+EXTRASIZE), int(BOARDSIZE)), data)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(os.path.join(images_folder, "image_%06d.png" % state.tick), format="png")

    pygame.display.flip()


def init():
    pygame.init()
    display = (int(BOARDSIZE + EXTRASIZE),int(BOARDSIZE))
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption("ropship")
    pygame.display.set_icon(pygame.image.load(io.BytesIO(base64.b85decode(ICON))))
    glutInit()

    glMatrixMode(GL_PROJECTION);
    glOrtho(0.0, BOARDSIZE + EXTRASIZE, BOARDSIZE, 0.0, 0.0, 10000.0);
    glMatrixMode(GL_MODELVIEW);
    glTranslated(BOARDSIZE/2.0,BOARDSIZE/2.0, -1.0)
    glRotated(180.0, 1.0, 0.0, 0.0)


class Dummy():
    def __init__(self, dd):
        for k, v in dd.items():
            if k == "teams":
                vnew = {}
                for k2, v2 in v.items():
                    vnew[int(k2)] = Dummy(v2)
                setattr(self, "teams", vnew)
            elif k == "moves" and v!=None:
                vnew = {}
                for k2, v2 in v.items():
                    vnew[int(k2)] = v2
                setattr(self, "moves", vnew)
            elif k == "bullets":
                vnew = []
                for v2 in v:
                    vnew.append(Dummy(v2))
                setattr(self, "bullets", vnew)
            else:
                if type(v) == dict:
                    vnew = Dummy(v)
                else:
                    vnew = v
                setattr(self, k, vnew)


def main(states, images_folder, video=None):
    init()
    with open(states, "rb") as fp:
        states_content = gzip.decompress(fp.read()).decode()

    states = json.loads(states_content)
    for state_dict in states:
        state = Dummy(state_dict)
        print("showing state:", repr(state.tick))
        show(state, images_folder, nstates=len(states)-1)

    if video != None:
        print("rendering video...")
        p = subprocess.Popen(["ffmpeg", "-y", "-i", os.path.join(images_folder, r"image_%06d.png"), "-c:v", "libx264", "-preset", "veryfast", "-qp", "0", "-f", "mp4", video], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()


if __name__ == "__main__":
    try:
        tf = sys.argv.index("--video")
        video = sys.argv[tf+1]
    except ValueError:
        video = None
    main(sys.argv[-2], sys.argv[-1], video)


'''
To run on Ubuntu 18.04:
sudo apt install python3
sudo apt install python3-pip
sudo apt install freeglut3-dev
sudo apt install ffmpeg
sudo pip3 install Pillow pygame PyOpenGL

python3 ./visualizer.py [--video <video_filepath>] <results.gz> <output_image_folder>

To run without a display:
sudo apt install xvfb
Xvfb :1 -screen 0 1024x768x24 < /dev/null &
export DISPLAY=":1"
'''
