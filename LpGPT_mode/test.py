import pandas as pd

df = pd.read_pickle("pdDF_Layer8_MB2.pkl")

#df = df[df.wafer==261][df.HGROC==1]


# for wafer in [183, 208, 234, 261]:
#     for HGROC in [1,2,3]:
#         d = df[df.wafer==wafer]
#         d = d[d.HGROC==HGROC]
#         print wafer, HGROC, d.bits.mean()
