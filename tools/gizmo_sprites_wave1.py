import json
W,H=16,12
def newg(): return [["."]*W for _ in range(H)]
def put(g,x,y,c):
    if 0<=x<W and 0<=y<H: g[y][x]=c
def rect(g,x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): put(g,x,y,c)
def body(g,x0,y0,x1,y1,rnd=1):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            corner=(x in(x0,x1)) and (y in(y0,y1))
            if rnd and corner: continue
            put(g,x,y,"b")
    for x in range(x0+1,x1): put(g,x,y0,"l")
    for y in range(y0+1,y1): put(g,x0,y,"l")
    for x in range(x0+1,x1): put(g,x,y1,"B")
    for y in range(y0+1,y1): put(g,x1,y,"B")
def face(g,x0=3,x1=12,y0=4,y1=8):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            if g[y][x] in "bBl": g[y][x]="s"
    for x in range(x0,x1+1):
        if g[y1][x]=="s": g[y1][x]="S"
def outline(g,keep="."):
    o=[r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if g[y][x]!=".": continue
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,ny=x+dx,y+dy
                if 0<=nx<W and 0<=ny<H and g[ny][nx]!=".": o[y][x]="o";break
    return o
def pts(g,c,*xy):
    for i in range(0,len(xy),2): put(g,xy[i],xy[i+1],c)
def line(g,c,x0,y0,x1,y1):
    n=max(abs(x1-x0),abs(y1-y0))
    for i in range(n+1):
        put(g,round(x0+(x1-x0)*i/max(n,1)),round(y0+(y1-y0)*i/max(n,1)),c)
# palette helpers: body main, light, dark, screen, accent, metal, dark-detail
def P(b,l,B,s,a,m="#aab4c4",k="#2a2a3a",y="#ffd23a",r="#ff4a4a",e="#14161e",o="#0e1018",S=None,w="#ffffff",g="#4ae08a"):
    return {"o":o,"b":b,"l":l,"B":B,"s":s,"S":S or s,"a":a,"m":m,"k":k,"y":y,"r":r,"e":e,"w":w,"g":g}
def mid(h): return h
R=[]
def gz(name,feet,move,build,pal,lines,rnd=1,box=(2,3,13,10),eyes=5,face_args=(),speed=1.0):
    g=newg();body(g,*box,rnd=rnd);face(g,*face_args);build(g)
    g=outline(g)
    R.append(dict(name=name,body=["".join(r) for r in g],feet=feet,move=move,pal=pal,lines=lines,eyes=eyes,speed=speed))
# 1 Toaster
def b_toaster(g):
    rect(g,4,1,6,2,"y");rect(g,9,1,11,2,"y");pts(g,"k",3,2,7,2,8,2,12,2);pts(g,"r",14,5,14,6,15,6)
gz("Toaster",True,"walk",b_toaster,P("#c8ccd6","#eef0f6","#8a90a0","#f4e8c8","#ff7a3a"),["*pop!*","i'm toasty","bread? bring me bread","two slices, no regrets"],box=(1,3,14,10))
# 2 Kettle
def b_kettle(g):
    pts(g,"m",0,4,1,4,0,3);rect(g,14,4,15,4,"k");rect(g,15,5,15,7,"k");rect(g,14,8,14,8,"k");rect(g,7,1,8,2,"m");pts(g,"w",5,0,10,0)
gz("Kettle",True,"hop",b_kettle,P("#e8503a","#ff9a80","#a82a1e","#fff2e0","#ffd23a"),["*whistles*","tea time!","i'm steaming (happily)","pour me a cup of friendship"])
# 3 Radio
def b_radio(g):
    line(g,"m",11,3,14,0);pts(g,"r",14,0);pts(g,"k",3,9,5,9,7,9,9,9,11,9);pts(g,"y",12,10)
gz("Radio",True,"walk",b_radio,P("#a8642a","#d89a58","#6a3a14","#c8f0d0","#ffd23a"),["*static*","...and now the weather","tune in!","this next song is for you"],box=(1,4,14,10))
# 4 Fan
def b_fan(g):
    rect(g,2,0,5,1,"a");rect(g,10,0,13,1,"a");rect(g,6,0,9,1,"m");pts(g,"k",7,1,8,1);pts(g,"m",3,5,3,7,12,5,12,7)
gz("Desk Fan",True,"float",b_fan,P("#58b8e8","#a8e0ff","#2a7aa8","#e8f8ff","#ff7aa8"),["*whirrr*","stay cool","spinning is my cardio","breeze incoming"],rnd=1,box=(2,2,13,10))
# 5 Microwave
def b_micro(g):
    rect(g,13,4,14,9,"k");pts(g,"g",13,5,14,5,13,7,14,7);pts(g,"r",14,9)
gz("Microwave",True,"walk",b_micro,P("#d8dce4","#ffffff","#9aa0b0","#243040","#4ae0ff"),["*ding!*","3... 2... 1...","reheating feelings","don't put a fork in me"],box=(1,3,14,10),face_args=(3,12,4,8))
# 6 Washer
def b_wash(g):
    pts(g,"r",3,3,5,3);rect(g,9,3,12,3,"a");pts(g,"m",3,4,12,4,2,5,13,5,2,6,13,6,2,7,13,7,3,8,12,8)
gz("Washing Machine",True,"walk",b_wash,P("#e8ecf4","#ffffff","#a8b0c8","#8ad0f0","#4a7aff"),["*sloshing*","spin cycle!","i love a clean sock","bubbles everywhere"],rnd=1,box=(2,2,13,10))
# 7 Camera
def b_cam(g):
    rect(g,3,2,5,3,"k");rect(g,11,2,12,3,"y");pts(g,"r",7,3,8,3)
gz("Camera",True,"walk",b_cam,P("#3a3e50","#6a708a","#1c1e2a","#a8c8ff","#ff4a4a"),["*click*","say cheese!","hold still...","i'll remember this"],box=(1,4,14,10))
# 8 Typewriter
def b_type(g):
    rect(g,4,0,11,4,"w");pts(g,"k",5,1,6,1,7,1,9,1,5,2,6,2,8,2,9,2,10,2,5,3,7,3);pts(g,"k",3,9,5,9,7,9,9,9,11,9,4,10,6,10,8,10,10,10)
gz("Typewriter",True,"walk",b_type,P("#4a6a5a","#8ab0a0","#2a4034","#f4ecd0","#c0a060"),["*clack clack ding*","dear friend...","once upon a time...","every word counts"],box=(1,5,14,10))
# 9 Gramophone
def b_gram(g):
    for y,(a,b) in enumerate([(13,15),(12,15),(11,14),(10,13)]): rect(g,a,y,b,y,"y")
    pts(g,"m",9,4,10,4)
gz("Gramophone",True,"walk",b_gram,P("#6a3a24","#a8704a","#3a1a0e","#f4e4c0","#ffd23a"),["*crackly waltz*","a song from long ago","needle's sharp, i'm sharper","dance with me"],box=(2,5,13,10))
# 10 Walkie
def b_walkie(g):
    rect(g,12,0,12,2,"k");pts(g,"r",4,2,5,2);pts(g,"k",4,9,6,9,8,9,10,9)
gz("Walkie-Talkie",True,"walk",b_walkie,P("#e8a02a","#ffd078","#a86a10","#d0f4c0","#2a2a3a"),["*krrk* copy that","over!","roger roger","this is blip control"],box=(3,3,12,10))
# 11 Cassette
def b_cass(g):
    rect(g,4,9,11,10,"w");pts(g,"k",5,9,7,9,9,9,6,10,8,10);pts(g,"r",3,3,12,3)
gz("Cassette",True,"walk",b_cass,P("#e84a8a","#ff9ac0","#9a1e58","#fff0f4","#4ae0ff"),["*rewinding*","side A or side B?","mixtape just for you","press play"],box=(1,3,14,10))
# 12 Floppy
def b_floppy(g):
    rect(g,5,2,10,3,"m");pts(g,"k",9,2,9,3);rect(g,4,9,11,10,"w");pts(g,"k",5,9,7,9,9,9)
    g[2][13]=".";g[3][13]="."
gz("Floppy Disk",False,"float",b_floppy,P("#4a6aff","#9ab0ff","#2a3aa8","#f4f4ff","#ff4a4a"),["*save icon noises*","1.44 megabytes of love","please don't bend me","insert disk to continue"],rnd=0,box=(2,2,13,10),face_args=(3,12,4,7))
# 13 CRT
def b_crt(g):
    pts(g,"m",4,1,3,0,11,1,12,0);rect(g,5,10,10,11,"k")
gz("CRT Monitor",True,"walk",b_crt,P("#c8c0a8","#f0ead0","#8a8268","#58e8a8","#ff4a4a"),["*static hiss*","no signal... just kidding","good old days","buffering since 1994"],box=(1,2,14,9),face_args=(2,13,3,8))
# 14 Handheld
def b_hand(g):
    pts(g,"k",4,9,3,10,4,10,5,10,4,11);pts(g,"r",11,9);pts(g,"a",12,10)
gz("Handheld",True,"walk",b_hand,P("#a8a8c0","#e0e0f0","#6a6a88","#a8c898","#8a2aff"),["*8-bit jingle*","one more level...","low battery!","game over? never"],box=(2,1,13,10),face_args=(3,12,2,7),eyes=4)
# 15 Calculator
def b_calc(g):
    for i,(x,y) in enumerate([(4,8),(6,8),(8,8),(10,8),(4,10),(6,10),(8,10),(10,10)]): put(g,x,y,"k" if i%3 else "a")
gz("Calculator",True,"walk",b_calc,P("#2a8a7a","#5ad0b8","#145048","#c8f0d8","#ff7a3a"),["*beep* 5318008","carry the one","i'm good with numbers","equals: happiness"],box=(3,1,12,10),face_args=(4,11,2,7),eyes=4)
# 16 Alarm clock
def b_alarm(g):
    rect(g,3,1,5,2,"y");rect(g,10,1,12,2,"y");rect(g,7,0,8,2,"m");pts(g,"r",7,5,8,5)
gz("Alarm Clock",True,"hop",b_alarm,P("#4aa8e8","#9adcff","#2a6a9a","#fff8e0","#ff4a4a"),["*RRRING*","wake up! wake up!","it's snooze o'clock","5 more minutes..."],box=(2,3,13,10))
# 17 Lamp
def b_lamp(g):
    for y,(a,b) in enumerate([(5,10),(4,11),(3,12),(3,12)]): rect(g,a,y,b,y,"a")
    rect(g,5,3,10,3,"y")
gz("Desk Lamp",True,"hop",b_lamp,P("#7a8a9a","#b8c4d0","#4a5a6a","#fff4c8","#ff9a3a"),["*click* let there be light","bright idea!","i read late with you","glowing review"],box=(2,4,13,10))
# 18 Vacuum
def b_vac(g):
    pts(g,"k",14,3,15,4,15,5,15,6,14,7);rect(g,3,11,5,11,"k");rect(g,10,11,12,11,"k");pts(g,"m",7,2,8,2)
gz("Vacuum",False,"walk",b_vac,P("#e84a4a","#ff9a9a","#9a1e1e","#fff2e0","#ffd23a"),["*vroom*","i suck at... dust","clean sweep!","nom nom crumbs"],box=(2,3,13,10))
# 19 Drone
def b_drone(g):
    rect(g,0,2,3,2,"m");rect(g,12,2,15,2,"m");pts(g,"a",1,1,14,1);pts(g,"k",4,3,11,3,4,11,11,11)
gz("Drone",False,"float",b_drone,P("#3a3e48","#6a7080","#1a1c24","#8ad8ff","#ff4a4a"),["*bzzzzz*","aerial view looks great","battery at 12%","filming everything"],box=(4,4,11,9),face_args=(4,11,5,7),speed=1.2)
# 20 Rover
def b_rover(g):
    rect(g,2,10,4,11,"k");rect(g,7,10,8,11,"k");rect(g,11,10,13,11,"k");rect(g,7,0,8,2,"m");pts(g,"k",6,0,9,0)
gz("Rover",False,"walk",b_rover,P("#d8a868","#f8d8a0","#9a6a38","#c8e8f0","#ff7a3a"),["*beep boop* exploring","found a rock!","phoning home","this planet is cozy"],box=(2,3,13,9))
# 21 Satellite
def b_sat(g):
    for y in range(4,10):
        for x in (0,1,2,3,12,13,14,15): put(g,x,y,"a" if (x+y)%2 else "l")
    rect(g,7,0,8,1,"m");pts(g,"m",6,2,9,2)
gz("Satellite",False,"float",b_sat,P("#c0c8d8","#f0f4ff","#8a92a8","#a8e0ff","#2a4aff"),["*orbit noises*","i see your house!","signal strength: love","spinning round and round"],box=(4,3,11,10),face_args=(4,11,4,8))
# 22 Printer
def b_print(g):
    rect(g,4,1,11,4,"w");pts(g,"k",5,2,6,2,7,2,9,2,10,2,5,3,8,3);rect(g,5,11,10,11,"w")
gz("Printer",True,"walk",b_print,P("#d8dce8","#ffffff","#98a0b8","#2a3a5a","#4ae08a"),["*chk-chk-chk*","paper jam! kidding","printing... printing...","low on ink and feelings"],box=(1,5,14,10),face_args=(3,12,5,8))
# 23 Robot arm
def b_arm(g):
    line(g,"a",4,5,6,0);line(g,"a",5,5,7,0);pts(g,"m",5,0,8,0,6,1,8,1);pts(g,"r",6,3)
gz("Robot Arm",True,"walk",b_arm,P("#e8a02a","#ffd078","#a86a10","#2a3a50","#ff4a4a"),["*servo whirr*","i can pick that up","precision is my thing","need a hand? i have one"],box=(3,6,12,10),face_args=(4,11,6,8),eyes=6)
# 24 Compass
def b_comp(g):
    pts(g,"r",7,1,8,1,7,2,8,2);pts(g,"k",2,6,13,6,7,10,8,10)
gz("Compass",True,"hop",b_comp,P("#b8923a","#f0d078","#7a5a14","#f4ecd0","#ff4a4a"),["*needle spins*","north is that way... i think","adventure awaits","i always find my way"],box=(2,3,13,10))
# 25 Metronome
def b_metro(g):
    for y,cut in ((2,(3,4,5,10,11,12)),(3,(3,4,11,12)),(4,(3,12))):
        for x in cut: g[y][x]="."
    line(g,"m",8,0,10,3);pts(g,"y",10,3,10,2);rect(g,5,10,10,10,"k")
gz("Metronome",True,"hop",b_metro,P("#6a4a8a","#b090d0","#3a2458","#f0e8ff","#ffd23a"),["*tick tock tick tock*","keep the beat","allegro!","i'm always on time"],box=(3,2,12,10))
# 26 Joystick
def b_joy(g):
    rect(g,7,1,8,3,"k");rect(g,6,0,9,0,"r");rect(g,6,1,6,1,"r");rect(g,9,1,9,1,"r");pts(g,"y",3,9,12,9)
gz("Joystick",True,"walk",b_joy,P("#2a2a3a","#5a5a70","#12121a","#a8f0c8","#ff4a4a"),["*click click*","up, up, down, down...","insert coin","player one ready"],box=(2,5,13,10),face_args=(3,12,5,8),eyes=5)
# 27 Bulb
def b_bulb(g):
    for y,cut in ((1,(3,4,11,12)),(2,(3,12))):
        for x in cut: g[y][x]="."
    rect(g,5,10,10,11,"m");pts(g,"k",5,11,7,11,9,11);pts(g,"y",0,5,1,4,14,4,15,5,2,1,13,1)
gz("Light Bulb",False,"float",b_bulb,P("#ffe66a","#fff8b8","#d8b020","#fffbe0","#ff9a3a"),["*bzzt* bright idea!","i'm glowing with pride","screw it, let's go","lights on!"],box=(3,1,12,9),face_args=(3,12,3,8))
# 28 Battery
def b_batt(g):
    rect(g,6,0,9,1,"m");rect(g,4,2,11,3,"a");pts(g,"w",7,2,8,2);pts(g,"g",4,9,5,9,6,9,8,9,9,9,10,9)
gz("Battery",True,"hop",b_batt,P("#4a4a58","#8a8aa0","#24242e","#d8f4d0","#4ae08a"),["*charging...*","full of energy!","+ and - make a pair","recharge me with snacks"],box=(3,2,12,10))
# 29 Telephone
def b_phone(g):
    rect(g,2,2,13,3,"k");rect(g,1,3,2,4,"k");rect(g,13,3,14,4,"k");pts(g,"a",1,4,14,4)
    for x in (4,7,10): put(g,x,9,"k")
gz("Telephone",True,"walk",b_phone,P("#e84a4a","#ff9a9a","#9a1e1e","#f8ecd8","#ffd23a"),["*ring ring*","hello? yes, it's me","wrong number? never","call me maybe"],box=(1,5,14,10),face_args=(3,12,5,8))
# 30 Cuckoo
def b_cuckoo(g):
    for y,(a,b) in enumerate([(6,9),(5,10),(4,11),(3,12)]): rect(g,a,y,b,y,"a")
    pts(g,"y",7,3,8,3);pts(g,"m",7,11,8,11)
gz("Cuckoo Clock",True,"hop",b_cuckoo,P("#8a5a2a","#c89458","#503010","#f8ecd0","#c03a2a"),["*cuckoo! cuckoo!*","it's... time!","tick tock, birdie talk","i pop out for fun"],box=(3,4,12,10),face_args=(4,11,4,8))
json.dump(R,open("wave1.json","w"))
print(len(R))
for r in R[:2]:
    print(r["name"]);print("\n".join(r["body"]))
