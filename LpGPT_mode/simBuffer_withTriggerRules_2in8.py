from ROOT import *
import array
import numpy

import random

import pandas as pd

from optparse import OptionParser
parser = OptionParser()
parser.add_option("--smallestFirst","--ordered", dest="smallestFirst", default=False,action="store_true",
		  help="Always readout the smallest sized HGROCs first" )
parser.add_option("--triggerRules", dest="applyTriggerRules", default=False,action="store_true",
		  help="Apply 2 L1A in 8 BX trigger rule" )

parser.add_option("--freq", dest="TriggerFrequency",default=42.5,type="float",
		  help="L1A frequency, randomly 1 out of N events (default 42.5)" )

parser.add_option("-N", dest="N",default=40e6,type="int",
		  help="Number of events to run on" )

(options, args) = parser.parse_args()

smallestFirst = options.smallestFirst
applyTriggerRules = options.applyTriggerRules

TriggerRate = 1./options.TriggerFrequency

df = pd.read_pickle("pdDF_Layer8_MB2.pkl")

events = list(df.event.unique())

gROOT.SetBatch(True)
gStyle.SetOptTitle(0)
gStyle.SetOptStat(0)

countTriggers = 0

rand = TRandom3(0)

graph = TGraph()

N = int(options.N)

print N

print "Trigger frequency is 1 in %.1f"%options.TriggerFrequency

nHGROCs = 12

DAQbuffer = [ [] for i in range(nHGROCs)]

bunchStructure = [72,12,288] #39 groups fo 72 filled, 12 empty, last 288 empty as abort gap

readoutBuffer = [0]*nHGROCs

drainFrequency = 640

drainBitsPerBX = 8960/drainFrequency

h_bufferSize = [TH1F("h_bufferSize_%i"%i_ROC,"h_bufferSize_%i"%i_ROC,700,0,7000) for i_ROC in range(nHGROCs)]
h_bufferEvents = [TH1F("h_bufferEvents_%i"%i_ROC,"h_bufferEvents_%i"%i_ROC,20,0,20) for i_ROC in range(nHGROCs)]



x = array.array('i')
bufferBits = array.array('i')
bufferEvents = array.array('i')

lastTenL1As = [-999]*10

n_Log = N/40

for i_BX in xrange(N):
    # if i_BX%n_Log==0:
    #     print i_BX
    
    
    for _i in range(nHGROCs):
        if readoutBuffer[_i]>drainBitsPerBX:
            readoutBuffer[_i] -= drainBitsPerBX
        else:
            readoutBuffer[_i] = 0


    for i_ROC in range(nHGROCs):
        if readoutBuffer[i_ROC]==0 and len(DAQbuffer[i_ROC])>0:
            if smallestFirst:
                DAQbuffer[i_ROC].sort()

            readoutBuffer[i_ROC] = DAQbuffer[i_ROC][0]
            DAQbuffer[i_ROC] = DAQbuffer[i_ROC][1:]




    orbitBXnumber = i_BX%3456
    if orbitBXnumber < (3564-288):   #not in abort gap
        if orbitBXnumber%84 < 72:    # 72 filled, 12 empty pattern
            if rand.Uniform()<TriggerRate:
                if i_BX-lastTenL1As[-2]>=8 or not applyTriggerRules:
                    lastTenL1As.append(i_BX)

                    if len(lastTenL1As)>10:
                        lastTenL1As = lastTenL1As[1:]

                    countTriggers += 1

                    # x.append(i_BX-1)
                    # bufferBits.append(sum(DAQbuffer))
                    # bufferEvents.append(len(DAQbuffer))
                    
                    DAQheaderbits = 24 #header
                    DAQheaderbits += 80 #bitmap
                    DAQheaderbits += 32 #trailer
                    
                    randEvent = list(df[df.event==random.choice(events)].bits)                    
                    for i_ROC in range(nHGROCs):
                        
                        DAQbuffer[i_ROC].append(randEvent[i_ROC] + DAQheaderbits)

                    
    for i_ROC in range(nHGROCs):
        h_bufferSize[i_ROC].Fill(sum(DAQbuffer[i_ROC])+readoutBuffer[i_ROC])
        h_bufferEvents[i_ROC].Fill(len(DAQbuffer[i_ROC]))



# grBits = TGraph(len(x),x,bufferBits)

# grEvts = TGraph(len(x),x,bufferEvents)



# grBits.GetXaxis().SetTitle("BX")
# grEvts.GetXaxis().SetTitle("BX")

# grBits.GetYaxis().SetTitle("Bits in Buffer")
# grEvts.GetYaxis().SetTitle("HGROCs in Buffer")

# grBits.SetNameTitle("Bits","Bits")
# grEvts.SetNameTitle("HGROCs","HGROCs")

# c = TCanvas("c","c",1200,600)
# grBits.Draw("alp")
# c.SaveAs("BitsInBuffer.png")

# grEvts.Draw("alp")
# c.SaveAs("HGROCsInBuffer.png")

outputName = "Buffers_byHGROC.root"
if applyTriggerRules:
    outputName = outputName.replace(".root","_withL1Rules_2in8.root")
if smallestFirst:
    outputName = outputName.replace(".root","_orderedReadout.root")
outFile = TFile(outputName,"recreate")

for i_ROC in range(nHGROCs):
    h_bufferSize[i_ROC].Write()
    h_bufferEvents[i_ROC].Write()

outFile.Close()

print countTriggers
