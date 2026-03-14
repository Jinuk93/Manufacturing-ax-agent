"""EDA JSON 데이터와 JS 코드를 data-review.html에 주입"""
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
html_path = project_root / "data-review.html"
json_path = project_root / "dashboards" / "eda_data.json"

# JSON 데이터 로드
with open(json_path, "r", encoding="utf-8") as f:
    eda_json = json.dumps(json.load(f), ensure_ascii=False, separators=(",", ":"))

# HTML 로드
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# JS 코드 블록
eda_js = """
// ═════════════════════════════════════════
// EDA 대시보드 — Plotly.js 기반
// ═════════════════════════════════════════
const EDA_DATA = """ + eda_json + """;

const PLOTLY_LAYOUT = {
  paper_bgcolor:'transparent',plot_bgcolor:'#1e1e1e',
  font:{family:'Pretendard,sans-serif',color:'#ccc',size:12},
  margin:{t:40,b:40,l:50,r:20},
  xaxis:{gridcolor:'rgba(255,255,255,0.06)',zerolinecolor:'rgba(255,255,255,0.1)'},
  yaxis:{gridcolor:'rgba(255,255,255,0.06)',zerolinecolor:'rgba(255,255,255,0.1)'},
  colorway:['#e8770e','#3b82f6','#22c55e','#ef4444','#a855f7','#06b6d4','#f59e0b','#ec4899','#14b8a6','#8b5cf6'],
};
const PLOTLY_CONFIG = {responsive:true,displayModeBar:false};

const SENSOR_DESC = {
  'ActualPosition':['실제 위치 (mm)','CNC 컨트롤러가 측정한 축의 현재 물리적 위치'],
  'CommandPosition':['명령 위치 (mm)','G-code에서 CNC에 지시한 목표 위치'],
  'ActualVelocity':['실제 속도 (mm/s)','축이 실제로 이동하는 속도'],
  'CommandVelocity':['명령 속도 (mm/s)','G-code가 지시한 목표 이동 속도'],
  'ActualAcceleration':['실제 가속도 (mm/s\\u00b2)','축의 가속/감속 정도'],
  'CommandAcceleration':['명령 가속도 (mm/s\\u00b2)','컨트롤러가 계획한 가속도 프로파일'],
  'CurrentFeedback':['모터 전류 (A)','서보 모터에 흐르는 전류. 마모 감지 핵심'],
  'DCBusVoltage':['DC 버스 전압 (V)','서보 드라이브의 전원 전압'],
  'OutputCurrent':['출력 전류 (A)','서보 드라이브가 모터로 출력하는 전류'],
  'OutputVoltage':['출력 전압 (V)','서보 드라이브가 모터에 인가하는 전압'],
  'OutputPower':['출력 전력 (W)','모터가 소비하는 전력. 마모 시 증가 경향'],
  'SystemInertia':['시스템 관성','축 구동계의 관성 모멘트 (상수)'],
  'CURRENT_PROGRAM_NUMBER':['프로그램 번호','실행 중인 NC 프로그램 번호 (상수)'],
};

const AXIS_DESC = {
  'X축':['좌우 이동 (테이블)','워크피스를 좌우로 이동시키는 축. 평면 절삭 시 주요 이송축.'],
  'Y축':['전후 이동 (테이블)','워크피스를 전후로 이동시키는 축. X축과 함께 2D 평면 윤곽 가공.'],
  'Z축':['상하 이동 (주축두)','주축을 상하로 이동시키는 축. 절삭 깊이(depth of cut) 결정.'],
  'S축':['스핀들 회전','공구를 회전시키는 주축. 마모 시 전류/전력 증가 경향.'],
  'M1':['기계 레벨 정보','축 단위가 아닌 기계 전체 레벨의 데이터.'],
};

function getSensorShort(col){const p=col.split('_');return p.length>1?p.slice(1).join('_'):col;}
function getSensorInfo(col){return SENSOR_DESC[getSensorShort(col)]||[col,''];}

let edaCurrentTab='overview';
let edaCurrentGroup=Object.keys(EDA_DATA.sensor_groups)[0];
let edaCurrentExp=Object.keys(EDA_DATA.timeseries)[0];

function renderEdaTab(tab){
  edaCurrentTab=tab;
  document.querySelectorAll('.eda-tab').forEach(t=>t.classList.toggle('active',t.dataset.eda===tab));
  const el=document.getElementById('eda-content');
  const renderers={overview:renderOverview,distribution:renderDistribution,timeseries:renderTimeseries,worn:renderWorn,correlation:renderCorrelation,process:renderProcess};
  if(renderers[tab]) renderers[tab](el);
}

// ── Tab 1: 데이터 개요 ──
function renderOverview(el){
  const k=EDA_DATA.kpi;
  const d=EDA_DATA.label_dist;
  let h='<h3>데이터 개요</h3>';
  h+='<div class="eda-kpi-grid">';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">실험 수</div><div class="eda-kpi-value">'+k.total_experiments+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">총 행 수</div><div class="eda-kpi-value">'+k.total_rows.toLocaleString()+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">유효 센서</div><div class="eda-kpi-value orange">'+k.valid_sensors+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">제거 컬럼</div><div class="eda-kpi-value sm">'+k.removed_columns+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">Worn</div><div class="eda-kpi-value" style="color:#ef4444">'+d.worn+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">Unworn</div><div class="eda-kpi-value" style="color:#22c55e">'+d.unworn+'</div></div>';
  h+='</div>';

  h+='<div class="eda-chart" id="eda-pie-chart" style="height:220px"></div>';
  h+='<h4>실험별 데이터 크기</h4>';
  h+='<div class="eda-chart" id="eda-bar-chart" style="height:280px"></div>';

  h+='<h4>센서 축 그룹 구조</h4>';
  h+='<div class="eda-info">';
  for(const[group,cols] of Object.entries(EDA_DATA.sensor_groups)){
    const ad=AXIS_DESC[group]||[group,''];
    h+='<strong>'+group+' ('+ad[0]+')</strong> — '+cols.length+'개 센서<br>';
  }
  h+='</div>';

  h+='<h4>실험 메타데이터</h4>';
  h+='<div style="overflow-x:auto;"><table class="eda-tbl"><thead><tr><th>실험</th><th>설비</th><th>소재</th><th>이송속도</th><th>클램프</th><th>공구 상태</th><th>행 수</th></tr></thead><tbody>';
  EDA_DATA.experiments.forEach(e=>{
    const cls=e.tool_condition==='worn'?'worn':'unworn';
    h+='<tr><td>'+e.id.replace('experiment_','#')+'</td><td>'+e.equipment+'</td><td>'+e.material+'</td><td>'+e.feedrate+'</td><td>'+e.clamp_pressure+'</td><td class="'+cls+'">'+e.tool_condition+'</td><td>'+e.rows+'</td></tr>';
  });
  h+='</tbody></table></div>';

  h+='<h4>제거 대상 컬럼 ('+EDA_DATA.removed_cols.length+'개)</h4>';
  h+='<div class="eda-info">';
  EDA_DATA.removed_cols.forEach(c=>{
    const info=getSensorInfo(c.col);
    h+='<code>'+c.col+'</code> '+info[0]+' — '+c.reason+'<br>';
  });
  h+='</div>';

  el.innerHTML=h;

  Plotly.newPlot('eda-pie-chart',[{
    values:[d.worn,d.unworn],labels:['Worn','Unworn'],
    type:'pie',marker:{colors:['#ef4444','#22c55e']},
    textinfo:'label+value',textfont:{color:'#fff',size:14},
    hole:0.4
  }],{...PLOTLY_LAYOUT,height:220,margin:{t:10,b:10,l:10,r:10},showlegend:false},PLOTLY_CONFIG);

  const exps=EDA_DATA.experiments;
  Plotly.newPlot('eda-bar-chart',[{
    x:exps.map(e=>e.id.replace('experiment_','#')),
    y:exps.map(e=>e.rows),
    type:'bar',
    marker:{color:exps.map(e=>e.tool_condition==='worn'?'#ef4444':'#22c55e')}
  }],{...PLOTLY_LAYOUT,height:280,xaxis:{...PLOTLY_LAYOUT.xaxis,title:'실험'},yaxis:{...PLOTLY_LAYOUT.yaxis,title:'행 수'}},PLOTLY_CONFIG);
}

// ── Tab 2: 센서 분포 ──
function renderDistribution(el){
  let h='<h3>센서 분포</h3>';
  h+='<p>축 그룹별로 센서의 값 분포를 Box Plot으로 확인합니다.</p>';
  h+='<div class="eda-group-btns" id="eda-dist-groups"></div>';
  h+='<div class="eda-chart" id="eda-box-chart" style="height:420px"></div>';
  h+='<h4>센서별 기초 통계량</h4>';
  h+='<div id="eda-stats-table"></div>';
  el.innerHTML=h;

  const groupBtns=document.getElementById('eda-dist-groups');
  Object.keys(EDA_DATA.sensor_groups).forEach(g=>{
    const btn=document.createElement('button');
    btn.className='eda-group-btn'+(g===edaCurrentGroup?' active':'');
    btn.textContent=g;
    btn.onclick=()=>{edaCurrentGroup=g;renderDistGroup(g);groupBtns.querySelectorAll('.eda-group-btn').forEach(b=>b.classList.toggle('active',b.textContent===g));};
    groupBtns.appendChild(btn);
  });
  renderDistGroup(edaCurrentGroup);
}

function renderDistGroup(group){
  const boxData=EDA_DATA.box_data[group];
  const stats=EDA_DATA.sensor_stats[group];
  if(!boxData) return;

  const traces=boxData.map(b=>({
    type:'box',name:b.col.replace(/^[A-Z]\\d+_/,''),
    lowerfence:[b.min],q1:[b.q1],median:[b.median],q3:[b.q3],upperfence:[b.max],
    boxmean:true,marker:{color:'#e8770e'}
  }));
  Plotly.newPlot('eda-box-chart',traces,{...PLOTLY_LAYOUT,height:420,showlegend:false},PLOTLY_CONFIG);

  let t='<table class="eda-tbl"><thead><tr><th>센서</th><th>평균</th><th>표준편차</th><th>최소</th><th>Q1</th><th>중앙</th><th>Q3</th><th>최대</th><th>왜도</th></tr></thead><tbody>';
  stats.forEach(s=>{
    t+='<tr><td><strong>'+s.col.replace(/^[A-Z]\\d+_/,'')+'</strong></td>';
    t+='<td>'+s.mean+'</td><td>'+s.std+'</td><td>'+s.min+'</td><td>'+s.q25+'</td><td>'+s.median+'</td><td>'+s.q75+'</td><td>'+s.max+'</td><td>'+s.skew+'</td></tr>';
  });
  t+='</tbody></table>';
  document.getElementById('eda-stats-table').innerHTML='<div style="overflow-x:auto">'+t+'</div>';
}

// ── Tab 3: 시계열 패턴 ──
function renderTimeseries(el){
  const expKeys=Object.keys(EDA_DATA.timeseries).sort();

  let h='<h3>시계열 패턴</h3>';
  h+='<p>각 실험의 대표 센서 시계열을 확인합니다. 200포인트로 다운샘플링되었습니다.</p>';
  h+='<select class="eda-select" id="eda-ts-exp">';
  expKeys.forEach(k=>{
    const exp=EDA_DATA.experiments.find(e=>e.id===k);
    const label=k.replace('experiment_','#')+(exp?' ('+exp.tool_condition+')':'');
    h+='<option value="'+k+'"'+(k===edaCurrentExp?' selected':'')+'>'+label+'</option>';
  });
  h+='</select>';
  h+='<div class="eda-chart" id="eda-ts-chart" style="height:500px"></div>';
  h+='<div id="eda-ts-process" class="eda-info" style="margin-top:8px"></div>';
  el.innerHTML=h;

  document.getElementById('eda-ts-exp').onchange=function(){edaCurrentExp=this.value;renderTsChart();};
  renderTsChart();
}

function renderTsChart(){
  const ts=EDA_DATA.timeseries[edaCurrentExp];
  if(!ts) return;
  const sensorKeys=Object.keys(ts).filter(k=>k!=='sequence'&&k!=='process');
  const traces=sensorKeys.map(s=>({
    x:ts.sequence,y:ts[s],type:'scatter',mode:'lines',name:s.replace(/^[A-Z]\\d+_/,''),
    line:{width:1.5}
  }));
  Plotly.newPlot('eda-ts-chart',traces,{
    ...PLOTLY_LAYOUT,height:500,
    xaxis:{...PLOTLY_LAYOUT.xaxis,title:'Sequence'},
    legend:{bgcolor:'transparent',font:{size:11}}
  },PLOTLY_CONFIG);

  if(ts.process){
    const procs=[...new Set(ts.process)];
    document.getElementById('eda-ts-process').innerHTML='<strong>이 실험의 공정 단계:</strong> '+procs.join(' \\u2192 ');
  }
}

// ── Tab 4: Worn vs Unworn ──
function renderWorn(el){
  let h='<h3>Worn vs Unworn 비교</h3>';
  h+='<p>마모(worn)와 정상(unworn) 공구의 센서 분포 차이를 비교합니다.</p>';
  h+='<div class="eda-group-btns" id="eda-worn-groups"></div>';
  h+='<div class="eda-chart" id="eda-worn-chart" style="height:420px"></div>';
  h+='<h4>센서별 차이 상세</h4>';
  h+='<div id="eda-worn-table"></div>';
  el.innerHTML=h;

  const groupBtns=document.getElementById('eda-worn-groups');
  Object.keys(EDA_DATA.worn_comparison).forEach(g=>{
    const btn=document.createElement('button');
    btn.className='eda-group-btn'+(g===edaCurrentGroup?' active':'');
    btn.textContent=g;
    btn.onclick=()=>{edaCurrentGroup=g;renderWornGroup(g);groupBtns.querySelectorAll('.eda-group-btn').forEach(b=>b.classList.toggle('active',b.textContent===g));};
    groupBtns.appendChild(btn);
  });
  renderWornGroup(edaCurrentGroup);
}

function renderWornGroup(group){
  const comp=EDA_DATA.worn_comparison[group];
  if(!comp) return;

  const wornTraces=comp.map(c=>({
    type:'box',name:c.col.replace(/^[A-Z]\\d+_/,'')+'(W)',
    lowerfence:[c.worn_box.min],q1:[c.worn_box.q1],median:[c.worn_box.median],q3:[c.worn_box.q3],upperfence:[c.worn_box.max],
    marker:{color:'#ef4444'},legendgroup:'worn'
  }));
  const unwornTraces=comp.map(c=>({
    type:'box',name:c.col.replace(/^[A-Z]\\d+_/,'')+'(U)',
    lowerfence:[c.unworn_box.min],q1:[c.unworn_box.q1],median:[c.unworn_box.median],q3:[c.unworn_box.q3],upperfence:[c.unworn_box.max],
    marker:{color:'#22c55e'},legendgroup:'unworn'
  }));

  const traces=[];
  for(let i=0;i<comp.length;i++){traces.push(unwornTraces[i]);traces.push(wornTraces[i]);}

  Plotly.newPlot('eda-worn-chart',traces,{...PLOTLY_LAYOUT,height:420,showlegend:false,boxmode:'group'},PLOTLY_CONFIG);

  let t='<div style="overflow-x:auto"><table class="eda-tbl"><thead><tr><th>센서</th><th>Unworn 평균</th><th>Worn 평균</th><th>차이(%)</th><th>Unworn Std</th><th>Worn Std</th><th>Std 비율</th></tr></thead><tbody>';
  comp.forEach(c=>{
    const diffCls=Math.abs(c.diff_pct)>10?'style="color:#f59e0b;font-weight:700"':'';
    t+='<tr><td><strong>'+c.col.replace(/^[A-Z]\\d+_/,'')+'</strong></td>';
    t+='<td class="unworn">'+c.unworn_mean+'</td><td class="worn">'+c.worn_mean+'</td>';
    t+='<td '+diffCls+'>'+c.diff_pct+'%</td>';
    t+='<td>'+c.unworn_std+'</td><td>'+c.worn_std+'</td><td>'+c.std_ratio+'</td></tr>';
  });
  t+='</tbody></table></div>';
  document.getElementById('eda-worn-table').innerHTML=t;
}

// ── Tab 5: 상관관계 ──
function renderCorrelation(el){
  let h='<h3>상관관계</h3>';
  h+='<p>축 그룹별 센서 간 상관행렬(Heatmap)을 확인합니다. |r| > 0.8인 강한 상관 쌍을 하이라이트합니다.</p>';
  h+='<div class="eda-group-btns" id="eda-corr-groups"></div>';
  h+='<div class="eda-chart" id="eda-corr-chart" style="height:450px"></div>';
  h+='<h4>강한 상관 쌍 (|r| > 0.8)</h4>';
  h+='<div id="eda-corr-pairs"></div>';
  el.innerHTML=h;

  const groupBtns=document.getElementById('eda-corr-groups');
  const corrGroups=Object.keys(EDA_DATA.correlations);
  const defaultG=corrGroups.includes(edaCurrentGroup)?edaCurrentGroup:corrGroups[0];
  corrGroups.forEach(g=>{
    const btn=document.createElement('button');
    btn.className='eda-group-btn'+(g===defaultG?' active':'');
    btn.textContent=g;
    btn.onclick=()=>{renderCorrGroup(g);groupBtns.querySelectorAll('.eda-group-btn').forEach(b=>b.classList.toggle('active',b.textContent===g));};
    groupBtns.appendChild(btn);
  });
  renderCorrGroup(defaultG);
}

function renderCorrGroup(group){
  const corr=EDA_DATA.correlations[group];
  if(!corr) return;
  const shortCols=corr.cols.map(c=>c.replace(/^[A-Z]\\d+_/,''));

  Plotly.newPlot('eda-corr-chart',[{
    z:corr.matrix,x:shortCols,y:shortCols,
    type:'heatmap',colorscale:[[0,'#1e3a5f'],[0.5,'#1a1a1a'],[1,'#e8770e']],
    zmin:-1,zmax:1,
    text:corr.matrix.map(row=>row.map(v=>v.toFixed(2))),
    texttemplate:'%{text}',textfont:{size:10,color:'#ccc'},
    hovertemplate:'%{x} vs %{y}: %{z:.3f}<extra></extra>'
  }],{...PLOTLY_LAYOUT,height:450,margin:{t:20,b:80,l:100,r:20}},PLOTLY_CONFIG);

  let pairs='<div class="eda-info">';
  if(corr.strong_pairs.length===0){pairs+='이 그룹에는 |r| > 0.8인 강한 상관 쌍이 없습니다.';}
  else{
    corr.strong_pairs.forEach(p=>{
      const color=p.r>0?'#22c55e':'#ef4444';
      pairs+='<span style="color:'+color+';font-weight:700">r='+p.r+'</span> '+p.a.replace(/^[A-Z]\\d+_/,'')+' \\u2194 '+p.b.replace(/^[A-Z]\\d+_/,'')+'<br>';
    });
  }
  pairs+='</div>';
  document.getElementById('eda-corr-pairs').innerHTML=pairs;
}

// ── Tab 6: 공정 단계 ──
function renderProcess(el){
  const proc=EDA_DATA.process;
  let h='<h3>공정 단계</h3>';
  h+='<p>가공 공정(Machining_Process) 10단계의 데이터 분포와 센서 패턴을 확인합니다.</p>';

  h+='<div class="eda-chart" id="eda-proc-bar" style="height:320px"></div>';

  if(proc.sensor_by_process){
    h+='<h4>공정별 '+proc.sensor_by_process.sensor+' 평균</h4>';
    h+='<div class="eda-chart" id="eda-proc-sensor" style="height:320px"></div>';
  }

  if(proc.worn_by_process){
    h+='<h4>공정별 Worn vs Unworn 비교 ('+proc.sensor_by_process.sensor+')</h4>';
    h+='<div class="eda-chart" id="eda-proc-worn" style="height:320px"></div>';
  }

  el.innerHTML=h;

  const procNames=Object.keys(proc.counts);
  const procCounts=Object.values(proc.counts);
  Plotly.newPlot('eda-proc-bar',[{
    x:procNames,y:procCounts,type:'bar',marker:{color:'#e8770e'}
  }],{...PLOTLY_LAYOUT,height:320,xaxis:{...PLOTLY_LAYOUT.xaxis,title:'공정 단계',tickangle:-30},yaxis:{...PLOTLY_LAYOUT.yaxis,title:'행 수'}},PLOTLY_CONFIG);

  if(proc.sensor_by_process){
    const spd=proc.sensor_by_process.data;
    Plotly.newPlot('eda-proc-sensor',[{
      x:spd.map(d=>d.process),y:spd.map(d=>d.mean),
      type:'bar',marker:{color:'#3b82f6'},
      error_y:{type:'data',array:spd.map(d=>d.std),visible:true,color:'#666'}
    }],{...PLOTLY_LAYOUT,height:320,xaxis:{...PLOTLY_LAYOUT.xaxis,tickangle:-30},yaxis:{...PLOTLY_LAYOUT.yaxis,title:'평균 전력 (W)'}},PLOTLY_CONFIG);
  }

  if(proc.worn_by_process){
    const wornData=proc.worn_by_process.filter(d=>d.condition==='worn');
    const unwornData=proc.worn_by_process.filter(d=>d.condition==='unworn');
    Plotly.newPlot('eda-proc-worn',[
      {x:unwornData.map(d=>d.process),y:unwornData.map(d=>d.mean),type:'bar',name:'Unworn',marker:{color:'#22c55e'}},
      {x:wornData.map(d=>d.process),y:wornData.map(d=>d.mean),type:'bar',name:'Worn',marker:{color:'#ef4444'}}
    ],{...PLOTLY_LAYOUT,height:320,barmode:'group',xaxis:{...PLOTLY_LAYOUT.xaxis,tickangle:-30},yaxis:{...PLOTLY_LAYOUT.yaxis,title:'평균 전력 (W)'},legend:{bgcolor:'transparent'}},PLOTLY_CONFIG);
  }
}

// ── EDA 탭 이벤트 바인딩 ──
document.querySelectorAll('.eda-tab').forEach(tab=>{
  tab.addEventListener('click',()=>renderEdaTab(tab.dataset.eda));
});
renderEdaTab('overview');
"""

# Insert before </script>
marker = "</script>"
idx = html.rfind(marker)
if idx == -1:
    print("ERROR: </script> not found")
else:
    html = html[:idx] + eda_js + "\n" + html[idx:]
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK - JS inserted. Final file size: {len(html):,} bytes ({len(html)//1024} KB)")
