import math
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, norm, theilslopes, linregress

def analyze(records, metadata):
    frame=pd.DataFrame(records)
    frame['date']=pd.to_datetime(frame['date']); frame['value']=pd.to_numeric(frame['value'])
    frame=frame.dropna().sort_values('date'); frame['month']=frame.date.dt.month
    climatology=frame.groupby('month')['value'].transform('mean')
    frame['anomaly']=frame.value-climatology
    y=frame.anomaly.to_numpy(); x=np.arange(len(frame))
    if len(y)<48: raise ValueError('At least 48 valid monthly observations are required')
    tau, p_raw=kendalltau(x,y)
    slope, intercept, low, high=theilslopes(y,x,0.95)
    r1=float(pd.Series(y).autocorr(lag=1)); r1=0 if not np.isfinite(r1) else max(-.99,min(.99,r1))
    n=len(y); n_eff=max(3,n*(1-r1)/(1+r1))
    # Conservative effective-sample-size adjustment for serially correlated residuals.
    z=norm.ppf(1-p_raw/2) if p_raw > 0 else 8.0
    p=float(2*(1-norm.cdf(abs(z)*math.sqrt(n_eff/n))))
    decade=10*12
    significant=p < .05
    direction='Increasing' if significant and slope>0 else 'Decreasing' if significant else 'No statistically significant trend'
    trend_line=intercept+slope*x
    result={'observations':frame[['date','value','anomaly']].assign(date=lambda d:d.date.dt.strftime('%Y-%m-%d')).to_dict('records'),'trend_line':[{'date':d.strftime('%Y-%m-%d'),'value':round(float(v),5)} for d,v in zip(frame.date,trend_line)],'statistics':{'method':'Seasonal-cycle removal + Mann–Kendall (autocorrelation-adjusted effective sample size) + Sen’s slope','slope_per_month':round(float(slope),7),'slope_per_decade':round(float(slope*decade),4),'ci95_per_decade':[round(float(low*decade),4),round(float(high*decade),4)],'p_value':round(p,5),'raw_p_value':round(float(p_raw),5),'tau':round(float(tau),4),'lag1_autocorrelation':round(r1,3),'effective_n':round(n_eff,1),'valid_observations':n,'direction':direction,'significant':significant,'period':f"{frame.date.min():%Y-%m} to {frame.date.max():%Y-%m}"},'metadata':metadata}
    unit=metadata['unit']; stat=result['statistics']
    sig='statistically significant' if significant else 'not statistically significant'
    result['interpretation']=(f"Investigation indicates a {direction.lower()} {metadata['label'].lower()} trend. "
        f"The Sen’s slope is {stat['slope_per_decade']:+.4f} {unit} per decade after seasonal-cycle removal. "
        f"The autocorrelation-adjusted Mann–Kendall p-value is {stat['p_value']:.5f}; this trend is {sig} at α = 0.05. "
        'This analysis describes an observed modeled-data association and does not establish a cause.')
    return result

def compare(a,b):
    sa,sb=a['statistics'],b['statistics']; delta=sa['slope_per_decade']-sb['slope_per_decade']
    avg_a=float(np.mean([i['value'] for i in a['observations']])); avg_b=float(np.mean([i['value'] for i in b['observations']]))
    stronger='First location' if abs(sa['slope_per_decade'])>abs(sb['slope_per_decade']) else 'Second location' if abs(sb['slope_per_decade'])>abs(sa['slope_per_decade']) else 'Neither location'
    left=pd.DataFrame(a['observations'])[['date','anomaly']].rename(columns={'anomaly':'first'})
    right=pd.DataFrame(b['observations'])[['date','anomaly']].rename(columns={'anomaly':'second'})
    paired=left.merge(right,on='date').dropna()
    if len(paired) >= 48:
        n=len(paired); fit=linregress(np.arange(n),paired['second'].to_numpy()-paired['first'].to_numpy())
        # Comparison significance is deliberately labeled as a descriptive linear test;
        # the individual trend tests above retain the autocorrelation adjustment.
        test={'method':'Linear regression test on paired deseasonalized anomaly differences','matched_observations':n,'difference_slope_per_decade':round(float(fit.slope*120),4),'ci95_per_decade':[round(float((fit.slope-1.96*fit.stderr)*120),4),round(float((fit.slope+1.96*fit.stderr)*120),4)],'p_value':round(float(fit.pvalue),5),'significant':bool(fit.pvalue < .05)}
    else:
        test={'method':'Not computed','matched_observations':len(paired),'reason':'Fewer than 48 matching valid monthly observations.'}
    return {'first':a,'second':b,'comparison':{'slope_difference_per_decade':round(delta,4),'average_difference':round(avg_a-avg_b,4),'stronger_observed_trend':stronger,'comparative_significance':test,'note':'The primary slope difference is between Sen’s slope estimates. The companion interaction test assesses whether linear anomaly trends differ; neither result implies causation between locations.'}}
