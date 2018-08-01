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

parser.add_option("--layer", dest="layer",default=8,type="int",
		  help="Layer to run on" )

parser.add_option("--rate", dest="rate",default=640,type="int",
		  help="Readout rate, in MHz" )

parser.add_option("--graphs", dest="saveGraphs",default=False,action="store_true",
		  help="Save graphs of buffer as function of BX" )

parser.add_option("-f",dest="inputFile",default="../Pandas_DF/pdDF_Subdet3_Layer6to8_MB2_FineWafers.pkl",
                  help="Input file (.pkl with dataframe)")

(options, args) = parser.parse_args()

smallestFirst = options.smallestFirst
applyTriggerRules = options.applyTriggerRules

TriggerRate = 1./options.TriggerFrequency

df = pd.read_pickle(options.inputFile)

events = list(df.event.unique())
layers = list(df.layer.unique())

df = df[df.layer==options.layer]
#df = df[df.side==1]

gROOT.SetBatch(True)
gStyle.SetOptTitle(0)
gStyle.SetOptStat(0)

#counter just to verify effective trigger rate
countTriggers = 0

rand = TRandom3(0)

graph = TGraph()

N = int(options.N)

print N

print "Trigger frequency is 1 in %.1f"%options.TriggerFrequency

nHGROCs = 12

DAQbuffer = [ [] for i in range(nHGROCs)]

#LHC bunch structure, for determining when an L1A can be issued
bunchStructure = [72,12,288] #39 groups fo 72 filled, 12 empty, last 288 empty as abort gap

readoutBuffer = [0]*nHGROCs

drainFrequency = options.rate

drainBitsPerBX = drainFrequency / 40

print drainBitsPerBX

#make histograms to store the buffer sizes
h_bufferSize = [TH1F("h_bufferSize_%i"%i_ROC,"h_bufferSize_%i"%i_ROC,1500,0,30000) for i_ROC in range(nHGROCs)]
h_bufferEvents = [TH1F("h_bufferEvents_%i"%i_ROC,"h_bufferEvents_%i"%i_ROC,60,0,60) for i_ROC in range(nHGROCs)]

#make graphs to save buffer size vs event
if options.saveGraphs:
    x = []
    bufferBits = []
    bufferEvents = []
    for i in range(nHGROCs):
        x.append(array.array('i'))
        bufferBits.append(array.array('i'))
        bufferEvents.append(array.array('i'))


lastTenL1As = [-999]*10

n_Log = N/40

for i_BX in xrange(N):
    # if i_BX%n_Log==0:
    #     print i_BX
    

    #drain buffers
    for _i in range(nHGROCs):
        if readoutBuffer[_i]>drainBitsPerBX:
            readoutBuffer[_i] -= drainBitsPerBX
        else:
            readoutBuffer[_i] = 0
            if options.saveGraphs:
                if len(DAQbuffer[_i])==0:
                    x[_i].append(i_BX)
                    bufferBits[_i].append(0)
                    bufferEvents[_i].append(0)


    #if readout buffer is empty, grab next event from buffer list (either sorted or not)
    for i_ROC in range(nHGROCs):
        if readoutBuffer[i_ROC]==0 and len(DAQbuffer[i_ROC])>0:
            if smallestFirst:
                DAQbuffer[i_ROC].sort()

            readoutBuffer[i_ROC] = DAQbuffer[i_ROC][0]
            DAQbuffer[i_ROC] = DAQbuffer[i_ROC][1:]
            

#    print readoutBuffer[0], DAQbuffer[0]
    orbitBXnumber = i_BX%3456

    #decide if we are in a good spot to issue a trigger
    if orbitBXnumber < (3564-288):   #not in abort gap
        if orbitBXnumber%84 < 72:    # 72 filled, 12 empty pattern
            if rand.Uniform()<TriggerRate:  #random number to get L1A
                if i_BX-lastTenL1As[-2]>=8 or not applyTriggerRules:
                    lastTenL1As.append(i_BX)

                    if len(lastTenL1As)>10:
                        lastTenL1As = lastTenL1As[1:]

                    countTriggers += 1

                    DAQheaderbits = 24 #header
                    DAQheaderbits += 80 #bitmap
                    DAQheaderbits += 32 #trailer
                    
                    
                    # select a random motherboard (random event, side)
                    
                    randEvent = df[df.event==random.choice(events)]
                    randEvent = randEvent[randEvent.side==random.choice([-1,1])]
#                    randEvent = randEvent[randEvent.layer==random.choice(layers)]
                    

                    randEventBits = list(randEvent.bits)

                    for i_ROC in range(nHGROCs):
                        if options.saveGraphs:
                            x[i_ROC].append(i_BX-1)
                            bufferBits[i_ROC].append(sum(DAQbuffer[i_ROC]) + readoutBuffer[i_ROC] )
                            bufferEvents[i_ROC].append(len(DAQbuffer[i_ROC]) + 1)
                                
                        DAQbuffer[i_ROC].append(randEventBits[i_ROC] + DAQheaderbits)

                        if options.saveGraphs:
                            x[i_ROC].append(i_BX)
                            bufferBits[i_ROC].append(sum(DAQbuffer[i_ROC]) + readoutBuffer[i_ROC] )
                            bufferEvents[i_ROC].append(len(DAQbuffer[i_ROC]) + 1)
                    

                    
    for i_ROC in range(nHGROCs):
        h_bufferSize[i_ROC].Fill(sum(DAQbuffer[i_ROC])+readoutBuffer[i_ROC])
        h_bufferEvents[i_ROC].Fill(len(DAQbuffer[i_ROC]))


grBits = []
grEvts = []

if options.saveGraphs:
    for i_ROC in range(nHGROCs):
    #    print i_ROC, len(x[i_ROC]), len(bufferBits[i_ROC]), x[i_ROC] ,bufferBits[i_ROC]
        grBits.append(TGraph(len(x[i_ROC]),x[i_ROC],bufferBits[i_ROC]))
        grEvts.append(TGraph(len(x[i_ROC]),x[i_ROC],bufferEvents[i_ROC]))
        
        grBits[i_ROC].GetXaxis().SetTitle("BX")
        grEvts[i_ROC].GetXaxis().SetTitle("BX")
        
        grBits[i_ROC].GetYaxis().SetTitle("Bits in Buffer")
        grEvts[i_ROC].GetYaxis().SetTitle("HGROCs in Buffer")
        
        grBits[i_ROC].SetNameTitle("Bits_%i"%i_ROC,"Bits_%i"%i_ROC)
        grEvts[i_ROC].SetNameTitle("HGROCs_%i"%i_ROC,"HGROCs_%i"%i_ROC)
        

outputName = "Buffers_byHGROC_Layer%s_Readout%s.root"%(options.layer, options.rate)
if applyTriggerRules:
    outputName = outputName.replace(".root","_withL1Rules_2in8.root")
if smallestFirst:
    outputName = outputName.replace(".root","_orderedReadout.root")
outFile = TFile(outputName,"recreate")

for i_ROC in range(nHGROCs):
    h_bufferSize[i_ROC].Write()
    h_bufferEvents[i_ROC].Write()
    if options.saveGraphs:
        grBits[i_ROC].Write()
        grEvts[i_ROC].Write()

outFile.Close()

print "Effective L1A rate : %.1f kHZ"%(40000.*countTriggers/N)
