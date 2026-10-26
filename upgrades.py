# HungsOS feature upgrades
# Boot-time source patcher: app.py remains the canonical GitHub source.

CALC_PAGE_REPLACEMENT = r'''
def page_calc():
    content = r"""
<h1>Calculator Plus</h1>
<div class="sub">Scientific · history · variables · equations · statistics · table</div>
<div class="card">
<div class="calc-display" id="disp">0</div>
<div class="row"><span class="muted">Angle</span><button id="mode" class="secondary" onclick="toggleMode()">DEG</button></div>
<input id="expr" placeholder="sin(30)+sqrt(16)" inputmode="text" autocomplete="off">
<div class="calc-grid" id="keys"></div>
</div>
<div class="card">
<div class="card-title">Tools</div>
<button class="secondary" onclick="showTool('eq')">Equation</button>
<button class="secondary" onclick="showTool('stat')">Statistics</button>
<button class="secondary" onclick="showTool('table')">Table</button>
<div id="eq" style="display:none;margin-top:12px"><input id="equation" placeholder="2*x+5=17"><button onclick="solveEq()">Solve for x</button><pre id="eqout" class="muted"></pre></div>
<div id="stat" style="display:none;margin-top:12px"><textarea id="nums" style="height:110px" placeholder="Numbers separated by spaces or commas"></textarea><button onclick="statsCalc()">Analyze</button><pre id="statout" class="muted"></pre></div>
<div id="table" style="display:none;margin-top:12px"><input id="fn" placeholder="f(x)=x^2+2*x+1"><div class="row"><input id="start" type="number" value="0" step="any"><input id="step" type="number" value="1" step="any"></div><button onclick="makeTable()">Generate 15 rows</button><pre id="tableout" class="muted"></pre></div>
</div>
<div class="card"><div class="card-title">History</div><div id="hist" class="muted">No calculations yet.</div><button class="danger" onclick="clearHist()">Clear history</button></div>
<script>
(function(){
var E=document.getElementById('expr'),D=document.getElementById('disp'),K=document.getElementById('keys'),angle='DEG',ans=0,vars={A:0,B:0,C:0},history=[];
try{history=JSON.parse(localStorage.getItem('hungos_calc_history_v2')||'[]');}catch(e){}
var keys=[['AC','ac'],['⌫','del'],['(','('],[')',' )'],['7','7'],['8','8'],['9','9'],['÷','/'],['4','4'],['5','5'],['6','6'],['×','*'],['1','1'],['2','2'],['3','3'],['−','-'],['0','0'],['.','.'],['+','+'],['=','eq'],['π','pi'],['e','e'],['^','^'],['%','%'],['sin','sin('],['cos','cos('],['tan','tan('],['asin','asin('],['acos','acos('],['atan','atan('],['ln','ln('],['log','log('],['√','sqrt('],['abs','abs('],['!','!'],['A','A'],['B','B'],['C','C'],['Ans','ans']];
keys.forEach(function(k){var b=document.createElement('button');b.textContent=k[0];b.className=k[1]=='eq'?'eq':(['/','*','-','+','^'].indexOf(k[1])>=0?'op':'fn');b.onclick=function(){press(k[1]);};K.appendChild(b);});
function save(){try{localStorage.setItem('hungos_calc_history_v2',JSON.stringify(history.slice(0,30)));}catch(e){}}
function render(){hist.innerHTML=history.length?history.map(function(x){return '<div style="padding:7px 0;border-bottom:1px solid #e7e7ed"><b>'+x.e+'</b> = '+x.r+'</div>';}).join(''):'No calculations yet.';}
function fmt(n){return Math.abs(n)<1e-12?'0':Number(n.toPrecision(12)).toString();}
function fact(n){if(n<0||n>170||n%1)throw Error('factorial');var r=1;for(var i=2;i<=n;i++)r*=i;return r;}
function evaluate(s){s=s.replace(/×/g,'*').replace(/÷/g,'/').replace(/π/g,'pi').replace(/√/g,'sqrt').replace(/−/g,'-').replace(/\^/g,'**').replace(/\bans\b/gi,'('+ans+')').replace(/\bpi\b/g,'Math.PI').replace(/\be\b/g,'Math.E').replace(/\bA\b/g,'('+vars.A+')').replace(/\bB\b/g,'('+vars.B+')').replace(/\bC\b/g,'('+vars.C+')').replace(/\bsqrt\s*\(/g,'Math.sqrt(').replace(/\babs\s*\(/g,'Math.abs(').replace(/\bln\s*\(/g,'Math.log(').replace(/\blog\s*\(/g,'Math.log10(');
var T={sin:function(x){x=angle=='DEG'?x*Math.PI/180:x;return Math.sin(x);},cos:function(x){x=angle=='DEG'?x*Math.PI/180:x;return Math.cos(x);},tan:function(x){x=angle=='DEG'?x*Math.PI/180:x;return Math.tan(x);},asin:function(x){var q=Math.asin(x);return angle=='DEG'?q*180/Math.PI:q;},acos:function(x){var q=Math.acos(x);return angle=='DEG'?q*180/Math.PI:q;},atan:function(x){var q=Math.atan(x);return angle=='DEG'?q*180/Math.PI:q;}};
s=s.replace(/\bsin\s*\(/g,'T.sin(').replace(/\bcos\s*\(/g,'T.cos(').replace(/\btan\s*\(/g,'T.tan(').replace(/\basin\s*\(/g,'T.asin(').replace(/\bacos\s*\(/g,'T.acos(').replace(/\batan\s*\(/g,'T.atan(').replace(/(\d+(?:\.\d+)?)%/g,'($1/100)').replace(/(\d+(?:\.\d+)?)!/g,'fact($1)');
if(!/^[0-9A-Za-z_+*/().,\s\-]+$/.test(s))throw Error('invalid');var r=Function('T','fact','"use strict";return ('+s+')')(T,fact);if(typeof r!='number'||!Number.isFinite(r))throw Error('math');return r;}
function press(v){if(v=='ac'){E.value='';D.textContent='0';return;}if(v=='del'){E.value=E.value.slice(0,-1);D.textContent=E.value||'0';return;}if(v=='eq'){calc();return;}E.value+=v;D.textContent=E.value||'0';}
function calc(){var e=E.value.trim();if(!e)return;try{var r=evaluate(e);ans=r;D.textContent=fmt(r);E.value=String(r);history.unshift({e:e,r:fmt(r)});history=history.slice(0,30);save();render();}catch(x){D.textContent='Error';}}
window.toggleMode=function(){angle=angle=='DEG'?'RAD':'DEG';mode.textContent=angle;};window.showTool=function(x){['eq','stat','table'].forEach(function(k){document.getElementById(k).style.display=k==x?'block':'none';});};
E.addEventListener('keydown',function(e){if(e.key=='Enter'){calc();e.preventDefault();}});
window.solveEq=function(){var q=equation.value.replace(/\s/g,'');if(q.indexOf('=')<0){eqout.textContent='Use an equation such as 2*x+5=17';return;}var p=q.split('=');if(p.length!=2){eqout.textContent='One = sign only.';return;}function f(x){return evaluate(p[0].replace(/x/gi,'('+x+')'))-evaluate(p[1].replace(/x/gi,'('+x+')'));}var roots=[],px=-100,py;for(var x=-100;x<=100;x+=0.5){try{var y=f(x);if(Math.abs(y)<1e-8)roots.push(x);if(py!==undefined&&y*py<0){var lo=px,hi=x;for(var i=0;i<35;i++){var m=(lo+hi)/2;if(f(lo)*f(m)<=0)hi=m;else lo=m;}roots.push((lo+hi)/2);}py=y;px=x;}catch(e){py=undefined;}}var u=[];roots.forEach(function(r){if(!u.some(function(a){return Math.abs(a-r)<1e-5;}))u.push(r);});eqout.textContent=u.length?'x ≈ '+u.map(fmt).join(', x ≈ '):'No root found in -100..100.';};
window.statsCalc=function(){var a=nums.value.split(/[\s,;]+/).filter(Boolean).map(Number).filter(Number.isFinite);if(!a.length){statout.textContent='Enter numbers.';return;}a.sort(function(x,y){return x-y;});var sum=a.reduce(function(x,y){return x+y;},0),mean=sum/a.length,med=a.length%2?a[(a.length-1)/2]:(a[a.length/2-1]+a[a.length/2])/2,v=a.reduce(function(s,x){return s+(x-mean)*(x-mean);},0)/a.length;statout.textContent='n = '+a.length+'\nmin = '+fmt(a[0])+'\nmax = '+fmt(a[a.length-1])+'\nmean = '+fmt(mean)+'\nmedian = '+fmt(med)+'\npopulation σ = '+fmt(Math.sqrt(v))+'\nsum = '+fmt(sum);};
window.makeTable=function(){var a=Number(start.value),d=Number(step.value),f=fn.value||'x',o='x\tf(x)\n';for(var i=0;i<15;i++){var x=a+i*d;try{o+=fmt(x)+'\t'+fmt(evaluate(f.replace(/\bx\b/g,'('+x+')')))+'\n';}catch(e){o+=fmt(x)+'\tError\n';}}tableout.textContent=o;};window.clearHist=function(){history=[];save();render();};render();
})();
</script>
"""
    return page("Calculator Plus", content)
'''

DOPE_BLOCK = r'''
DOPE_HTML = r"""
<h1>🧠 DOPE AI 2.0</h1>
<div class="sub">Neural Reaction Lab · adaptive pattern analysis · random outcomes stay random</div>
<div class="card" style="text-align:center"><div class="muted">CURRENT REACTION</div><div id="face" style="font-size:62px;margin:10px">🤔</div><div id="reaction" style="font-size:19px;font-weight:750">Ready</div><div id="detail" class="muted">Run rounds to build an observation history.</div></div>
<div class="card"><div class="card-title">Prediction</div><div class="row"><span class="muted">Next guess</span><b id="guess">—</b></div><div class="row"><span class="muted">Confidence</span><span id="conf">—</span></div><div class="row"><span class="muted">Strategy</span><span id="strategy">Cold start</span></div><button class="full" id="run">⚡ Run reaction</button><button class="full secondary" id="reset" style="margin-top:9px">Reset experiment</button></div>
<div class="grid"><div class="card"><div class="muted">ROUNDS</div><div id="rounds" style="font-size:26px;font-weight:750">0</div></div><div class="card"><div class="muted">MATCHES</div><div id="correct" style="font-size:26px;font-weight:750">0</div></div><div class="card"><div class="muted">ACCURACY</div><div id="accuracy" style="font-size:26px;font-weight:750">—</div></div></div>
<div class="card"><div class="card-title">🧪 What changed</div><p class="muted">Tracks short patterns, long-term transitions, strategy performance and a rolling recent window. It compares transition, recent-pattern and blended strategies.</p><p class="muted">The outcome generator is random. Confidence and accuracy are observations, not proof that future random outcomes can be predicted.</p></div>
<div class="card"><div class="card-title">Strategy scoreboard</div><div id="scores" class="muted">No data yet.</div></div><div class="card"><div class="card-title">Recent lab log</div><div id="log" class="muted">No rounds yet.</div></div>
<script>
(function(){var S=['🍎','🌙','⭐','🪐'],L={'🍎':'Apple','🌙':'Moon','⭐':'Star','🪐':'Planet'},KEY='dope_neural_reaction_lab_v2',st={rounds:0,correct:0,last:'',seq:[],trans:{},strategies:{transition:{ok:0,n:0},recent:{ok:0,n:0},blend:{ok:0,n:0}},log:[]};try{var z=JSON.parse(localStorage.getItem(KEY)||'null');if(z&&z.trans&&z.strategies)st=z;}catch(e){}function save(){try{localStorage.setItem(KEY,JSON.stringify(st));}catch(e){}}function trans(f){var c=st.trans[f]||{},best=S[0],hi=-1,total=0;S.forEach(function(x){var n=c[x]||0;total+=n;if(n>hi){hi=n;best=x;}});return {g:best,conf:total?Math.round(hi/total*100):25};}function recent(){var n=Math.min(6,st.seq.length);if(n<2)return {g:S[Math.floor(Math.random()*S.length)],conf:25};var a=st.seq.slice(-n),c={};S.forEach(function(x){c[x]=0;});for(var i=0;i<a.length-1;i++)if(a[i]===a[a.length-1])c[a[i+1]]++;var best=S[0],hi=-1,total=0;S.forEach(function(x){total+=c[x];if(c[x]>hi){hi=c[x];best=x;}});return {g:best,conf:total?Math.round(hi/total*100):25};}function blend(){var a=trans(st.last),b=recent(),c={};S.forEach(function(x){c[x]=0;});c[a.g]+=.55;c[b.g]+=.45;var best=S[0],hi=-1;S.forEach(function(x){if(c[x]>hi){hi=c[x];best=x;}});return {g:best,conf:Math.round(hi*100)};}function choose(){var o=[['transition',trans(st.last)],['recent',recent()],['blend',blend()]];o.sort(function(a,b){var A=st.strategies[a[0]],B=st.strategies[b[0]],x=A.n?A.ok/A.n:0,y=B.n?B.ok/B.n:0;return y-x;});return st.rounds?o[0]:o[2];}function render(){rounds.textContent=st.rounds;correct.textContent=st.correct;accuracy.textContent=st.rounds?Math.round(st.correct/st.rounds*100)+'%':'—';var p=choose();guess.textContent=p[1].g+' '+L[p[1].g];conf.textContent=p[1].conf+'% observed-model confidence';strategy.textContent=p[0];var s='';['transition','recent','blend'].forEach(function(k){var q=st.strategies[k],a=q.n?Math.round(q.ok/q.n*100):0;s+='<div class="row"><span>'+k+'</span><span>'+q.ok+'/'+q.n+' · '+a+'%</span></div>';});scores.innerHTML=s;log.innerHTML=st.log.length?st.log.map(function(x){return '<div style="padding:6px 0;border-bottom:1px solid #e7e7ed">'+x+'</div>';}).join(''):'No rounds yet.';}run.onclick=function(){var p=choose(),out=S[Math.floor(Math.random()*S.length)],hit=p[1].g===out;st.rounds++;if(hit)st.correct++;st.strategies[p[0]].n++;if(hit)st.strategies[p[0]].ok++;if(st.last){if(!st.trans[st.last])st.trans[st.last]={};st.trans[st.last][out]=(st.trans[st.last][out]||0)+1;}st.seq.push(out);if(st.seq.length>120)st.seq.shift();st.last=out;face.textContent=hit?'🤩':(st.rounds%3===0?'😮':'🤔');reaction.textContent=hit?'Prediction matched!':'Unexpected outcome!';detail.textContent='Guess: '+p[1].g+' · result: '+out+' · model: '+p[0];st.log.unshift('#'+st.rounds+' · '+p[0]+' · guess '+p[1].g+' · result '+out+' · '+(hit?'match':'miss'));if(st.log.length>12)st.log.length=12;save();render();};reset.onclick=function(){st={rounds:0,correct:0,last:'',seq:[],trans:{},strategies:{transition:{ok:0,n:0},recent:{ok:0,n:0},blend:{ok:0,n:0}},log:[]};face.textContent='🤔';reaction.textContent='Ready';detail.textContent='Run rounds to build an observation history.';save();render();};render();})();
</script>
"""
'''

def apply():
    try:
        with open("app.py", "r") as f:
            src = f.read()
    except Exception as e:
        print("Upgrade: cannot read app.py:", e)
        return
    start = src.find("def page_calc():")
    end = src.find("\n\n# -------------------- EXTRA APPS", start)
    if start >= 0 and end > start:
        src = src[:start] + CALC_PAGE_REPLACEMENT.strip() + src[end:]
    start = src.find('DOPE_HTML = r"""')
    end = src.find('\n\nGAMES_HTML = r"""', start)
    if start >= 0 and end > start:
        src = src[:start] + DOPE_BLOCK.strip() + src[end:]
    if "Calculator Plus" not in src or "DOPE AI 2.0" not in src:
        print("Upgrade: expected sections were not found; leaving app.py unchanged.")
        return
    try:
        with open("app.py", "w") as f:
            f.write(src)
        print("HungsOS upgrades applied: Calculator Plus + DOPE AI 2.0")
    except Exception as e:
        print("Upgrade: cannot write app.py:", e)
