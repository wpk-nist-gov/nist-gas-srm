# ruff:file-ignore[manual-from-import]  # Needed to avoid pyright import cycle error
import nist_gas_srm.core.basemodels.rcert as rcert
import nist_gas_srm.core.basemodels.srm as srm
import nist_gas_srm.core.basemodels.standard_analysis as stdanal


class CompletePublic(srm.CompletePublic):
    rcert: rcert.CompletePublic
    standard_analysis: stdanal.CompletePublic


class CompleteCreate(srm.CompleteCreate):
    rcert: rcert.CompleteCreate
    standard_analysis: stdanal.CompleteCreate
