// Editable two-slide segment. Numeric chart evidence comes from the saved synthetic run.
export function buildSlides(presentation) {
  const addText = (slide, name, text, x, y, w, h, size=28, color='#15383A', bold=false) => {
    const s = slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    s.text=text;
    s.text.style={typeface:'Arial',fontSize:size,color,bold};
    s.text.insets=0;
    return s;
  };
  const s1=presentation.slides.add({width:1280,height:720});
  s1.background.fill='#FFFFFF';
  addText(s1,'title','Inverse PINN parameter inference',64,44,1152,70,46,'#15383A',true);
  addText(s1,'equations','dH/dt = rH(1 − H/K) − aHP/(b + H)\ndP/dt = eaHP/(b + H) − mP',64,145,1152,120,35);
  addText(s1,'loss','Loss = data error + 10 × ODE error + 10 × initial error',64,295,1152,60,31,'#197278',true);
  addText(s1,'architecture','Network: scaled time input, three hidden layers, positive state outputs',64,390,1152,54,27);
  addText(s1,'parameters','Estimate r, a and m. Fix K = 60, b = 20 and e = 0.6 for this controlled test.',64,464,1152,72,27);
  addText(s1,'training','Adam and L-BFGS training use three seeds and observations through 1915.',64,554,1152,58,27);
  addText(s1,'disclosure','Yash, MAC F314. All data in this segment are synthetic.',64,657,1152,30,19,'#4D6263');
  s1.speakerNotes.text='My part tests whether a physics-informed neural network can recover model parameters while fitting observations. I used synthetic data while our shared historical-data interfaces are pending. The network takes scaled time and predicts positive hare and lynx indices. Automatic differentiation computes time derivatives. The loss combines normalized data, ODE residual and initial-condition errors. I estimate r, a and m in positive bounds while fixing K, b and e. Adam training is followed by L-BFGS, with three optimizer seeds. Correct fixed constants and an exact initial state are favorable synthetic assumptions. Sources: Rosenzweig and MacArthur (1963), https://doi.org/10.1086/282272; Raissi et al. (2019), https://doi.org/10.1016/j.jcp.2018.10.045; src/lynx_hare/pinn.py; configs/synthetic.json.';
  const s2=presentation.slides.add({width:1280,height:720});
  s2.background.fill='#FFFFFF';
  addText(s2,'title','Synthetic recovery and ODE forecasts',64,44,1152,70,46,'#15383A',true);
  addText(s2,'recovery-value','0.36%',64,165,410,100,78,'#197278',true);
  addText(s2,'recovery-label','Maximum parameter error\nacross three annual-data seeds',64,285,420,90,28);
  addText(s2,'scope','16 training observations with 3% noise\nEstimate r, a and m\nOne fixed noise realization',64,405,420,140,25,'#4D6263');
  const chart=s2.charts.add('bar',{
    position:{left:515,top:145,width:700,height:410},
    title:'Held-out RMSE in synthetic index units', titleTextStyle:{fontSize:25},
    categories:['Hare','Lynx'],
    series:[{name:'PINN-derived ODE',values:[0.331892,0.386242],fill:'#197278'},
            {name:'Least squares',values:[0.296172,0.441202],fill:'#C4532E'}],
    barOptions:{direction:'column',grouping:'clustered'},hasLegend:true,
    legend:{position:'bottom',textStyle:{fontSize:22}},
    xAxis:{textStyle:{fontSize:24}},
    yAxis:{min:0,textStyle:{fontSize:20},numberFormatCode:'0.0'},
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.000',textStyle:{fontSize:21}},
    chartFill:'#FFFFFF'
  });
  for (const style of [chart.legend.textStyle,chart.dataLabels.textStyle,chart.xAxis.textStyle,chart.yAxis.textStyle,chart.titleTextStyle]) style.typeface='Arial';
  addText(s2,'finding','Least squares has lower hare RMSE. The PINN has lower lynx RMSE.',64,579,1152,58,29,'#15383A',true);
  addText(s2,'caveat','Five test years after 1915. Correct fixed constants and an exact initial state limit the claim.',64,656,1152,36,21,'#4D6263');
  s2.speakerNotes.text='Across three seeds, maximum parameter error was about 0.006 percent for clean quarterly data and 0.36 percent for noisy annual data. These optimizer replicates use one noise realization, so they are not confidence intervals. For forecasting I freeze learned parameters, then integrate the ODE from 1900 through 1920. I do not extrapolate the network or restart from test observations. The chart scores five noisy held-out observations per species. Least squares has lower hare RMSE and the selected PINN has lower lynx RMSE, so the comparison is mixed. I also check loss-weight and initial-guess sensitivity, independent residuals and local parameter sensitivities. This validates the implementation on a controlled example. Historical predictive accuracy remains untested. Source: results/synthetic/heldout_metrics.csv, parameter_recovery.csv, selected_run.json. The selected seed minimizes training loss. The same fixed parameters, bounds, scale, initial condition and RK45 solver apply to both methods.';
}
