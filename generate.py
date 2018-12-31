from datetime import datetime
from calendar import monthrange,month_name,TextCalendar
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import requests
import json
import re

LEAGUES = {'NHL':{1:['Devils',(203,7,41),(0,0,0)],2:['Islanders',(0,46,137),(255,74,0)],
                  3:['Rangers',(0,56,168),(206,17,38)],4:['Flyers',(253,67,0),(0,0,0)],
                  5:['Penguins',(255,183,15),(0,0,0)],6:['Bruins',(255,184,0),(45,41,38)],
                  7:['Sabres',(0,33,71),(255,183,15)],8:['Canadiens',(168,21,43),(0,28,99)],
                  9:['Senators',(203,7,41),(200,147,0)],10:['Maple Leafs',(0,36,101),(255,255,255)],
                  12:['Hurricanes',(207,10,38),(0,0,0)],13:['Panthers',(204,11,45),(13,33,69)],
                  14:['Lightning',(255,255,255),(0,31,93)],15:['Capitals',(203,7,41),(0,29,66)],
                  16:['Blackhawks',(207,10,44),(0,0,0)],17:['Red Wings',(204,9,47),(255,255,255)],
                  18:['Predators',(255,184,0),(0,29,67)],19:['Blues',(255,184,0),(0,46,136)],
                  20:['Flames',(203,7,41),(244,191,62)],21:['Avalanche',(113,37,61),(26,96,147)],
                  22:['Oilers',(255,81,19),(0,33,71)],23:['Canucks',(0,31,92),(151,153,155)],
                  24:['Ducks',(249,86,2),(0,0,0)],25:['Stars',(0,99,64),(162,170,173)],
                  26:['Kings',(255,255,255),(161,170,173)],28:['Sharks',(0,98,115),(235,113,0)],
                  29:['Blue Jackets',(0,29,66),(203,7,41)],30:['Wild',(19,72,52),(168,21,43)],
                  52:['Jets',(0,29,67),(169,22,43)],53:['Coyotes',(135,36,49),(222,203,162)],
                  54:['Golden Knights',(0,0,0),(141,116,74)]}}
                  
DIMENSIONS = (1242,2688)
WEEKDAYS = '   S    M     T    W    T     F     S'
MONTH_OFFSET = [0,170,140,230,310,350,330,340,220,110,190,120,140]
GAME_SIZE = 170,170
LOGO_SIZE = 1000,1000
GAME_START = (99,1575)
BACK_START = (123,1565)
GAME_W = 148
GAME_H = 177

def get_team_id(league, name):
    if league == 'NHL':
        for team in LEAGUES['NHL'].keys():
            if name.title() == LEAGUES['NHL'][team][0]:
                return team
        return -1
    else:
        return -1
        
def get_team_calendar(league, id, month=datetime.now().month, year=datetime.now().year):
    firstDay,numDays = monthrange(year,month)
    if league == 'NHL':
        params = {'startDate':'%d-%02d-01' % (year,month),'endDate':'%d-%02d-%d' % (year,month,numDays),'teamId':id}
        response = requests.get('https://statsapi.web.nhl.com/api/v1/schedule',params=params)
        data = response.json()
        games = {}
        print month_name[month], year
        for game in data['dates']:
            home = True
            day = datetime.strptime(game['date'],'%Y-%m-%d').day
            teams = [game['games'][0]['teams']['away']['team']['id'],game['games'][0]['teams']['home']['team']['id']]
            print str(day)+':',game['games'][0]['teams']['away']['team']['name'],'@',game['games'][0]['teams']['home']['team']['name']
            if teams[0] == id:
                home = False
            teams.remove(id)
            games[day] = (teams[0],home)
        return games
    else:
        return -1
        
def generate_wallpaper(league, team, month=datetime.now().month, year=datetime.now().year):
    id = get_team_id(league,team)
    bcolor = LEAGUES[league][id][1]
    fcolor = LEAGUES[league][id][2]
    cal = TextCalendar(6).formatmonth(year,month,w=4,l=2)
    cal = re.sub(r' (\d\W)',r'  \1',cal)
    caln = cal.split('\n\n')
    caln[1] = WEEKDAYS
    numDays = sum(c.isdigit() for c in caln[2])
    if numDays < 5:
        caln[2] = ' ' + caln[2]
        cal = re.sub(r'9*(10\W)',r' \1',cal)
    caln[2] = (7-numDays)*'  ' + caln[2]
    cal = '\n\n'.join(caln[1:])
    team_sch = get_team_calendar(league, id, month=month, year=year)
    # for game in team_sch, break up cal to find which row/col the day is in, if in the first week use numDays to find col, use dict of arrays to store offsets
    weeks = [0,numDays+1,0,0,0,0]
    for week in [2,3,4,5]:
        weeks[week] = weeks[week-1] + 7
    
    c_fnt = ImageFont.truetype('fonts/LeelaUIb.ttf',78)
    m_fnt = ImageFont.truetype('fonts/LeelaUIb.ttf',156)
    
    background = Image.new('RGBA', DIMENSIONS, color = bcolor)
    d = ImageDraw.Draw(background)
    d.text((100,1400), cal, font=c_fnt, fill=fcolor)
    d.text((100+MONTH_OFFSET[month],1200), month_name[month].upper(), font=m_fnt, fill=fcolor)
    
    logo = Image.open('images/NHL/' + str(id) + '.png')
    logo.thumbnail(LOGO_SIZE, Image.ANTIALIAS)
    bg_w, bg_h = background.size
    logo_w, logo_h = logo.size
    offset = ((bg_w - logo_w) // 2, (bg_h - logo_h) // 4)
    background.paste(logo,offset,logo)
    
    gm_b = Image.new('RGB',(GAME_SIZE[0]-50,GAME_SIZE[1]-50), color = bcolor)
    draw = ImageDraw.Draw(gm_b,'RGBA')
    w = 0
    
    
    for game in team_sch.keys():
        t_fcolor = fcolor + (125,)
        team,home = team_sch[game]
        if w != 5 and game >= weeks[w+1]:
            w += 1
        if w == 0:
            d = (7-numDays) + (game - 1)
        else:
            d = game - weeks[w]
        offs = (BACK_START[0]+d*GAME_W,BACK_START[1]+w*GAME_H)
        background.paste(gm_b,offs)
        offs = (GAME_START[0]+d*GAME_W,GAME_START[1]+w*GAME_H)
        
        if home:
            draw.ellipse((0,0,GAME_SIZE[0]-50,GAME_SIZE[1]-50), fill=t_fcolor)
    
        gm = Image.open('images/NHL/'+str(team)+'.png').convert('RGBA')
        gm.thumbnail(GAME_SIZE, Image.ANTIALIAS)
        background.paste(gm,offs,gm)
    
    background.save('test'+str(month)+'.png')
    

#print get_team_id('NHL','Jets')
for i in [10,11,12,1,2,3,4]:
    if i < 4:
        generate_wallpaper('NHL','Capitals',month=i,year=2019)
    else:
        generate_wallpaper('NHL','Capitals',month=i,year=2018)