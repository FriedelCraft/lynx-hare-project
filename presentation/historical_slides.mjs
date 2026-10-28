// Editable historical presentation. Values come from frozen evaluation CSVs.
import path from 'node:path';
import fs from 'node:fs';
const ink='#15383A', teal='#197278', orange='#C4532E';
function text(s,name,value,x,y,w,h,size=28,color=ink,bold=false){
  const t=s.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  t.text=value;t.text.style={typeface:'Arial',fontSize:size,color,bold};t.text.insets=0;return t;
}
function slide(p,title,owner,number){
  const s=p.slides.add({width:1280,height:720});s.background.fill='#FFFFFF';
  text(s,'title',title,64,42,1152,75,43,ink,true);
  text(s,'footer',`${owner}, MAC F314     ${number}`,64,667,1152,28,18,'#4D6263');return s;
}
function image(s,root,file,x=64,y=145,w=1152,h=485){
  s.images.add({blob:new Uint8Array(fs.readFileSync(path.join(root,file))),contentType:'image/png',alt:file,fit:'contain',position:{left:x,top:y,width:w,height:h}});
}
function note(s,content,source){s.speakerNotes.text=content+'\nSource: '+source;}
function rmseChart(s,metrics){
  const rounded=v=>Math.round(v*1e6)/1e6;
  const c=s.charts.add('bar',{position:{left:510,top:155,width:700,height:410},
    title:'Held-out RMSE, thousands of pelts',titleTextStyle:{fontSize:24},categories:['Hare','Lynx'],
    series:[{name:'PINN-derived ODE',values:[metrics.pinn.hare_rmse,metrics.pinn.lynx_rmse].map(rounded),fill:teal},
            {name:'Least squares',values:[metrics.least_squares.hare_rmse,metrics.least_squares.lynx_rmse].map(rounded),fill:orange}],
    barOptions:{direction:'column',grouping:'clustered'},hasLegend:true,
    legend:{position:'bottom',textStyle:{fontSize:21}},xAxis:{textStyle:{fontSize:23}},
    yAxis:{min:0,textStyle:{fontSize:20},numberFormatCode:'0.0'},
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:21}},chartFill:'#FFFFFF'});
  for(const style of [c.legend.textStyle,c.dataLabels.textStyle,c.xAxis.textStyle,c.yAxis.textStyle,c.titleTextStyle])style.typeface='Arial';
}
export function addYash(p,root,metrics,start=1){
  const a=slide(p,'Inverse PINN on historical pelt data','Yash',start);
  text(a,'equations','dH/dt = rH(1 − H/K) − aHP/(b + H)\ndP/dt = eaHP/(b + H) − mP',64,145,1152,112,35);
  text(a,'loss','Loss = data error + 10 × ODE error + 10 × initial error',64,290,1152,64,31,teal,true);
  text(a,'network','Scaled time input, 3 × 48 tanh units, positive hare and lynx outputs',64,390,1152,66,27);
  text(a,'fit','All six positive coefficients fitted to 1900–1915, across three seeds',64,470,1152,60,27);
  text(a,'forecast','Freeze parameters, then integrate the ODE from 1900 through 1920',64,550,1152,65,27);
  note(a,'About 55 seconds. The model predicts two pelt indices. Autograd supplies the time derivatives for the physics residual. Data scales use training maxima only. Adam is followed by L-BFGS. We estimate all six positive coefficients, unlike the earlier controlled synthetic test that fixed three coefficients. We select the seed using training loss and forecast by ODE integration, without restarting from a test state. The IC penalty is soft and its discrepancy is reported.',
       'src/lynx_hare/historical_pinn.py; configs/historical.json; Raissi et al. (2019), https://doi.org/10.1016/j.jcp.2018.10.045');
  const b=slide(p,'Forecast comparison and parameter sensitivity','Yash',start+1);
  text(b,'runs','13 runs',64,170,410,92,66,teal,true);
  text(b,'evidence','Three seeds plus error-model,\ninitial-state, bound and\nphysics-weight checks',64,285,420,145,28);
  text(b,'limit','K and b move towards\nexpanded upper bounds',64,470,420,90,28,orange,true);
  rmseChart(b,metrics);
  text(b,'finding','Hare RMSE is similar. Least squares predicts lynx more accurately.',64,590,1152,56,28,ink,true);
  note(b,'About 65 seconds. Across all retained checks, the primary PINN has hare RMSE about 2.85 and lynx RMSE about 4.32. Least squares gives about 3.07 and 3.04. Hare MAE is essentially tied, so we do not claim a clear hare advantage. Several parameters follow the chosen bounds, and the re-integrated ODE has a training cost 1.86 times the least-squares minimum in the main variant. A soft-physics network optimum is not the same objective as least squares on the ODE trajectory. We retained worse sensitivity outcomes and made no post-test retuning. Synthetic recovery separately checks implementation, not historical biological accuracy.',
       'results/historical/advay_evaluation_v1/comparison.json; results/historical/advay_evaluation_v1/pinn_training_fit.json; results/historical/yash_pinn_wider_v1/');
}
export function buildGroup(p,root,metrics){
  let s=slide(p,'Lynx and hare pelt dynamics','Arnav',1);
  image(s,root,'results/historical/data_checks/figures/advay_raw_series.png',64,140,1152,430);
  text(s,'question','Can one mechanistic model explain oscillations and forecast unseen years?',64,585,1152,58,29,teal,true);
  note(s,'About 55 seconds. Introduce the approximately decadal hare and lynx oscillation. Counts are thousands of pelts traded, not animal censuses. We use the Stan compilation and record disagreement with another compilation. The task combines model formulation, stability, numerical checks and two inverse-fitting methods.', 'data/historical/provenance.json; contributions/arnav/presentation_notes.md');
  s=slide(p,'Model, observation units and scaling','Arnav',2);
  text(s,'model','H′ = rH(1 − H/K) − aHP/(b + H)\nP′ = eaHP/(b + H) − mP',64,160,1152,130,39);
  text(s,'reason','Logistic hare growth and saturating predation',64,330,1152,55,32,teal,true);
  text(s,'units','H and P are pelt indices. Unknown trapping scales enter effective coefficients.',64,420,1152,85,29);
  text(s,'scales','Theory coordinates: s = rt, x = H/K, y = aP/(rK)',64,545,1152,60,31);
  note(s,'About 65 seconds. Explain how resource limitation and Holling-II saturation improve the neutral-cycle Lotka-Volterra reference. Unknown constant observation factors are absorbed into effective pelt-unit coefficients. Annual totals approximate point samples. Explain the dimensionless scaling and how it differs from the fixed training-max normalization in the PINN. Neither convention establishes accurate biological coefficient recovery.', 'contributions/arnav/equations_and_units.md; contributions/arnav/sections/arnav_model.tex');
  s=slide(p,'Equilibria and phase-plane geometry','Joel',3);
  image(s,root,'results/integration/figures/group_nullclines.png',64,135,780,485);
  text(s,'coexist','H* = mb/(ea − m)\nK > H*, ea > m',875,210,340,130,31,teal,true);
  text(s,'geometry','Predator nullcline\nis vertical.\nPrey nullcline has a hump.',875,400,340,165,27);
  note(s,'About 55 seconds. Describe the origin, prey-only and feasible coexistence equilibria. Use the Jacobian and nullcline slope to classify coexistence stability. A stable equilibrium can be a node or a focus. The feasibility conditions characterize a coexistence equilibrium; they are not automatically restrictions imposed on the statistical fitting domain.', 'report/joel_stability_section.tex; src/lynx_hare/stability.py');
  s=slide(p,'Hopf threshold and enrichment','Joel',4);
  text(s,'threshold','K_H = b + 2H*\nσ = K/K_H',64,165,420,135,43,teal,true);
  text(s,'condition','Trace crosses zero\nDeterminant stays positive',64,350,420,110,29);
  text(s,'claim','A theorem for the model\nA conditional ecological interpretation',64,510,420,100,27);
  image(s,root,'results/stability/figures/joel_trace_det.png',515,150,700,450);
  note(s,'About 65 seconds. Explain transversality and the Hopf threshold. Increasing carrying capacity can destabilize the equilibrium and enlarge oscillations: paradox of enrichment. Separate the analytic threshold, cited results about periodic orbits and numerical Lyapunov evidence. Fitted sigma above one describes that fitted ODE, while uncertainty across methods and assumptions limits a claim about the real ecosystem.', 'report/joel_stability_section.tex; results/stability/validation_targets.json');
  s=slide(p,'Numerical checks across the threshold','Rishi',5);
  image(s,root,'results/simulations/figures/rishi_bifurcation.png',64,140,1152,430);
  text(s,'solver','Shared RHS, RK45, declared tolerances and a documented burn-in',64,585,1152,55,29,teal,true);
  note(s,'About 60 seconds. RK45 preserves the Lotka-Volterra invariant while Euler drifts. Show damped versus sustained motion below and above the illustrative K_H=90. The post-transient amplitude grows near onset with log-log slope about 0.507. Explain why a long burn-in matters. Historical fitting uses model.solve tolerances, while long-run simulations use tighter settings.', 'configs/simulations.json; docs/rishi_simulation_handoff.md');
  s=slide(p,'Historical fits relative to Hopf','Rishi',6);
  image(s,root,'results/simulations/historical/figures/rishi_historical_sigma.png',64,140,1152,430);
  text(s,'conclusion','Fits reproduce a short cycle while disagreeing about long-run stability',64,585,1152,55,29,teal,true);
  note(s,'About 60 seconds. The displayed analysis covers the 13 PINN runs and 18 matching least-squares starts. Selected PINN sigma lies around 1.32 to 1.48, while the least-squares observation/IC variants span roughly 0.55 to 1.07. Very slow growth or decay makes 16 training years insufficient to distinguish long-run regimes. Bounds and the observation model materially affect the result.', 'results/simulations/historical/summary.json; presentation/rishi_notes.md');
  addYash(p,root,metrics,7);
  s=slide(p,'Independent baseline and held-out validation','Advay',9);
  image(s,root,'results/historical/advay_evaluation_v1/figures/advay_heldout_overlay.png',64,140,820,485);
  text(s,'protocol','Train 1900–1915\nScore 1916–1920\nSame units and solver',905,200,310,150,29,teal,true);
  text(s,'starts','240 starts across\nthree declared variants',905,435,310,110,28);
  note(s,'About 60 seconds. State how the independent baseline uses the shared config and verifies the matching benchmark. Forecasts and selection precede scoring; Yash had already published scores, so this is independent reproduction rather than a new blinded test. Score hare and lynx separately on five years. Under the declared comparison rule, hare is similar and least squares is better for lynx. Retain all sensitivities.', 'docs/advay_baseline_protocol.md; docs/advay_scoring_plan.md; results/historical/advay_evaluation_v1/');
  s=slide(p,'Conclusions and limits of inference','Advay',10);
  text(s,'result','The model forecasts one crash and recovery with useful short-term accuracy',64,155,1152,100,35,teal,true);
  text(s,'limits','Five held-out years provide a small test\nPelt returns depend on catchability and source compilation\nSeveral coefficients track numerical bounds\nObservation assumptions change the inferred stability regime',64,315,1152,210,30);
  text(s,'ending','A good trajectory fit gives conditional evidence about this model',64,575,1152,65,31,ink,true);
  note(s,'About 60 seconds. Both methods outperform persistence and training-mean reference forecasts, but the small window limits generalization. The PINN does not outperform least squares overall. State the uncertain observation factors, missing vegetation/weather/spatial effects, boundary sensitivity and weak identification. Finish with the distinction between a fitted mechanism and proven ecological causality. The full notebook, report, datasets, EPS graphs and per-person AI logs accompany the submission.', 'report/advay_data_validation_section.tex; results/historical/advay_evaluation_v1/comparison.json');
}
