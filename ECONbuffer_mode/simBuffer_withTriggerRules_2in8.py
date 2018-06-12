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

(options, args) = parser.parse_args()

smallestFirst = options.smallestFirst
applyTriggerRules = options.applyTriggerRules

TriggerRate = 1./options.TriggerFrequency

df = pd.read_pickle("pdDF_Layer8_MB2.pkl")

events = list(df.event.unique())

gROOT.SetBatch(True)
gStyle.SetOptTitle(0)
gStyle.SetOptStat(0)

h_bufferSize = TH1F("h_bufferSize","h_bufferSize",700,0,70000)
h_bufferHGROCs = TH1F("h_bufferHGROCs","h_bufferHGROCs",200,0,200)

countTriggers = 0

rand = TRandom3(0)

graph = TGraph()

N = int(options.N)
print N

print "Trigger frequency is 1 in %.1f"%options.TriggerFrequency

DAQbuffer = []
DAQbufferEvtNumber = []


bunchStructure = [72,12,288] #39 groups fo 72 filled, 12 empty, last 288 empty as abort gap

nReadoutPipelines = 8
readoutBuffer = [0]*8

drainBitsPerBX = 224/nReadoutPipelines

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

                    x.append(i_BX-1)
                    bufferBits.append(sum(DAQbuffer))
                    bufferHGROCs.append(len(DAQbuffer))
                    
                    DAQheaderbits = 24 #header
                    DAQheaderbits += 80 #bitmap
                    DAQheaderbits += 32 #trailer
                    
                    randEvent = list(df[df.event==random.choice(events)].bits)
                    for DAQbits in randEvent:
                        DAQbuffer.append(DAQbits + DAQheaderbits)

                    x.append(i_BX)
                    bufferBits.append(sum(DAQbuffer))
                    bufferHGROCs.append(len(DAQbuffer))
                    
    h_bufferSize.Fill(sum(DAQbuffer)+sum(readoutBuffer))
    h_bufferHGROCs.Fill(len(DAQbuffer))



grBits = TGraph(len(x),x,bufferBits)

grEvts = TGraph(len(x),x,bufferHGROCs)



grBits.GetXaxis().SetTitle("BX")
grEvts.GetXaxis().SetTitle("BX")

grBits.GetYaxis().SetTitle("Bits in Buffer")
grEvts.GetYaxis().SetTitle("HGROCs in Buffer")

grBits.SetNameTitle("Bits","Bits")
grEvts.SetNameTitle("HGROCs","HGROCs")

c = TCanvas("c","c",1200,600)
grBits.Draw("alp")
c.SaveAs("BitsInBuffer.png")

grEvts.Draw("alp")
c.SaveAs("HGROCsInBuffer.png")

outputName = "Buffers_byHGROC.root"
if applyTriggerRules:
    outputName = outputName.replace(".root","_withL1Rules_2in8.root")
if smallestFirst:
    outputName = outputName.replace(".root","_orderedReadout.root")
outFile = TFile(outputName,"recreate")

grBits.Write()
grEvts.Write()
h_bufferSize.Write()
h_bufferHGROCs.Write()
outFile.Close()

print "Effective L1A rate : %.1f kHZ"%(40000.*countTriggers/N)
