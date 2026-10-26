# HungsOS feature upgrades
# This module patches app.py from the GitHub source before app.py is imported.
# It keeps app.py as the canonical source file while allowing large UI upgrades.

CALC_PAGE = r'''
PAGE_CALC_REPLACEMENT
'''

DOPE_BLOCK = r'''
DOPE_HTML = r"""
<h1>🧠 DOPE AI 2.0</h1>
<div class="sub">Neural Reaction Lab · adaptive pattern analysis · random outcomes stay random</div>
<div class="card" style="text-align:center">
 <div class="muted">CURRENT REACTION</div><div id="face" style="font-size:62px;margin:10px">🤔</div>
 <div id="reaction" style="font-size:19px;font-weight:750">Ready</div>
 <div id="detail" class="muted">Run rounds to build an observation history.</div>
</div>
<div class="card">
 <div class="card-title">Prediction</div>
 <div class="row"><span class="muted">Next guess</span><b id="guess">—</b></div>
 <div class="row"><span class="muted">Confidence</span><span id="conf">—</span></div>
 <div class="row"><span class="muted">Strategy</span><span id="strategy">Cold start</span></div>
 <button class="full" id="run">⚡ Run reaction</button>
 <button class="full secondary" id="reset" style="margin-top:9px">Reset experiment</button>
</div>
<div class="grid">
 <div class="card"><div class="muted">ROUNDS</div><div id="rounds" style="font-size:26px;font-weight:750">0</div></div>
 <div class="card"><div class="muted">MATCHES</div><div id="correct" style="font-size:26px;font-weight:750">0</div></div>
 <div class="card"><div class="muted">ACCURACY</div><div id="accuracy" style="font-size:26px;font-weight:750">—</div></div>
</div>
<div class="card">
 <div class="card-title">🧪 What changed</div>
 <p class="muted">2.0 tracks short patterns, long-term transition frequencies, strategy performance and a rolling recent window. It chooses between three lightweight strategies: transition, recent-pattern, and blended.</p>
 <p class="muted">The outcome generator is still random. A high score or confidence value is not proof that future random outcomes can be predicted.</p>
</div>
<div class="card"><div class="card-title">Strategy scoreboard</div><div id="scores" class="muted">No data yet.</div></div>
<div class="card"><div class="card-title">Recent lab log</div><div id="log" class="muted">No rounds yet.</div></div>
<script>
(function(){
var S=['🍎','🌙','⭐','🪐'],L={'🍎':'Apple','🌙':'Moon','⭐':'Star','🪐':'Planet'};
var KEY='dope_neural_reaction_lab_v2';
var st={rounds:0,correct:0,last:'',seq:[],trans:{},strategies:{transition:{ok:0,n:0},recent:{ok:0,n:0},blend:{ok:0,n:0}},log:[]};
try{var z=JSON.parse(localStorage.getItem(KEY)||'null');if(z&&z.trans&&z.strategies)st=z;}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st));}catch(e){}}
function counts(from){var c=st.trans[from]||{},total=0;S.forEach(function(x){total+=c[x]||0;});return {c:c,total:total};}
function transitionGuess(from){var q=counts(from),best=S[0],hi=-1;S.forEach(function(x){if((q.c[x]||0)>hi){hi=q.c[x]||0;best=x;}});return {g:best,conf:q.total?Math.round(hi/q.total*100):25};}
function recentGuess(){var n=Math.min(6,st.seq.length);if(n<2)return {g:S[Math.floor(Math.random()*S.length)],conf:25};var last=st.seq.slice(-n),c={};S.forEach(function(x){c[x]=0;});for(var i=0;i<last.length-1;i++){if(last[i]===last[n-1])c[last[i+1]]++;}var best=S[0],hi=-1,total=0;S.forEach(function(x){total+=c[x];if(c[x]>hi){hi=c[x];best=x;}});return {g:best,conf:total?Math.round(hi/total*100):25};}
function blendGuess(){var a=transitionGuess(st.last),b=recentGuess(),c={};S.forEach(function(x){c[x]=0;});c[a.g]+=0.55;c[b.g]+=0.45;var best=S[0],hi=-1;S.forEach(function(x){if(c[x]>hi){hi=c[x];best=x;}});return {g:best,conf:Math.round(hi*100)};}
function choose(){var opts=[['transition',transitionGuess(st.last)],['recent',recentGuess()],['blend',blendGuess()]];opts.sort(function(a,b){var A=st.strategies[a[0]],B=st.strategies[b[0]],ra=A.n?A.ok/A.n:0,rb=B.n?B.ok/B.n:0;return rb-ra;});if(!st.rounds)return opts[2];return opts[0];}
function render(){rounds.textContent=st.rounds;correct.textContent=st.correct;accuracy.textContent=st.rounds?Math.round(st.correct/st.rounds*100)+'%':'—';var p=choose();guess.textContent=p[1].g+' '+L[p[1].g];conf.textContent=p[1].conf+'% observed-model confidence';strategy.textContent=p[0];var sh='';['transition','recent','blend'].forEach(function(k){var q=st.strategies[k],a=q.n?Math.round(q.ok/q.n*100):0;sh+='<div class="row"><span>'+k+'</span><span>'+q.ok+'/'+q.n+' · '+a+'%</span></div>';});scores.innerHTML=sh;log.innerHTML=st.log.length?st.log.map(function(x){return '<div style="padding:6px 0;border-bottom:1px solid #e7e7ed">'+x+'</div>';}).join(''):'No rounds yet.';}
run.onclick=function(){var p=choose(),out=S[Math.floor(Math.random()*S.length)],hit=p[1].g===out;st.rounds++;if(hit)st.correct++;st.strategies[p[0]].n++;if(hit)st.strategies[p[0]].ok++;if(st.last){if(!st.trans[st.last])st.trans[st.last]={};st.trans[st.last][out]=(st.trans[st.last][out]||0)+1;}st.seq.push(out);if(st.seq.length>120)st.seq.shift();st.last=out;face.textContent=hit?'🤩':(st.rounds%3===0?'😮':'🤔');reaction.textContent=hit?'Prediction matched!':'Unexpected outcome!';detail.textContent='Guess: '+p[1].g+' · result: '+out+' · model: '+p[0];st.log.unshift('#'+st.rounds+' · '+p[0]+' · guess '+p[1].g+' · result '+out+' · '+(hit?'match':'miss'));if(st.log.length>12)st.log.length=12;save();render();};
reset.onclick=function(){st={rounds:0,correct:0,last:'',seq:[],trans:{},strategies:{transition:{ok:0,n:0},recent:{ok:0,n:0},blend:{ok:0,n:0}},log:[]};face.textContent='🤔';reaction.textContent='Ready';detail.textContent='Run rounds to build an observation history.';save();render();};
render();
})();
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

    # Calculator: replace the old simple page_calc() function.
    start = src.find("def page_calc():")
    end = src.find("\n\n# -------------------- EXTRA APPS", start)
    if start >= 0 and end > start:
        replacement = CALC_PAGE_REPLACEMENT.strip()
        if replacement and replacement != "PAGE_CALC_REPLACEMENT":
            src = src[:start] + replacement + src[end:]

    # DOPE AI: replace only the DOPE_HTML block, leaving the arcade and routes intact.
    start = src.find('DOPE_HTML = r"""')
    end = src.find('\n\nGAMES_HTML = r"""', start)
    if start >= 0 and end > start:
        block = DOPE_BLOCK.strip()
        src = src[:start] + block + src[end:]

    if "Calculator Plus" not in src or "DOPE AI 2.0" not in src:
        print("Upgrade: expected sections were not found; leaving app.py unchanged.")
        return

    try:
        with open("app.py", "w") as f:
            f.write(src)
        print("HungsOS upgrades applied: Calculator Plus + DOPE AI 2.0")
    except Exception as e:
        print("Upgrade: cannot write app.py:", e)
