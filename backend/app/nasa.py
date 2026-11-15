import asyncio, time, logging
from typing import Any
import httpx

log = logging.getLogger(__name__)
POWER_URL = 'https://power.larc.nasa.gov/api/temporal/monthly/point'
VARIABLES = {
 'T2M': {'label':'Temperature at 2 meters', 'unit':'°C', 'community':'SB', 'source':'NASA GMAO MERRA-2 assimilation model'},
 'PRECTOTCORR': {'label':'Corrected precipitation', 'unit':'mm/day', 'community':'SB', 'source':'NASA GMAO MERRA-2 assimilation model'},
 'WS10M': {'label':'Wind speed at 10 meters', 'unit':'m/s', 'community':'SB', 'source':'NASA GMAO MERRA-2 assimilation model'},
 'ALLSKY_SFC_SW_DWN': {'label':'All-sky surface shortwave downward radiation', 'unit':'kWh/m²/day', 'community':'SB', 'source':'NASA CERES / GEWEX SRB radiation archives'},
}
_cache: dict[tuple, tuple[float, dict]] = {}
_lock = asyncio.Lock()

class NasaError(Exception): pass

async def fetch(q) -> dict[str, Any]:
    key=(q.latitude,q.longitude,q.variable,q.start_year,q.end_year)
    async with _lock:
        cached=_cache.get(key)
        if cached and time.time()-cached[0] < 3600: return cached[1]
    params={'parameters':q.variable,'community':VARIABLES[q.variable]['community'],'longitude':q.longitude,'latitude':q.latitude,'start':q.start_year,'end':q.end_year,'format':'JSON'}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response=await client.get(POWER_URL,params=params)
            response.raise_for_status()
            raw=response.json()
    except (httpx.HTTPError, ValueError) as e:
        log.warning('NASA POWER retrieval failed: %s', e)
        raise NasaError('NASA POWER data is currently unavailable. No observations were substituted.') from e
    try:
        values=raw['properties']['parameter'][q.variable]
        records=[]
        for stamp, value in values.items():
            if len(stamp)==6 and stamp[4:]!='13' and value not in (-999, -999.0, None):
                records.append({'date':f'{stamp[:4]}-{stamp[4:]}-01','value':float(value)})
        if len(records)<48: raise ValueError('insufficient valid monthly records')
    except (KeyError, TypeError, ValueError) as e:
        raise NasaError('NASA POWER returned an unexpected or insufficient data response.') from e
    meta=VARIABLES[q.variable]
    result={'records':records,'metadata':{'source':'NASA POWER Monthly Point API','variable':q.variable,**meta,'latitude':q.latitude,'longitude':q.longitude,'requested_period':f'{q.start_year}–{q.end_year}','retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'api_url':str(response.url)}}
    async with _lock: _cache[key]=(time.time(),result)
    return result
