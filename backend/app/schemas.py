from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Query(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    variable: Literal['T2M', 'PRECTOTCORR', 'WS10M', 'ALLSKY_SFC_SW_DWN']
    start_year: int = Field(ge=1981, le=2025)
    end_year: int = Field(ge=1981, le=2025)
    @model_validator(mode='after')
    def years(self):
        if self.end_year < self.start_year: raise ValueError('end_year must be on or after start_year')
        if self.end_year - self.start_year < 4: raise ValueError('Select at least five complete years')
        return self

class CompareQuery(BaseModel):
    first: Query
    second: Query
    @model_validator(mode='after')
    def compatible(self):
        if self.first.variable != self.second.variable: raise ValueError('Locations must use the same variable')
        return self

class ReportRequest(BaseModel):
    result: dict
    title: str = Field(default='EARTHSCOPE Investigation Report', max_length=120)
