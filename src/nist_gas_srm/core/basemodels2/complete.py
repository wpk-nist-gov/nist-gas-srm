import nist_gas_srm.core.basemodels2.standard_analysis as stdanal
from nist_gas_srm.core.basemodels2 import rcert, srm


class Create(srm.CompletePublic):
    rcert: rcert.CompletePublic
    standard_analysis: stdanal.CompletePublic


class Public(srm.CompleteCreate):
    rcert: rcert.CompleteCreate
    standard_analysis: stdanal.CompleteCreate
