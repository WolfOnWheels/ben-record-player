import re, json, math
s=open('content.txt','rb').read().decode('latin1')
toks=s.split()
H=841.89
glyphs=[]; color=None; nums=[]; cur=None; sub=[]
def bez(p0,p1,p2,p3,n=6):
    out=[]
    for i in range(1,n+1):
        t=i/n; u=1-t
        out.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0], u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
    return out
for t in toks:
    try: nums.append(float(t)); continue
    except: pass
    if t=='k': color=tuple(nums[-4:])
    elif t=='cm': cur={'tx':nums[-2],'ty':nums[-1],'cmds':[],'subs':[],'color':color}
    elif cur is not None and t=='m':
        cur['cmds'].append(('M',nums[-2:])); cur['subs'].append([tuple(nums[-2:])])
    elif cur is not None and t=='l':
        cur['cmds'].append(('L',nums[-2:])); cur['subs'][-1].append(tuple(nums[-2:]))
    elif cur is not None and t=='c':
        cur['cmds'].append(('C',nums[-6:])); p0=cur['subs'][-1][-1]; cur['subs'][-1]+=bez(p0,tuple(nums[-6:-4]),tuple(nums[-4:-2]),tuple(nums[-2:]))
    elif cur is not None and t=='h': cur['cmds'].append(('Z',[]))
    elif cur is not None and t=='re':
        x,y,w,h=nums[-4:]
        cur['cmds']+= [('M',[x,y]),('L',[x+w,y]),('L',[x+w,y+h]),('L',[x,y+h]),('Z',[])]
        cur['subs'].append([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])
    elif cur is not None and t in ('f','f*'):
        tx,ty=cur['tx'],cur['ty']
        if not cur['subs']:
            nums=[]; continue
        pts=[(tx+x,ty+y) for sp in cur['subs'] for (x,y) in sp]
        area=0;per=0
        for sp in cur['subs']:
            for i in range(len(sp)):
                x0,y0=sp[i-1];x1,y1=sp[i]; area+=x0*y1-x1*y0; per+=math.hypot(x1-x0,y1-y0)
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        # svg path in page coords with y flipped
        d=[]
        for c,a in cur['cmds']:
            if c=='Z': d.append('Z'); continue
            pp=[]
            for i in range(0,len(a),2): pp.append(f"{tx+a[i]:.2f} {H-(ty+a[i+1]):.2f}")
            d.append(c+' '.join(pp))
        glyphs.append({'cx':sum(xs)/len(xs),'cy':H-sum(ys)/len(ys),'w':max(xs)-min(xs),'h':max(ys)-min(ys),
                       'area':abs(area)/2,'per':per,'nsub':len(cur['subs']),'color':cur['color'],'d':''.join(d)})
        cur['cmds']=[];cur['subs']=[]
    nums=[]
json.dump(glyphs,open('glyphs.json','w'))
from collections import Counter
print(len(glyphs))
for c in Counter(g['color'] for g in glyphs): 
    gs=[g for g in glyphs if g['color']==c]; print(c,len(gs), [ (round(g['cx'],1),round(g['cy'],1),round(g['w'],1)) for g in gs[:2]])
