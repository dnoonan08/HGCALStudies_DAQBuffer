#!/bin/bash
job=$1
if [ -z ${_CONDOR_SCRATCH_DIR} ] ; then 
    echo "Running Interactively" ; 
else
    echo "Running In Batch"
    cd ${_CONDOR_SCRATCH_DIR}
    echo ${_CONDOR_SCRATCH_DIR}
    echo "xrdcp root://cmseos.fnal.gov//store/user/dnoonan/HGCAL_Concentrator/pdDF_Subdet3_Layer6to8_MB2_FineWafers.pkl ."
	xrdcp root://cmseos.fnal.gov//store/user/dnoonan/HGCAL_Concentrator/pdDF_Subdet3_Layer6to8_MB2_FineWafers.pkl .

    source /cvmfs/cms.cern.ch/cmsset_default.sh
	cd /cvmfs/cms.cern.ch/slc6_amd64_gcc630/cms/cmssw/CMSSW_9_4_2/
	eval `scramv1 runtime -sh`
	cd -
fi

python simBuffer_withTriggerRules_2in8.py -N 40000000 -f pdDF_Subdet3_Layer6to8_MB2_FineWafers.pkl

rm simBuffer_withTriggerRules_2in8.py
rm pdDF_Subdet3_Layer6to8_MB2_FineWafers.pkl

mv Buffers_byHGROC.root Buffers_byHGROC_${job}.root