# HungsOS PC Video Cast receiver
# Packet: HFR1 + uint16 tile_count, then x,y,w,h (uint16 LE) and RGB565 LE pixels.

CAST_PAGE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HungsOS Video Cast</title><style>
body{margin:0;background:#101827;color:#f5f7ff;font:16px Arial;padding:18px}
main{max-width:560px;margin:auto}.card{background:#202d40;border-radius:18px;padding:16px;margin:12px 0}
button,input{padding:12px;border:0;border-radius:12px;margin:5px}button{background:#347fbd;color:white}
video{width:100%;background:#000;border-radius:12px}small{color:#b7c4d8}
</style></head><body><main><h2>HungsOS PC · Video Cast</h2>
<div class="card"><input id="file" type="file" accept="video/*"><video id="v" controls playsinline></video>
<p><button id="start">Start casting</button><button id="stop">Stop</button></p>
<small>Browser-decodes the video, scales to 320×240, and sends changed 16×16 tiles. Initial target: 8 FPS.</small>
<p id="status">Choose a video.</p></div></main><script>
const file=document.getElementById('file'),v=document.getElementById('v'),status=document.getElementById('status');
let running=false,last=null,timer=null,busy=false,frames=0,canvas=document.createElement('canvas');
canvas.width=320;canvas.height=240;const ctx=canvas.getContext('2d',{willReadFrequently:true});
file.onchange=()=>{if(file.files[0]){v.src=URL.createObjectURL(file.files[0]);status.textContent='Ready';}};
function le(n){return [n&255,(n>>8)&255]}
function rgb565(r,g,b){return ((r&248)<<8)|((g&252)<<3)|(b>>3)}
async function sendFrame(){
 if(!running||busy||v.paused||v.ended||v.readyState<2||!v.videoWidth)return;
 busy=true;
 try{
  ctx.fillStyle='#000';ctx.fillRect(0,0,320,240);
  const scale=Math.min(320/v.videoWidth,240/v.videoHeight),w=Math.round(v.videoWidth*scale),h=Math.round(v.videoHeight*scale);
  ctx.drawImage(v,(320-w)/2,(240-h)/2,w,h);
  const pixels=ctx.getImageData(0,0,320,240).data,tiles=[];
  for(let ty=0;ty<240;ty+=16)for(let tx=0;tx<320;tx+=16){
   let changed=!last;
   if(last){for(let yy=ty;yy<Math.min(ty+16,240)&&!changed;yy+=2)for(let xx=tx;xx<Math.min(tx+16,320);xx+=2){
    const i=(yy*320+xx)*4;if(Math.abs(pixels[i]-last[i])>8||Math.abs(pixels[i+1]-last[i+1])>8||Math.abs(pixels[i+2]-last[i+2])>8){changed=true;break;}
   }}
   if(changed){const tw=Math.min(16,320-tx),th=Math.min(16,240-ty),tile=new Uint8Array(8+tw*th*2);
    tile.set([...le(tx),...le(ty),...le(tw),...le(th)],0);let p=8;
    for(let yy=ty;yy<ty+th;yy++)for(let xx=tx;xx<tx+tw;xx++){const i=(yy*320+xx)*4,n=rgb565(pixels[i],pixels[i+1],pixels[i+2]);tile[p++]=n&255;tile[p++]=n>>8;}
    tiles.push(tile);
   }
  }
  const parts=[new Uint8Array([72,70,82,49,...le(tiles.length)])];let total=6;
  for(const tile of tiles){parts.push(tile);total+=tile.length;}
  const packet=new Uint8Array(total);let offset=0;for(const part of parts){packet.set(part,offset);offset+=part.length;}
  const response=await fetch('/video/frame',{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:packet});
  if(!response.ok)throw new Error('receiver HTTP '+response.status);
  last=new Uint8ClampedArray(pixels);frames++;status.textContent='Casting · '+frames+' frames · '+tiles.length+' changed tiles';
 }catch(e){status.textContent='Cast error: '+e.message;running=false;}
 finally{busy=false;}
}
document.getElementById('start').onclick=()=>{if(!v.src){status.textContent='Choose a video first.';return;}running=true;v.play();status.textContent='Starting…';if(timer)clearInterval(timer);timer=setInterval(sendFrame,125);};
document.getElementById('stop').onclick=()=>{running=false;if(timer)clearInterval(timer);timer=null;status.textContent='Stopped';};
</script></body></html>"""

def apply_packet(packet, framebuffer, show):
    if len(packet) < 6 or packet[0:4] != b"HFR1":
        return False
    count = packet[4] | (packet[5] << 8)
    pos = 6
    for _ in range(count):
        if pos + 8 > len(packet):
            return False
        x = packet[pos] | (packet[pos+1] << 8)
        y = packet[pos+2] | (packet[pos+3] << 8)
        w = packet[pos+4] | (packet[pos+5] << 8)
        h = packet[pos+6] | (packet[pos+7] << 8)
        pos += 8
        size = w * h * 2
        if w < 1 or h < 1 or x + w > 320 or y + h > 240 or pos + size > len(packet):
            return False
        for row in range(h):
            src = pos + row * w * 2
            dst = ((y + row) * 320 + x) * 2
            framebuffer[dst:dst+w*2] = packet[src:src+w*2]
        pos += size
    if pos != len(packet):
        return False
    show()
    return True
