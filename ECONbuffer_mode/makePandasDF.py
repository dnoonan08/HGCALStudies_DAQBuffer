import uproot
import pandas as pd
import numpy as np
import pyxrootd
import ROOT

from myMapping import waferMBmap



adcLSB_ = 100./1024.
tdcLSB_ = 10000./4096.
tdcOnsetfC_ = 60.

# maxBits = 0
# maxMB = None
# maxEvent = -1
# maxFile = -1


# h_total_bits = ROOT.TH1F("h_total_bits","h_total_bits",800,0,8000)
# h_total_bits_MBType = [ROOT.TH1F("h_total_bits_1","h_total_bits_1",800,0,8000),
#                        ROOT.TH1F("h_total_bits_2","h_total_bits_2",800,0,8000),
#                        ROOT.TH1F("h_total_bits_3","h_total_bits_3",800,0,8000),
#                        ROOT.TH1F("h_total_bits_4","h_total_bits_4",800,0,8000)]



for iFile in xrange(1,91):
    if iFile==20: continue

    print iFile, "loading"

    _tree = uproot.open("root://cmseos.fnal.gov//store/user/lpchgcal/ConcentratorNtuples/L1THGCal_Ntuples/RelValTTbar_14TeV/crab_RelValTTbar_14TeV/180411_205247/0000/ntuple_%i.root"%iFile,xrootdsource=dict(chunkbytes=1024**3, limitbytes=1024**3))["hgcalTriggerNtuplizer/HGCalTriggerNtuple"]
#    _tree = uproot.open("root://cmseos.fnal.gov//store/user/lpchgcal/ConcentratorNtuples/L1THGCal_Ntuples/RelValNuGun/crab_RelValNuGun/180413_042405/0000/ntuple_%i.root"%iFile,xrootdsource=dict(chunkbytes=1024**3, limitbytes=1024**3))["hgcalTriggerNtuplizer/HGCalTriggerNtuple"]

    print "reading"

    for iEvent in range(_tree.numentries):

        values = _tree.arrays(["genjet_pt","genjet_eta","genjet_phi","hgcdigi_subdet","hgcdigi_layer","hgcdigi_cell","hgcdigi_zside","hgcdigi_data","hgcdigi_isadc","hgcdigi_wafer","hgcdigi_wafertype","hgcdigi_eta","hgcdigi_phi"],entrystart=iEvent, entrystop=iEvent+1)


        gen_df = pd.DataFrame({'pt':values['genjet_pt'][0],
                               'eta':values['genjet_eta'][0],
                               'phi':values['genjet_phi'][0],
                               })
    
        gen_df = gen_df[gen_df.pt>15][abs(gen_df.eta)>1.5]

        df = pd.DataFrame({"subdet"    : values['hgcdigi_subdet'][0],
                           'cell'      : values['hgcdigi_cell'][0],
                           'layer'     : values['hgcdigi_layer'][0],
                           'wafer'     : values['hgcdigi_wafer'][0],
                           'wafertype' : values['hgcdigi_wafertype'][0],
                           'side'      : values['hgcdigi_zside'][0],
                           'data'      : values['hgcdigi_data'][0],
                           'isadc'     : values['hgcdigi_isadc'][0],
                           'eta'       : values['hgcdigi_eta'][0],
                           'phi'       : values['hgcdigi_phi'][0],
                           }
                          )
    
        df = df[df.subdet==3][df.layer==8][df.wafertype==1][df.side==1]
#        chargeConverter = "hgcdigi_isadc ? hgcdigi_data*%f : %f + hgcdigi_data * %f"%(adcLSB_, (int(tdcOnsetfC_/adcLSB_) + 1.0)*adcLSB_, tdcLSB_)
    
        df["motherboard"] = df['wafer'].map(waferMBmap)
        df = df[df.motherboard%4==2]

        df["charge"] = np.where(df.isadc==1,df.data*adcLSB_, (int(tdcOnsetfC_/adcLSB_) + 1.0)*adcLSB_ + df.data*tdcLSB_)
        
        df["bits"] = np.where(df.charge>150, 30, np.where(df.charge>10,20,np.where(df.charge>0.7,10,0)))
    
        df["HGROC"] = np.where(df.cell>160, 3, np.where(df.cell>80,2,1))

        #print df

        group = df.ix[:,['motherboard','wafer','HGROC','bits']].groupby(['motherboard','wafer','HGROC'],as_index=False)

        event = group.sum()
        event["Ncells"] = group["bits"].count().bits
        event["event"] = iEvent+(iFile-1)*100
        

        if iFile==1 and iEvent==0:
            result = [event]
        else:
            result.append(event)
        print iEvent, '-'*20


result = pd.concat(result)
#print result

result.to_pickle("pdDF_Layer8_MB2.pkl")

#         _eventMax = result.loc[result.bits.idxmax()]

#         for i_ in xrange(len(result)):
#             i_MB = (result.motherboard.iloc[i_]-1)%4
#             h_total_bits.Fill(result.bits.iloc[i_])
#             h_total_bits_MBType[i_MB].Fill(result.bits.iloc[i_])
# #        print maxBits, _eventMax.bits

#         if _eventMax.bits > maxBits:
#             maxBits = _eventMax.bits
#             maxMB = _eventMax
#             maxEvent = iEvent
#             maxFile = iFile

# print maxMB
# print maxFile,maxEvent

# _tree = uproot.open("root://cmseos.fnal.gov//store/user/lpchgcal/ConcentratorNtuples/L1THGCal_Ntuples/RelValTTbar_14TeV/crab_RelValTTbar_14TeV/180411_205247/0000/ntuple_%i.root"%maxFile,xrootdsource=dict(chunkbytes=1024**3, limitbytes=1024**3))["hgcalTriggerNtuplizer/HGCalTriggerNtuple"]
# values = _tree.arrays(["genjet_pt","genjet_eta","genjet_phi"],entrystart=maxEvent, entrystop=maxEvent+1)

# gen_df = pd.DataFrame({'pt':values['genjet_pt'][0],
#                        'eta':values['genjet_eta'][0],
#                        'phi':values['genjet_phi'][0],
#                        })

# gen_df = gen_df[gen_df.pt>15][abs(gen_df.eta)>1.5]

# print gen_df

# outFile = ROOT.TFile("output.root","recreate")
# h_total_bits.Write()
# for i in range(4):
#     h_total_bits_MBType[i].Write()
# outFile.Close()
