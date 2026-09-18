import sys,struct,os
sys.path.insert(0,os.path.dirname(__file__))
from ntt.resource import read_resource
def walk(b,off,end,depth):
    while off+8<=end:
        size,=struct.unpack_from('>I',b,off); tag=b[off+4:off+8][::-1]
        if size<8 or off+size>end or not all(48<=c<91 or c==32 or c==95 for c in tag):
            print('  '*depth+f'@{off:#x} data {end-off}: {b[off:off+48].hex(" ")}'); return
        print('  '*depth+f'@{off:#x} {tag.decode()} {size}: {b[off+8:off+40].hex(" ")}')
        walk(b,off+8,off+size,depth+1) if depth<int(os.environ.get("DEPTH","1")) else None
        off+=size
for p in sys.argv[1:]:
    r=read_resource(p); b=r.body; i=b.find(b'02UN')
    print(p, 'body',len(b),'NU20 at',i, b[:i+4].hex(' '))
    walk(b,i+4,len(b),0)
