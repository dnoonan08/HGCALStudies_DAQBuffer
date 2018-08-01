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
parser.add_option("--freq", dest="TriggerFrequency", default=42.5,type="float",
		  help="L1A frequency, randomly 1 out of N events (default 42.5)" )

parser.add_option("--NoBunchStructure", dest="IgnoreBunchStructure", default=False,action="store_true",
		  help="Ignore the more realistic bunch structure" )

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

gROOT.SetBatch(True)
gStyle.SetOptTitle(0)
gStyle.SetOptStat(0)

h_bufferSize = TH1F("h_bufferSize","h_bufferSize",1000,0,100000)
h_bufferHGROCs = TH1F("h_bufferHGROCs","h_bufferHGROCs",250,0,250)

countTriggers = 0

rand = TRandom3(0)

graph = TGraph()

N = int(options.N)
print N

print "Trigger frequency is 1 in %.1f"%options.TriggerFrequency

DAQbuffer = []
DAQbufferEvtNumber = []


bunchStructure = [72,12,288] #39 groups fo 72 filled, 12 empty, last 288 empty as abort gap

nReadoutPipelines = 7
readoutBuffer = [0]*nReadoutPipelines

drainBitsPerBX = 224/nReadoutPipelines

if options.saveGraphs:
    x = array.array('i')
    bufferBits = array.array('i')
    bufferHGROCs = array.array('i')

lastTenL1As = [-999]*10

n_Log = N/40

for i_BX in xrange(N):
    # if i_BX%n_Log==0:
    #     print i_BX
    
    
    for _i in range(nReadoutPipelines):
        if readoutBuffer[_i]>drainBitsPerBX:
            readoutBuffer[_i] -= drainBitsPerBX
        else:
            readoutBuffer[_i] = 0

    while 0 in readoutBuffer and len(DAQbuffer) > 0:
        readoutBuffer.remove(0)
        if smallestFirst:
            DAQbuffer.sort()

        readoutBuffer.append(DAQbuffer[0])
        DAQbuffer = DAQbuffer[1:]

    if options.saveGraphs:
        if sum(DAQbuffer)==0:
            x.append(i_BX)
            bufferBits.append(sum(DAQbuffer))
            bufferHGROCs.append(len(DAQbuffer))


    orbitBXnumber = i_BX%3456
    if orbitBXnumber < (3564-288):   #not in abort gap
        if orbitBXnumber%84 < 72:    # 72 filled, 12 empty pattern
            if rand.Uniform()<TriggerRate:
                if i_BX-lastTenL1As[-2]>=8 or not applyTriggerRules:
                    lastTenL1As.append(i_BX)

                    if len(lastTenL1As)>10:
                        lastTenL1As = lastTenL1As[1:]

                    countTriggers += 1

                    if options.saveGraphs:
                        x.append(i_BX-1)
                        bufferBits.append(sum(DAQbuffer))
                        bufferHGROCs.append(len(DAQbuffer))
                    
                    DAQheaderbits = 24 #header
                    DAQheaderbits += 80 #bitmap
                    DAQheaderbits += 32 #trailer
                    
                    randEvent = df[df.event==random.choice(events)]
                    randEvent = randEvent[randEvent.side==random.choice([-1,1])]

                    randEventBits = list(randEvent.bits)

                    for DAQbits in randEventBits:
                        DAQbuffer.append(DAQbits + DAQheaderbits)

                    if options.saveGraphs:
                        x.append(i_BX)
                        bufferBits.append(sum(DAQbuffer))
                        bufferHGROCs.append(len(DAQbuffer))
                    
    h_bufferSize.Fill(sum(DAQbuffer)+sum(readoutBuffer))
    h_bufferHGROCs.Fill(len(DAQbuffer))



if options.saveGraphs:
    grBits = TGraph(len(x),x,bufferBits)

    grEvts = TGraph(len(x),x,bufferHGROCs)

    grBits.GetXaxis().SetTitle("BX")
    grEvts.GetXaxis().SetTitle("BX")

    grBits.GetYaxis().SetTitle("Bits in Buffer")
    grEvts.GetYaxis().SetTitle("HGROCs in Buffer")
    
    grBits.SetNameTitle("Bits","Bits")
    grEvts.SetNameTitle("HGROCs","HGROCs")
    

outputName = "Buffers_byHGROC_Layer%s_Readout%s.root"%(options.layer, options.rate)
if applyTriggerRules:
    outputName = outputName.replace(".root","_withL1Rules_2in8.root")
if smallestFirst:
    outputName = outputName.replace(".root","_orderedReadout.root")
outFile = TFile(outputName,"recreate")

if options.saveGraphs:
    grBits.Write()
    grEvts.Write()
h_bufferSize.Write()
h_bufferHGROCs.Write()
outFile.Close()

print "Effective L1A rate : %.1f kHZ"%(40000.*countTriggers/N)
