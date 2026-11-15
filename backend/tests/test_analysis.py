from app.analysis import analyze, compare
from app.reports import pdf
def records(delta=0): return [{'date':f'{y}-{m:02d}-01','value':20+m*.2+(y-2000)*.08+delta} for y in range(2000,2006) for m in range(1,13)]
meta={'label':'Temperature at 2 meters','unit':'°C','variable':'T2M','latitude':0,'longitude':0}
def test_analyze_seasonal_data():
 r=analyze(records(),meta); assert r['statistics']['valid_observations']==72; assert r['statistics']['slope_per_decade']>0
def test_compare():
 a=analyze(records(),meta); b=analyze(records(2),meta); assert 'comparison' in compare(a,b)
def test_report_contains_investigation_output():
 result=analyze(records(), {**meta, 'source':'NASA POWER Monthly Point API'})
 assert pdf('Test report', result).startswith(b'%PDF')
