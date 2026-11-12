# Shot plan, output timeline (seconds). Total speech 54.12, black tail to 54.62
TOTAL=54.62; SPEECH_END=54.12
W=(670,150,440,280)   # studio wall panel (wide shots)
L=(0,80,480,305)      # left wall area (close shots)
# kinds: A=anchor (sync), B=broll strip (region, raw_start), C=cover (full-frame broll, region, raw_start, blur), S=split3 [(region,raw)...], K=black
SHOTS=[
 (0.00, 3.95,'A',{}),
 (3.95, 6.03,'C',dict(r=W,raw=4.0,blur=0)),          # "24" text-mask
 (6.03, 6.87,'A',{}),
 (6.87, 8.57,'B',dict(r=W,raw=0.6)),                 # 31 lakh
 (8.57, 9.97,'A',{}),
 (9.97,11.92,'B',dict(r=W,raw=8.0)),                 # 17,000
 (11.92,13.36,'B',dict(r=L,raw=20.3)),
 (13.36,15.00,'B',dict(r=L,raw=18.7)),               # 15,000 sachivalayam
 (15.00,16.88,'A',{}),
 (16.88,18.80,'B',dict(r=L,raw=22.3)),               # 2.5 lakh volunteers
 (18.80,19.98,'A',{}),
 (19.98,21.98,'B',dict(r=L,raw=27.0)),               # 10,500 RBK
 (21.98,23.86,'A',{}),
 (23.86,25.32,'B',dict(r=L,raw=31.8)),               # 10,000 clinics
 (25.32,26.89,'A',{}),
 (26.89,28.13,'B',dict(r=L,raw=33.5)),               # 25 lakh aarogyasri
 (28.13,29.37,'B',dict(r=L,raw=35.6)),
 (29.37,31.75,'A',{}),
 (31.75,33.31,'C',dict(r=W,raw=37.5,blur=0)),        # "17" text-mask
 (33.31,33.95,'A',{}),
 (33.95,35.25,'B',dict(r=W,raw=44.0)),               # Uddanam hospital
 (35.25,36.56,'B',dict(r=W,raw=45.3)),
 (36.56,38.38,'B',dict(r=W,raw=48.6)),               # 750 cr water
 (38.38,40.13,'A',{}),
 (40.13,43.77,'S',dict(p=[(W,1.5),(W,40.0),(W,9.0)])),  # 4 / 10 / 6
 (43.77,45.21,'B',dict(r=W,raw=54.55)),               # 17,805 cr
]
# burst 45.21-46.53: 7 cuts
bs=[(W,0.2),(L,19.5),(W,2.5),(L,27.5),(W,38.5),(L,32.2),(W,10.5)]
t=45.21; d=(46.53-45.21)/7
for r,raw in bs:
    SHOTS.append((round(t,3),round(t+d,3),'B',dict(r=r,raw=raw))); t+=d
SHOTS+=[
 (46.53,47.45,'C',dict(r=W,raw=55.2,blur=0)),               # naadu-nedu
 (47.45,49.15,'C',dict(r=W,raw=10.0,blur=1)),        # 130 card
 (49.15,51.28,'C',dict(r=W,raw=2.0,blur=1)),         # 1 lakh cr card
 (51.28,52.48,'B',dict(r=W,raw=11.0)),
 (52.48,54.12,'C',dict(r=W,raw=2.0,blur=1)),                               # anchor, end card overlays from 52.48
 (54.12,54.62,'K',{}),
]
# beats with stat cards (overlay)
STATS=[ # (start,end,number,label,kind)
 (6.87,8.57,'31','లక్షల ఇళ్ల పట్టాలు','count'),
 (9.97,11.92,'17,000','జగనన్న కాలనీలు','count'),
 (13.36,15.00,'15,000','గ్రామ సచివాలయాలు','count'),
 (16.88,18.80,'2.5','లక్షల వాలంటీర్లు','count'),
 (19.98,21.98,'10,500','రైతు భరోసా కేంద్రాలు','count'),
 (23.86,25.32,'10,000','విలేజ్ క్లినిక్‌లు','count'),
 (26.89,29.37,'₹25','లక్షల వరకు ఆరోగ్యశ్రీ','count'),
 (33.95,36.56,'ఉద్దానం','కిడ్నీ రీసెర్చ్ & సూపర్ స్పెషాలిటీ హాస్పిటల్','pin'),
 (36.56,38.38,'₹750','కోట్లతో రక్షిత మంచినీరు','count'),
 (43.77,45.21,'₹17,805','కోట్లు · నాడు-నేడు బడులు','count'),
]
