"""renderOverview 함수를 상세 교육적 버전으로 교체"""
with open('data-review.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_start = content.find('function renderOverview(el){')
old_end = content.find('\n// \u2500\u2500 Tab 2:', old_start)

new_func = """function renderOverview(el){
  const k=EDA_DATA.kpi;
  const d=EDA_DATA.label_dist;
  let h='';

  // \u2500 \uc139\uc158 0: \uc774 \ub370\uc774\ud130\ub294 \ubb34\uc5c7\uc778\uac00? \u2500
  h+='<h3>\uc774 \ub370\uc774\ud130\ub294 \ubb34\uc5c7\uc778\uac00?</h3>';
  h+='<div class="eda-info">';
  h+='<strong style="font-size:15px;color:#e8770e;">Kaggle CNC Mill Tool Wear Dataset</strong><br><br>';
  h+='\uc774 \ub370\uc774\ud130\uc14b\uc740 <strong>\ubbf8\uc2dc\uac04 \ub300\ud559\uad50(University of Michigan) SMART Lab</strong>\uc5d0\uc11c \uc218\ud589\ud55c \uc2e4\uc81c CNC \ubc00\ub9c1 \uc2e4\ud5d8\uc5d0\uc11c \uc218\uc9d1\ub41c \uac83\uc785\ub2c8\ub2e4.<br>';
  h+='<strong>\uc655\uc2a4(wax)</strong> \uc18c\uc7ac\ub97c CNC \ubc00\ub9c1 \uba38\uc2e0\uc73c\ub85c \uac00\uacf5\ud558\uba74\uc11c, ';
  h+='CNC \ucee8\ud2b8\ub864\ub7ec(SCADA \ub808\ubca8)\uac00 <strong>100ms \uac04\uaca9</strong>\uc73c\ub85c \uc13c\uc11c\uac12\uc744 \uae30\ub85d\ud588\uc2b5\ub2c8\ub2e4.<br><br>';
  h+='<strong>\uc6b0\ub9ac \ud504\ub85c\uc81d\ud2b8\uc5d0\uc11c\uc758 \uc5ed\ud560:</strong><br>';
  h+='\uc774 \uc13c\uc11c \ub370\uc774\ud130\ub97c \ubd84\uc11d\ud558\uc5ec <strong>"\uacf5\uad6c\uac00 \ub9c8\ubaa8\ub418\uc5c8\ub294\uc9c0(worn) \uc544\ub2cc\uc9c0(unworn)"\ub97c \uc608\uce21</strong>\ud558\ub294 \uac83\uc774 \ud575\uc2ec \ubaa9\ud45c\uc785\ub2c8\ub2e4.<br>';
  h+='\uc989, \uc13c\uc11c \ud328\ud134\ub9cc \ubcf4\uace0 \uacf5\uad6c \uc0c1\ud0dc\ub97c \uc790\ub3d9\uc73c\ub85c \ud310\ub2e8\ud558\ub294 <strong>\uc608\uc9c0\ubcf4\uc804(Predictive Maintenance)</strong> \uc2dc\uc2a4\ud15c\uc758 \uae30\ucd08 \ub370\uc774\ud130\uc785\ub2c8\ub2e4.';
  h+='</div>';

  // \u2500 \uc139\uc158 1: \ub370\uc774\ud130 \ucd9c\ucc98 3\uc885 \u2500
  h+='<h4>\ub370\uc774\ud130 \ucd9c\ucc98 \uad6c\uc870</h4>';
  h+='<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:12px 0;">';

  h+='<div class="eda-info" style="border-left:3px solid #e8770e;">';
  h+='<strong style="color:#e8770e;">SCADA / CNC \ucee8\ud2b8\ub864\ub7ec</strong><br>';
  h+='<span style="font-size:12px;color:#888;">experiment_01~18.csv</span><br><br>';
  h+='X, Y, Z\ucd95 \uc11c\ubcf4 \ubaa8\ud130 \uc13c\uc11c<br>';
  h+='S\ucd95 (\uc2a4\ud540\ub4e4) \ud68c\uc804 \uc13c\uc11c<br>';
  h+='\uc704\uce58/\uc18d\ub3c4/\uac00\uc18d\ub3c4/\uc804\ub958/\uc804\uc555/\uc804\ub825<br>';
  h+='100ms \uc8fc\uae30\ub85c \uc2e4\uc2dc\uac04 \uc218\uc9d1<br><br>';
  h+='\u2192 <strong>48\uac1c \ucee8\ub7fc</strong> (\uc13c\uc11c \uc2dc\uacc4\uc5f4)';
  h+='</div>';

  h+='<div class="eda-info" style="border-left:3px solid #3b82f6;">';
  h+='<strong style="color:#3b82f6;">MES (\uc2e4\ud5d8 \uba54\ud0c0\ub370\uc774\ud130)</strong><br>';
  h+='<span style="font-size:12px;color:#888;">train.csv</span><br><br>';
  h+='\uc2e4\ud5d8 \ubc88\ud638 (experiment_no)<br>';
  h+='\uc18c\uc7ac \uc885\ub958 (material: wax)<br>';
  h+='\uc774\uc1a1\uc18d\ub3c4 (feedrate)<br>';
  h+='\ud074\ub7a8\ud504 \uc555\ub825 (clamp_pressure)<br>';
  h+='\uac00\uacf5 \uc644\ub8cc \uc5ec\ubd80<br><br>';
  h+='\u2192 <strong>\uc2e4\ud5d8 \uc870\uac74 + \uacb0\uacfc \ub77c\ubca8</strong>';
  h+='</div>';

  h+='<div class="eda-info" style="border-left:3px solid #22c55e;">';
  h+='<strong style="color:#22c55e;">\ud488\uc9c8 \uac80\uc0ac (\ub77c\ubca8)</strong><br>';
  h+='<span style="font-size:12px;color:#888;">train.csv\uc758 tool_condition</span><br><br>';
  h+='\uc2e4\ud5d8 \ud6c4 \uac80\uc0ac\uad00\uc774 \uacf5\uad6c \uc0c1\ud0dc\ub97c \ud310\uc815<br>';
  h+='<span class="worn">worn</span> = \ub9c8\ubaa8\ub428 (\uad50\uccb4 \ud544\uc694)<br>';
  h+='<span class="unworn">unworn</span> = \uc815\uc0c1 (\uacc4\uc18d \uc0ac\uc6a9 \uac00\ub2a5)<br><br>';
  h+='\u2192 \uc774\uac83\uc774 \uc6b0\ub9ac\uc758 <strong>\uc608\uce21 \ub300\uc0c1(Target)</strong><br>';
  h+='\uc13c\uc11c \ud328\ud134\ub9cc \ubcf4\uace0 "\ub9c8\ubaa8 \uc5ec\ubd80" \uc608\uce21';
  h+='</div>';
  h+='</div>';

  // \u2500 \uc139\uc158 2: \ud575\uc2ec \uc218\uce58 KPI \u2500
  h+='<h4>\ud575\uc2ec \uc218\uce58 \ud55c\ub208\uc5d0 \ubcf4\uae30</h4>';
  h+='<div class="eda-kpi-grid">';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">\uc2e4\ud5d8 \uc218</div><div class="eda-kpi-value">'+k.total_experiments+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">\ucd1d \ud589 \uc218</div><div class="eda-kpi-value">'+k.total_rows.toLocaleString()+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">\uc720\ud6a8 \uc13c\uc11c</div><div class="eda-kpi-value orange">'+k.valid_sensors+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">\uc81c\uac70 \ucee8\ub7fc</div><div class="eda-kpi-value sm">'+k.removed_columns+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">Worn (\ub9c8\ubaa8)</div><div class="eda-kpi-value" style="color:#ef4444">'+d.worn+'</div></div>';
  h+='<div class="eda-kpi"><div class="eda-kpi-label">Unworn (\uc815\uc0c1)</div><div class="eda-kpi-value" style="color:#22c55e">'+d.unworn+'</div></div>';
  h+='</div>';
  h+='<div class="eda-info" style="font-size:12px;color:#888;">';
  h+='<strong>\uc218\uce58 \ud574\uc11d:</strong> 18\uac1c \uc2e4\ud5d8\uc5d0\uc11c \ucd1d 25,286\ud589\uc758 \uc13c\uc11c \ub370\uc774\ud130\uac00 \uc218\uc9d1\ub418\uc5c8\uc2b5\ub2c8\ub2e4. ';
  h+='\uc6d0\ubcf8 48\uac1c \ucee8\ub7fc \uc911 \uc0c1\uc218\uac12\uc774\uac70\ub098 \uc804\ubd80 0\uc778 5\uac1c\ub97c \uc81c\uac70\ud558\uba74 \uc720\ud6a8 42\uac1c \uc13c\uc11c\uac00 \ub0a8\uc2b5\ub2c8\ub2e4. ';
  h+='Worn 10\uac1c vs Unworn 8\uac1c\ub85c \uc57d\uac04 \ubd88\uade0\ud615\uc774\uc9c0\ub9cc \uc2ec\uac01\ud558\uc9c0 \uc54a\uc740 \uc218\uc900\uc785\ub2c8\ub2e4.';
  h+='</div>';

  // \u2500 \uc139\uc158 3: \uacf5\uad6c \uc0c1\ud0dc \ubd84\ud3ec \u2500
  h+='<h4>\uacf5\uad6c \uc0c1\ud0dc \ubd84\ud3ec \u2014 Worn vs Unworn\uc774\ub780?</h4>';
  h+='<div class="eda-info">';
  h+='<strong>Worn (\ub9c8\ubaa8)</strong> = \uac00\uacf5 \ud6c4 \uacf5\uad6c \ub0a0\uc774 \ub2f3\uc544\uc11c \uad50\uccb4\uac00 \ud544\uc694\ud55c \uc0c1\ud0dc. ';
  h+='\ub9c8\ubaa8\ub41c \uacf5\uad6c\ub85c \uacc4\uc18d \uac00\uacf5\ud558\uba74 \ud488\uc9c8 \uc800\ud558, \uce58\uc218 \uc624\ucc28, \uc2ec\ud558\uba74 \uacf5\uad6c \ud30c\uc190\uc774 \ubc1c\uc0dd\ud569\ub2c8\ub2e4.<br>';
  h+='<strong>Unworn (\uc815\uc0c1)</strong> = \uacf5\uad6c \ub0a0\uc774 \uc544\uc9c1 \ucda9\ubd84\ud788 \ub0a0\uce74\ub85c\uc6cc \uacc4\uc18d \uc0ac\uc6a9\ud560 \uc218 \uc788\ub294 \uc0c1\ud0dc.<br><br>';
  h+='<strong>\uc654 \uc911\uc694\ud55c\uac00?</strong><br>';
  h+='\uc2e4\uc81c \ud604\uc7a5\uc5d0\uc11c\ub294 \uac00\uacf5\uc744 \uba48\ucd94\uace0 \uacf5\uad6c\ub97c \ube7c\uc11c \uac80\uc0ac\ud574\uc57c \ub9c8\ubaa8 \uc5ec\ubd80\ub97c \uc54c \uc218 \uc788\uc2b5\ub2c8\ub2e4. ';
  h+='\uc774 \ud504\ub85c\uc81d\ud2b8\ub294 <strong>\uc13c\uc11c \ub370\uc774\ud130\ub9cc\uc73c\ub85c \uacf5\uad6c \uc0c1\ud0dc\ub97c \uc790\ub3d9 \ud310\ub2e8</strong>\ud558\uc5ec ';
  h+='\ubd88\ud544\uc694\ud55c \uc815\uc9c0 \uc5c6\uc774 \uc801\uc808\ud55c \uc2dc\uc810\uc5d0 \uad50\uccb4\ud560 \uc218 \uc788\uac8c \ud558\ub294 \uac83\uc774 \ubaa9\ud45c\uc785\ub2c8\ub2e4.';
  h+='</div>';
  h+='<div class="eda-chart" id="eda-pie-chart" style="height:220px"></div>';

  // \u2500 \uc139\uc158 4: \uc2e4\ud5d8\uc774\ub780 \ubb34\uc5c7\uc778\uac00? \u2500
  h+='<h4>\uc2e4\ud5d8\ubcc4 \ub370\uc774\ud130 \ud06c\uae30 \u2014 "\uc2e4\ud5d8"\uc774\ub780?</h4>';
  h+='<div class="eda-info">';
  h+='<strong>\uc2e4\ud5d8(Experiment)</strong>\uc774\ub780 \ud55c \ubc88\uc758 CNC \ubc00\ub9c1 \uac00\uacf5 \uc791\uc5c5\uc744 \uc758\ubbf8\ud569\ub2c8\ub2e4.<br>';
  h+='\ubbf8\uc2dc\uac04\ub300 \uc5f0\uad6c\ud300\uc774 \ucd1d 18\ubc88\uc758 \uac00\uacf5 \uc2e4\ud5d8\uc744 \uc218\ud589\ud588\uace0, \uac01 \uc2e4\ud5d8\ub9c8\ub2e4 ';
  h+='<strong>\uc774\uc1a1\uc18d\ub3c4(feedrate)</strong>\uc640 <strong>\ud074\ub7a8\ud504 \uc555\ub825(clamp_pressure)</strong>\uc744 \ub2e4\ub974\uac8c \uc124\uc815\ud558\uc5ec \ub2e4\uc591\ud55c \uc870\uac74\uc5d0\uc11c\uc758 \uc13c\uc11c \ubc18\uc751\uc744 \uae30\ub85d\ud588\uc2b5\ub2c8\ub2e4.<br><br>';
  h+='<strong>\uc2e4\ud5d8\ubcc4 \ud589 \uc218\uac00 \ub2e4\ub978 \uc774\uc720:</strong><br>';
  h+='\uac00\uacf5 \uc2dc\uac04\uc774 \uc2e4\ud5d8\ub9c8\ub2e4 \ub2e4\ub974\uae30 \ub54c\ubb38\uc785\ub2c8\ub2e4. \uc774\uc1a1\uc18d\ub3c4\uac00 \ub290\ub9ac\uba74 \uac00\uacf5\uc5d0 \uc624\ub798 \uac78\ub824 \ud589 \uc218\uac00 \ub9ce\uace0, \ube60\ub974\uba74 \uc801\uc2b5\ub2c8\ub2e4. ';
  h+='\ub610\ud55c \uc77c\ubd80 \uc2e4\ud5d8(#04, #05, #07)\uc740 \uac00\uacf5\uc774 \uc911\uac04\uc5d0 \uc911\ub2e8(<code>machining_finalized=no</code>)\ub418\uc5b4 \ud589 \uc218\uac00 \ud2b9\ud788 \uc801\uc2b5\ub2c8\ub2e4.<br><br>';
  h+='<strong>\ud574\uc11d \ud3ec\uc778\ud2b8:</strong><br>';
  h+='\ube68\uac04\uc0c9 = worn(\ub9c8\ubaa8), \ucd08\ub85d\uc0c9 = unworn(\uc815\uc0c1). ';
  h+='\ub9c8\ubaa8\ub41c \uacf5\uad6c\ub85c \uac00\uacf5\ud55c \uc2e4\ud5d8\ub3c4, \uc815\uc0c1 \uacf5\uad6c\ub85c \uac00\uacf5\ud55c \uc2e4\ud5d8\ub3c4 \ud589 \uc218\uc5d0 \ud070 \ucc28\uc774\ub294 \uc5c6\uc2b5\ub2c8\ub2e4. ';
  h+='\uc989, \ub370\uc774\ud130 \uc591 \uc790\uccb4\uac00 \uc544\ub2c8\ub77c <strong>\uc13c\uc11c\uac12\uc758 \ud328\ud134 \ucc28\uc774</strong>\ub85c \ub9c8\ubaa8\ub97c \uad6c\ubd84\ud574\uc57c \ud569\ub2c8\ub2e4.';
  h+='</div>';
  h+='<div class="eda-chart" id="eda-bar-chart" style="height:280px"></div>';

  // \u2500 \uc139\uc158 5: \uc2e4\ud5d8 \uc870\uac74 \uba54\ud0c0\ub370\uc774\ud130 \uc124\uba85 \u2500
  h+='<h4>\uc2e4\ud5d8 \uc870\uac74 (MES \uba54\ud0c0\ub370\uc774\ud130) \u2014 \uac01 \ud56d\ubaa9\uc758 \uc758\ubbf8</h4>';
  h+='<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:12px 0;">';

  const metaDescs = [
    ['material','\uc18c\uc7ac \uc885\ub958','\uac00\uacf5 \ub300\uc0c1 \uc18c\uc7ac. \uc774 \ub370\uc774\ud130\uc14b\uc740 wax(\uc655\uc2a4) \ub2e8\uc77c \uc18c\uc7ac\uc785\ub2c8\ub2e4. \uc2e4\uc81c \ud604\uc7a5\uc5d0\uc11c\ub294 \ucca0\uac15, \uc54c\ub8e8\ubbf8\ub284 \ub4f1 \ub2e4\uc591\ud569\ub2c8\ub2e4.'],
    ['feedrate','\uc774\uc1a1\uc18d\ub3c4 (mm/min)','\uacf5\uad6c\uac00 \uc6cc\ud06c\ud53c\uc2a4\ub97c \uae4e\uc544\ub098\uac00\ub294 \uc18d\ub3c4. \ub192\uc744\uc218\ub85d \ube60\ub974\uc9c0\ub9cc \uacf5\uad6c \ub9c8\ubaa8\uac00 \ube68\ub77c\uc9d1\ub2c8\ub2e4. \uc774 \ub370\uc774\ud130\uc5d0\uc11c 3~20 \ubc94\uc704.'],
    ['clamp_pressure','\ud074\ub7a8\ud504 \uc555\ub825 (bar)','\uc6cc\ud06c\ud53c\uc2a4\ub97c \uace0\uc815\ud558\ub294 \uc9c0\uadf8\uc758 \uc555\ub825. \ub0ae\uc73c\uba74 \uc9c4\ub3d9/\ub5a8\ub9bc, \ub108\ubb34 \ub192\uc73c\uba74 \ubcc0\ud615. \uc774 \ub370\uc774\ud130\uc5d0\uc11c 2.5~4.0 \ubc94\uc704.'],
    ['tool_condition','\uacf5\uad6c \uc0c1\ud0dc (Target)','worn(\ub9c8\ubaa8) \ub610\ub294 unworn(\uc815\uc0c1). \uac00\uacf5 \ud6c4 \uac80\uc0ac\uad00\uc774 \ud310\uc815\ud55c \uacb0\uacfc\uc774\uba70, \uc774\uac83\uc774 \uc6b0\ub9ac\uac00 \uc608\uce21\ud560 \ub300\uc0c1\uc785\ub2c8\ub2e4.'],
    ['Machining_Process','\uac00\uacf5 \uacf5\uc815 \ub2e8\uacc4','Prep \u2192 Layer 1~3 (Up/Down) \u2192 End. \ucd1d 10\ub2e8\uacc4. \uac01 \ub2e8\uacc4\ub9c8\ub2e4 \uc808\uc0ad \uc870\uac74\uacfc \uc13c\uc11c \ud328\ud134\uc774 \ub2ec\ub77c\uc9d1\ub2c8\ub2e4.'],
  ];
  metaDescs.forEach(([key,title,desc])=>{
    h+='<div class="eda-info" style="padding:14px;">';
    h+='<strong style="color:#e8770e;">'+title+'</strong><br>';
    h+='<code>'+key+'</code><br>';
    h+='<span style="font-size:12px;">'+desc+'</span>';
    h+='</div>';
  });
  h+='</div>';

  // \uc2e4\ud5d8 \uba54\ud0c0 \ud14c\uc774\ube14
  h+='<div style="overflow-x:auto;margin:16px 0;"><table class="eda-tbl"><thead><tr>';
  h+='<th>\uc2e4\ud5d8</th><th>\uc124\ube44</th><th>\uc18c\uc7ac</th><th>\uc774\uc1a1\uc18d\ub3c4</th><th>\ud074\ub7a8\ud504 \uc555\ub825</th><th>\uacf5\uad6c \uc0c1\ud0dc</th><th>\ud589 \uc218</th><th>\uac00\uacf5 \uc644\ub8cc</th>';
  h+='</tr></thead><tbody>';
  EDA_DATA.experiments.forEach(e=>{
    const cls=e.tool_condition==='worn'?'worn':'unworn';
    const fin=e.finalized==='yes'?'<span style="color:#22c55e">\uc644\ub8cc</span>':'<span style="color:#f59e0b">\uc911\ub2e8</span>';
    h+='<tr><td>'+e.id.replace('experiment_','#')+'</td><td>'+e.equipment+'</td><td>'+e.material+'</td>';
    h+='<td>'+e.feedrate+'</td><td>'+e.clamp_pressure+'</td>';
    h+='<td class="'+cls+'">'+e.tool_condition+'</td><td>'+e.rows+'</td><td>'+fin+'</td></tr>';
  });
  h+='</tbody></table></div>';

  // \u2500 \uc139\uc158 6: \uc13c\uc11c \ucd95 \uadf8\ub8f9 \uad6c\uc870 \u2500
  h+='<h4>\uc13c\uc11c \ub370\uc774\ud130 \uad6c\uc870 \u2014 42\uac1c \uc13c\uc11c\uac00 \ubb58\uc9c0</h4>';
  h+='<div class="eda-info">';
  h+='CNC \ubc00\ub9c1 \uba38\uc2e0\uc758 <strong>4\uac1c \ucd95(X, Y, Z, S)</strong>\uc5d0\uc11c \uac01\uac01 <strong>6~11\uac1c \uc13c\uc11c</strong>\uac00 \ub370\uc774\ud130\ub97c \uc218\uc9d1\ud569\ub2c8\ub2e4. ';
  h+='\uac01 \ucd95\uc774 \uae30\uacc4\uc758 \uc5b4\ub290 \ubd80\ubd84\uc774\uace0, \uc5b4\ub5a4 \uc13c\uc11c\uac00 \ubd99\uc5b4 \uc788\ub294\uc9c0 \uc774\ud574\ud558\uba74, ';
  h+='<strong>\uc5b4\ub5a4 \uc13c\uc11c\uac00 \ub9c8\ubaa8 \uac10\uc9c0\uc5d0 \uc720\uc6a9\ud560\uc9c0</strong> \ud310\ub2e8\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.';
  h+='</div>';

  for(const[group,cols] of Object.entries(EDA_DATA.sensor_groups)){
    const ad=AXIS_DESC[group]||[group,''];
    h+='<div class="eda-info" style="margin:8px 0;border-left:3px solid #e8770e;">';
    h+='<strong style="color:#e8770e;font-size:14px;">'+group+' \u2014 '+ad[0]+'</strong>';
    h+=' <span style="font-size:12px;color:#888;">('+cols.length+'\uac1c \uc13c\uc11c)</span><br>';
    h+='<span style="font-size:12px;">'+ad[1]+'</span><br><br>';
    h+='<table class="eda-tbl" style="font-size:12px;margin:4px 0 0;">';
    h+='<thead><tr><th>\uc13c\uc11c \ucee8\ub7fc</th><th>\uc758\ubbf8</th><th>\uc124\uba85</th></tr></thead><tbody>';
    cols.forEach(c=>{
      const info=getSensorInfo(c);
      h+='<tr><td><code>'+c+'</code></td><td><strong>'+info[0]+'</strong></td><td style="color:#999;">'+info[1]+'</td></tr>';
    });
    h+='</tbody></table>';
    h+='</div>';
  }

  // \u2500 \uc139\uc158 7: \uc13c\uc11c \uac04 \ud575\uc2ec \uad00\uacc4 \u2500
  h+='<h4>\uc13c\uc11c \uac04 \ud575\uc2ec \uad00\uacc4 \u2014 \uc5b4\ub5a4 \uc13c\uc11c\ub07c\ub9ac \uc5f0\uacb0\ub418\ub098?</h4>';
  h+='<div class="eda-info">';
  h+='<strong style="color:#e8770e;">\u2460 Command vs Actual (\uba85\ub839 vs \uc2e4\uc81c)</strong><br>';
  h+='Position, Velocity, Acceleration \uac01\uac01\uc5d0 Command(\ubaa9\ud45c)\uc640 Actual(\uc2e4\uc81c)\uac00 \uc30d\uc73c\ub85c \uc874\uc7ac\ud569\ub2c8\ub2e4.<br>';
  h+='\ub450 \uac12\uc758 \ucc28\uc774 = <strong>\ucd94\uc885 \uc624\ucc28(Following Error)</strong> \u2192 \uae30\uacc4 \uc0c1\ud0dc/\ub9c8\ubaa8 \ud310\ub2e8\uc758 \ud575\uc2ec \uc9c0\ud45c.<br>';
  h+='\uc815\uc0c1\uc774\uba74 \uac70\uc758 \ub3d9\uc77c, \ub9c8\ubaa8/\uc774\uc0c1 \uc2dc \ucc28\uc774\uac00 \uc99d\uac00\ud569\ub2c8\ub2e4.<br><br>';
  h+='<strong style="color:#3b82f6;">\u2461 \uc804\ub958/\uc804\uc555/\uc804\ub825 (\ubd80\ud558 3\ud615\uc81c)</strong><br>';
  h+='CurrentFeedback \u2248 OutputCurrent (\ubaa8\ud130\uc5d0 \ud750\ub974\ub294 \uc804\ub958)<br>';
  h+='OutputPower = OutputVoltage \u00d7 OutputCurrent (\uc804\ub825 = \uc804\uc555 \u00d7 \uc804\ub958)<br>';
  h+='\uc808\uc0ad \ubd80\ud558\uac00 \ud074\uc218\ub85d \uc804\ub958/\uc804\ub825 \uc99d\uac00 \u2192 <strong>\ub9c8\ubaa8\ub41c \uacf5\uad6c\ub294 \ub354 \ub9ce\uc740 \uc804\ub825 \uc18c\ube44</strong><br><br>';
  h+='<strong style="color:#22c55e;">\u2462 \ucd95 \uac04 \uad00\uacc4</strong><br>';
  h+='X-Y\ucd95\uc740 \ud3c9\uba74 \uc774\ub3d9\uc744 \ud568\uaed8 \uc218\ud589 \u2192 \ub3d9\uc2dc\uc5d0 \uac12\uc774 \ubcc0\ud558\ub294 \uad6c\uac04\uc774 \ub9ce\uc74c<br>';
  h+='Z\ucd95\uc740 \uc808\uc0ad \uae4a\uc774 \u2192 \ub2e4\ub978 \ucd95\uacfc \ub3c5\ub9bd\uc801\uc73c\ub85c \uc6c0\uc9c1\uc774\ub294 \uacbd\uc6b0\uac00 \ub9ce\uc74c<br>';
  h+='S\ucd95(\uc8fc\ucd95)\uc740 \ud56d\uc0c1 \ud68c\uc804 \u2192 \uc808\uc0ad \uc911 \uc804\ub958/\uc804\ub825\uc774 \ud575\uc2ec';
  h+='</div>';

  // \u2500 \uc139\uc158 8: \uc81c\uac70 \ub300\uc0c1 \ucee8\ub7fc \u2500
  h+='<h4>\uc81c\uac70 \ub300\uc0c1 \ucee8\ub7fc ('+EDA_DATA.removed_cols.length+'\uac1c) \u2014 \uc65c \ube7c\ub294\uac00?</h4>';
  h+='<div class="eda-info">';
  h+='\uc6d0\ubcf8 48\uac1c \ucee8\ub7fc \uc911 \uc544\ub798 '+EDA_DATA.removed_cols.length+'\uac1c\ub294 \ubd84\uc11d\uc5d0 \uc4f8\ubaa8\uac00 \uc5c6\uc5b4 \uc81c\uac70\ud569\ub2c8\ub2e4:<br><br>';
  EDA_DATA.removed_cols.forEach(c=>{
    const info=getSensorInfo(c.col);
    h+='<code>'+c.col+'</code> <strong>'+info[0]+'</strong> \u2192 '+c.reason+'<br>';
  });
  h+='<br>48 - '+EDA_DATA.removed_cols.length+' = <strong>'+k.valid_sensors+'\uac1c</strong>\uac00 \uc2e4\uc81c \ubd84\uc11d\uc5d0 \uc4f8 \uc218 \uc788\ub294 \uc720\ud6a8 \uc13c\uc11c\uc785\ub2c8\ub2e4.';
  h+='</div>';

  el.innerHTML=h;

  // \ucc28\ud2b8 \ub80c\ub354\ub9c1
  Plotly.newPlot('eda-pie-chart',[{
    values:[d.worn,d.unworn],labels:['Worn (\ub9c8\ubaa8)','Unworn (\uc815\uc0c1)'],
    type:'pie',marker:{colors:['#ef4444','#22c55e']},
    textinfo:'label+value',textfont:{color:'#fff',size:14},
    hole:0.4
  }],{...PLOTLY_LAYOUT,height:220,margin:{t:10,b:10,l:10,r:10},showlegend:false},PLOTLY_CONFIG);

  const exps=EDA_DATA.experiments;
  Plotly.newPlot('eda-bar-chart',[{
    x:exps.map(e=>e.id.replace('experiment_','#')),
    y:exps.map(e=>e.rows),
    type:'bar',
    marker:{color:exps.map(e=>e.tool_condition==='worn'?'#ef4444':'#22c55e')},
    hovertemplate:'%{x}<br>\ud589 \uc218: %{y}<extra></extra>'
  }],{...PLOTLY_LAYOUT,height:280,
    xaxis:{...PLOTLY_LAYOUT.xaxis,title:'\uc2e4\ud5d8 \ubc88\ud638'},
    yaxis:{...PLOTLY_LAYOUT.yaxis,title:'\ud589 \uc218 (= 100ms \u00d7 \ud589 \uc218 = \uac00\uacf5 \uc2dc\uac04)'}
  },PLOTLY_CONFIG);
}
"""

content = content[:old_start] + new_func + content[old_end:]

with open('data-review.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done. File size: {len(content):,} bytes")
