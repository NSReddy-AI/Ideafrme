"""4K upscaler: Real-ESRGAN x4plus in pure numpy (CPU, slow, no PyTorch). Model weights: BSD-3-Clause (xinntao/Real-ESRGAN).
Usage: python esrgan_np.py <in.png> <out.png> [tile]"""
import zipfile, pickle, numpy as np, sys, time, os
from numpy.lib.stride_tricks import sliding_window_view
def load_pth(path):
    z=zipfile.ZipFile(path); pre=z.namelist()[0].split('/')[0]
    class U(pickle.Unpickler):
        def find_class(self,mod,name):
            if name=='_rebuild_tensor_v2':
                def rb(storage,offset,size,stride,*a):
                    arr=storage[offset:offset+int(np.prod(size))] if stride==tuple(np.cumprod((1,)+tuple(size[::-1]))[:-1][::-1]) else None
                    return np.lib.stride_tricks.as_strided(storage[offset:],shape=size,strides=[s*4 for s in stride]).copy()
                return rb
            if name in('FloatStorage',): return 'f'
            if mod=='collections' and name=='OrderedDict':
                import collections; return collections.OrderedDict
            return super().find_class(mod,name)
        def persistent_load(self,pid):
            _,typ,key,loc,n=pid
            return np.frombuffer(z.read(f'{pre}/data/{key}'),dtype=np.float32)
    return U(z.open(f'{pre}/data.pkl')).load()
W=load_pth(os.path.join(os.path.dirname(os.path.abspath(__file__)),'models','RealESRGAN_x4plus.pth')); W=W.get('params_ema',W)
def conv(x,name,act=False):
    w=W[name+'.weight']; b=W[name+'.bias']  # w: (O,I,3,3); x: (I,H,Wd)
    xp=np.pad(x,((0,0),(1,1),(1,1)),mode='constant')
    cols=sliding_window_view(xp,(3,3),axis=(1,2))  # I,H,W,3,3
    y=np.einsum('ihwab,oiab->ohw',cols,w,optimize=True)+b[:,None,None]
    return np.where(y>0,y,0.2*y) if act else y
def rdb(x,p):
    x1=conv(x,p+'.conv1',1); x2=conv(np.concatenate([x,x1]),p+'.conv2',1)
    x3=conv(np.concatenate([x,x1,x2]),p+'.conv3',1); x4=conv(np.concatenate([x,x1,x2,x3]),p+'.conv4',1)
    x5=conv(np.concatenate([x,x1,x2,x3,x4]),p+'.conv5'); return x5*0.2+x
def up2(x): return x.repeat(2,1).repeat(2,2)
def net(img):  # img float32 3,H,W in [0,1]
    f=conv(img,'conv_first'); b=f
    for i in range(23):
        o=b
        for j in (1,2,3): o=rdb(o,f'body.{i}.rdb{j}')
        b=o*0.2+b
    f=f+conv(b,'conv_body')
    f=conv(up2(f),'conv_up1',1); f=conv(up2(f),'conv_up2',1)
    return conv(conv(f,'conv_hr',1),'conv_last')
def upscale(rgb,tile=96,pad=10):
    H,Wd,_=rgb.shape; out=np.zeros((H*4,Wd*4,3),np.float32)
    x=rgb.astype(np.float32).transpose(2,0,1)/255
    for y0 in range(0,H,tile):
        for x0 in range(0,Wd,tile):
            ya,yb=max(0,y0-pad),min(H,y0+tile+pad); xa,xb=max(0,x0-pad),min(Wd,x0+tile+pad)
            t=time.time(); o=net(x[:,ya:yb,xa:xb])
            cy,cx=(y0-ya)*4,(x0-xa)*4; h,w=min(tile,H-y0)*4,min(tile,Wd-x0)*4
            out[y0*4:y0*4+h,x0*4:x0*4+w]=o[:,cy:cy+h,cx:cx+w].transpose(1,2,0)
            print(f'tile {y0},{x0} {time.time()-t:.1f}s',flush=True)
    return (np.clip(out,0,1)*255+0.5).astype(np.uint8)
if __name__=='__main__':
    from PIL import Image
    im=np.array(Image.open(sys.argv[1]).convert('RGB'))
    Image.fromarray(upscale(im,int(sys.argv[3]) if len(sys.argv)>3 else 96)).save(sys.argv[2])
