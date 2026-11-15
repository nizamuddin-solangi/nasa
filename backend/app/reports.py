from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
def pdf(title,result):
 b=BytesIO(); c=canvas.Canvas(b,pagesize=letter); w,h=letter; y=h-54
 def line(text, size=10):
  nonlocal y
  if y<50: c.showPage(); y=h-54
  c.setFont('Helvetica',size); c.drawString(48,y,text[:125]); y-=16
 c.setFillColorRGB(.02,.12,.2); c.rect(0,h-90,w,90,fill=1,stroke=0); c.setFillColorRGB(.8,.95,1); c.setFont('Helvetica-Bold',20); c.drawString(48,h-54,'EARTHSCOPE');
 y=h-118; line(title,15); m=result['metadata']; s=result['statistics']
 for text in [f"Location: {m['latitude']:.4f}, {m['longitude']:.4f}",f"NASA source: {m.get('source', 'NASA POWER Monthly Point API')}",f"Variable: {m['label']} ({m['variable']}); units: {m['unit']}",f"Period: {s['period']}; valid monthly observations: {s['valid_observations']}",f"Classification: {s['direction']}",f"Sen's slope: {s['slope_per_decade']} {m['unit']} per decade",f"95% CI: {s['ci95_per_decade'][0]} to {s['ci95_per_decade'][1]}",f"Mann-Kendall p-value: {s['p_value']}"] : line(text)
 obs=result['observations']; vals=[x['value'] for x in obs]
 if vals:
  y-=8; left,right,bottom,top=48,w-48,y-110,y
  lo,hi=min(vals),max(vals); span=hi-lo or 1
  c.setStrokeColorRGB(.25,.45,.55); c.rect(left,bottom,right-left,top-bottom,fill=0)
  c.setStrokeColorRGB(.1,.65,.8); path=c.beginPath()
  for i,value in enumerate(vals):
   px=left+(right-left)*i/max(1,len(vals)-1); py=bottom+(top-bottom)*(value-lo)/span
   path.moveTo(px,py) if i==0 else path.lineTo(px,py)
  c.drawPath(path); c.setFillColorRGB(.1,.1,.1); c.setFont('Helvetica',8); c.drawString(left, bottom-12, 'Historical NASA POWER monthly observations'); y=bottom-30
 for text in ['', 'Interpretation:',result['interpretation'],'', 'Method and limitations:',s['method'],'NASA POWER values are model-derived / gridded estimates, not direct ground-station observations. Results do not establish causation.'] : line(text)
 c.save(); return b.getvalue()
