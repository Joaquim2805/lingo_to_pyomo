\ Model ChocoDelice
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  500 x[Montreal,N,1] + 500 x[Montreal,N,2] + 500 x[Montreal,N,3]
   + 400 x[Montreal,L,1] + 400 x[Montreal,L,2] + 400 x[Montreal,L,3]
   + 600 x[Quebec,N,1] + 600 x[Quebec,N,2] + 600 x[Quebec,N,3]
   + 300 x[Quebec,L,1] + 300 x[Quebec,L,2] + 300 x[Quebec,L,3]
   + 300 y[Montreal,Gatineau,N,1] + 300 y[Montreal,Gatineau,N,2]
   + 300 y[Montreal,Gatineau,N,3] + 300 y[Montreal,Gatineau,L,1]
   + 300 y[Montreal,Gatineau,L,2] + 300 y[Montreal,Gatineau,L,3]
   + 400 y[Montreal,Sherbrooke,N,1] + 400 y[Montreal,Sherbrooke,N,2]
   + 400 y[Montreal,Sherbrooke,N,3] + 400 y[Montreal,Sherbrooke,L,1]
   + 400 y[Montreal,Sherbrooke,L,2] + 400 y[Montreal,Sherbrooke,L,3]
   + 600 y[Montreal,Saguenay,N,1] + 600 y[Montreal,Saguenay,N,2]
   + 600 y[Montreal,Saguenay,N,3] + 600 y[Montreal,Saguenay,L,1]
   + 600 y[Montreal,Saguenay,L,2] + 600 y[Montreal,Saguenay,L,3]
   + 500 y[Quebec,Gatineau,N,1] + 500 y[Quebec,Gatineau,N,2]
   + 500 y[Quebec,Gatineau,N,3] + 500 y[Quebec,Gatineau,L,1]
   + 500 y[Quebec,Gatineau,L,2] + 500 y[Quebec,Gatineau,L,3]
   + 600 y[Quebec,Sherbrooke,N,1] + 600 y[Quebec,Sherbrooke,N,2]
   + 600 y[Quebec,Sherbrooke,N,3] + 600 y[Quebec,Sherbrooke,L,1]
   + 600 y[Quebec,Sherbrooke,L,2] + 600 y[Quebec,Sherbrooke,L,3]
   + 300 y[Quebec,Saguenay,N,1] + 300 y[Quebec,Saguenay,N,2]
   + 300 y[Quebec,Saguenay,N,3] + 300 y[Quebec,Saguenay,L,1]
   + 300 y[Quebec,Saguenay,L,2] + 300 y[Quebec,Saguenay,L,3]
   + 150 z[Montreal,N,1] + 150 z[Montreal,N,2] + 150 z[Montreal,N,3]
   + 150 z[Montreal,L,1] + 150 z[Montreal,L,2] + 150 z[Montreal,L,3]
   + 250 z[Quebec,N,1] + 250 z[Quebec,N,2] + 250 z[Quebec,N,3]
   + 250 z[Quebec,L,1] + 250 z[Quebec,L,2] + 250 z[Quebec,L,3]
   + 300 w[N,Gatineau,1] + 300 w[N,Gatineau,2] + 300 w[N,Gatineau,3]
   + 200 w[N,Sherbrooke,1] + 200 w[N,Sherbrooke,2] + 200 w[N,Sherbrooke,3]
   + 400 w[N,Saguenay,1] + 400 w[N,Saguenay,2] + 400 w[N,Saguenay,3]
   + 300 w[L,Gatineau,1] + 300 w[L,Gatineau,2] + 300 w[L,Gatineau,3]
   + 200 w[L,Sherbrooke,1] + 200 w[L,Sherbrooke,2] + 200 w[L,Sherbrooke,3]
   + 400 w[L,Saguenay,1] + 400 w[L,Saguenay,2] + 400 w[L,Saguenay,3]
   + 14 s[Montreal,N,1] + 14 s[Montreal,N,2] + 14 s[Montreal,N,3]
   + 14 s[Montreal,L,1] + 14 s[Montreal,L,2] + 14 s[Montreal,L,3]
   + 14 s[Quebec,N,1] + 14 s[Quebec,N,2] + 14 s[Quebec,N,3]
   + 14 s[Quebec,L,1] + 14 s[Quebec,L,2] + 14 s[Quebec,L,3] + 8 s[TR,N,1]
   + 8 s[TR,N,2] + 8 s[TR,N,3] + 8 s[TR,L,1] + 8 s[TR,L,2] + 8 s[TR,L,3]
   + 9000 e[Gatineau,N,1] + 9000 e[Gatineau,N,2] + 9000 e[Gatineau,N,3]
   + 9000 e[Gatineau,L,1] + 9000 e[Gatineau,L,2] + 9000 e[Gatineau,L,3]
   + 9000 e[Sherbrooke,N,1] + 9000 e[Sherbrooke,N,2]
   + 9000 e[Sherbrooke,N,3] + 9000 e[Sherbrooke,L,1]
   + 9000 e[Sherbrooke,L,2] + 9000 e[Sherbrooke,L,3] + 9000 e[Saguenay,N,1]
   + 9000 e[Saguenay,N,2] + 9000 e[Saguenay,N,3] + 9000 e[Saguenay,L,1]
   + 9000 e[Saguenay,L,2] + 9000 e[Saguenay,L,3] + 200 a_c[1] + 200 a_c[2]
   + 200 a_c[3] + 100 a_l[1] + 100 a_l[2] + 100 a_l[3]
Subject To
 Cap_Montreal_1: 2 x[Montreal,N,1] + x[Montreal,L,1] <= 180
 Cap_Montreal_2: 2 x[Montreal,N,2] + x[Montreal,L,2] <= 140
 Cap_Montreal_3: 2 x[Montreal,N,3] + x[Montreal,L,3] <= 90
 Cap_Quebec_1: 2 x[Quebec,N,1] + x[Quebec,L,1] <= 120
 Cap_Quebec_2: 2 x[Quebec,N,2] + x[Quebec,L,2] <= 110
 Cap_Quebec_3: 2 x[Quebec,N,3] + x[Quebec,L,3] <= 110
 BilanUsine_Montreal_N_1: x[Montreal,N,1] - y[Montreal,Gatineau,N,1]
   - y[Montreal,Sherbrooke,N,1] - y[Montreal,Saguenay,N,1]
   - z[Montreal,N,1] - s[Montreal,N,1] = -10
 BilanUsine_Montreal_N_2: x[Montreal,N,2] - y[Montreal,Gatineau,N,2]
   - y[Montreal,Sherbrooke,N,2] - y[Montreal,Saguenay,N,2]
   - z[Montreal,N,2] + s[Montreal,N,1] - s[Montreal,N,2] = 0
 BilanUsine_Montreal_N_3: x[Montreal,N,3] - y[Montreal,Gatineau,N,3]
   - y[Montreal,Sherbrooke,N,3] - y[Montreal,Saguenay,N,3]
   - z[Montreal,N,3] + s[Montreal,N,2] - s[Montreal,N,3] = 0
 BilanUsine_Montreal_L_1: x[Montreal,L,1] - y[Montreal,Gatineau,L,1]
   - y[Montreal,Sherbrooke,L,1] - y[Montreal,Saguenay,L,1]
   - z[Montreal,L,1] - s[Montreal,L,1] = -10
 BilanUsine_Montreal_L_2: x[Montreal,L,2] - y[Montreal,Gatineau,L,2]
   - y[Montreal,Sherbrooke,L,2] - y[Montreal,Saguenay,L,2]
   - z[Montreal,L,2] + s[Montreal,L,1] - s[Montreal,L,2] = 0
 BilanUsine_Montreal_L_3: x[Montreal,L,3] - y[Montreal,Gatineau,L,3]
   - y[Montreal,Sherbrooke,L,3] - y[Montreal,Saguenay,L,3]
   - z[Montreal,L,3] + s[Montreal,L,2] - s[Montreal,L,3] = 0
 BilanUsine_Quebec_N_1: x[Quebec,N,1] - y[Quebec,Gatineau,N,1]
   - y[Quebec,Sherbrooke,N,1] - y[Quebec,Saguenay,N,1] - z[Quebec,N,1]
   - s[Quebec,N,1] = -5
 BilanUsine_Quebec_N_2: x[Quebec,N,2] - y[Quebec,Gatineau,N,2]
   - y[Quebec,Sherbrooke,N,2] - y[Quebec,Saguenay,N,2] - z[Quebec,N,2]
   + s[Quebec,N,1] - s[Quebec,N,2] = 0
 BilanUsine_Quebec_N_3: x[Quebec,N,3] - y[Quebec,Gatineau,N,3]
   - y[Quebec,Sherbrooke,N,3] - y[Quebec,Saguenay,N,3] - z[Quebec,N,3]
   + s[Quebec,N,2] - s[Quebec,N,3] = 0
 BilanUsine_Quebec_L_1: x[Quebec,L,1] - y[Quebec,Gatineau,L,1]
   - y[Quebec,Sherbrooke,L,1] - y[Quebec,Saguenay,L,1] - z[Quebec,L,1]
   - s[Quebec,L,1] = -5
 BilanUsine_Quebec_L_2: x[Quebec,L,2] - y[Quebec,Gatineau,L,2]
   - y[Quebec,Sherbrooke,L,2] - y[Quebec,Saguenay,L,2] - z[Quebec,L,2]
   + s[Quebec,L,1] - s[Quebec,L,2] = 0
 BilanUsine_Quebec_L_3: x[Quebec,L,3] - y[Quebec,Gatineau,L,3]
   - y[Quebec,Sherbrooke,L,3] - y[Quebec,Saguenay,L,3] - z[Quebec,L,3]
   + s[Quebec,L,2] - s[Quebec,L,3] = 0
 BilanTR_N_1: z[Montreal,N,1] + z[Quebec,N,1] - w[N,Gatineau,1]
   - w[N,Sherbrooke,1] - w[N,Saguenay,1] - s[TR,N,1] = 0
 BilanTR_N_2: z[Montreal,N,2] + z[Quebec,N,2] - w[N,Gatineau,2]
   - w[N,Sherbrooke,2] - w[N,Saguenay,2] + s[TR,N,1] - s[TR,N,2] = 0
 BilanTR_N_3: z[Montreal,N,3] + z[Quebec,N,3] - w[N,Gatineau,3]
   - w[N,Sherbrooke,3] - w[N,Saguenay,3] + s[TR,N,2] - s[TR,N,3] = 0
 BilanTR_L_1: z[Montreal,L,1] + z[Quebec,L,1] - w[L,Gatineau,1]
   - w[L,Sherbrooke,1] - w[L,Saguenay,1] - s[TR,L,1] = 0
 BilanTR_L_2: z[Montreal,L,2] + z[Quebec,L,2] - w[L,Gatineau,2]
   - w[L,Sherbrooke,2] - w[L,Saguenay,2] + s[TR,L,1] - s[TR,L,2] = 0
 BilanTR_L_3: z[Montreal,L,3] + z[Quebec,L,3] - w[L,Gatineau,3]
   - w[L,Sherbrooke,3] - w[L,Saguenay,3] + s[TR,L,2] - s[TR,L,3] = 0
 Demande_Gatineau_N_1: y[Montreal,Gatineau,N,1] + y[Quebec,Gatineau,N,1]
   + w[N,Gatineau,1] + e[Gatineau,N,1] = 25
 Demande_Gatineau_N_2: y[Montreal,Gatineau,N,2] + y[Quebec,Gatineau,N,2]
   + w[N,Gatineau,2] + e[Gatineau,N,2] = 35
 Demande_Gatineau_N_3: y[Montreal,Gatineau,N,3] + y[Quebec,Gatineau,N,3]
   + w[N,Gatineau,3] + e[Gatineau,N,3] = 40
 Demande_Gatineau_L_1: y[Montreal,Gatineau,L,1] + y[Quebec,Gatineau,L,1]
   + w[L,Gatineau,1] + e[Gatineau,L,1] = 25
 Demande_Gatineau_L_2: y[Montreal,Gatineau,L,2] + y[Quebec,Gatineau,L,2]
   + w[L,Gatineau,2] + e[Gatineau,L,2] = 35
 Demande_Gatineau_L_3: y[Montreal,Gatineau,L,3] + y[Quebec,Gatineau,L,3]
   + w[L,Gatineau,3] + e[Gatineau,L,3] = 40
 Demande_Sherbrooke_N_1: y[Montreal,Sherbrooke,N,1]
   + y[Quebec,Sherbrooke,N,1] + w[N,Sherbrooke,1] + e[Sherbrooke,N,1] = 20
 Demande_Sherbrooke_N_2: y[Montreal,Sherbrooke,N,2]
   + y[Quebec,Sherbrooke,N,2] + w[N,Sherbrooke,2] + e[Sherbrooke,N,2] = 25
 Demande_Sherbrooke_N_3: y[Montreal,Sherbrooke,N,3]
   + y[Quebec,Sherbrooke,N,3] + w[N,Sherbrooke,3] + e[Sherbrooke,N,3] = 30
 Demande_Sherbrooke_L_1: y[Montreal,Sherbrooke,L,1]
   + y[Quebec,Sherbrooke,L,1] + w[L,Sherbrooke,1] + e[Sherbrooke,L,1] = 20
 Demande_Sherbrooke_L_2: y[Montreal,Sherbrooke,L,2]
   + y[Quebec,Sherbrooke,L,2] + w[L,Sherbrooke,2] + e[Sherbrooke,L,2] = 25
 Demande_Sherbrooke_L_3: y[Montreal,Sherbrooke,L,3]
   + y[Quebec,Sherbrooke,L,3] + w[L,Sherbrooke,3] + e[Sherbrooke,L,3] = 30
 Demande_Saguenay_N_1: y[Montreal,Saguenay,N,1] + y[Quebec,Saguenay,N,1]
   + w[N,Saguenay,1] + e[Saguenay,N,1] = 15
 Demande_Saguenay_N_2: y[Montreal,Saguenay,N,2] + y[Quebec,Saguenay,N,2]
   + w[N,Saguenay,2] + e[Saguenay,N,2] = 20
 Demande_Saguenay_N_3: y[Montreal,Saguenay,N,3] + y[Quebec,Saguenay,N,3]
   + w[N,Saguenay,3] + e[Saguenay,N,3] = 25
 Demande_Saguenay_L_1: y[Montreal,Saguenay,L,1] + y[Quebec,Saguenay,L,1]
   + w[L,Saguenay,1] + e[Saguenay,L,1] = 15
 Demande_Saguenay_L_2: y[Montreal,Saguenay,L,2] + y[Quebec,Saguenay,L,2]
   + w[L,Saguenay,2] + e[Saguenay,L,2] = 20
 Demande_Saguenay_L_3: y[Montreal,Saguenay,L,3] + y[Quebec,Saguenay,L,3]
   + w[L,Saguenay,3] + e[Saguenay,L,3] = 25
 StockCap_Montreal_1: s[Montreal,N,1] + s[Montreal,L,1] <= 30
 StockCap_Montreal_2: s[Montreal,N,2] + s[Montreal,L,2] <= 30
 StockCap_Montreal_3: s[Montreal,N,3] + s[Montreal,L,3] <= 30
 StockCap_Quebec_1: s[Quebec,N,1] + s[Quebec,L,1] <= 20
 StockCap_Quebec_2: s[Quebec,N,2] + s[Quebec,L,2] <= 20
 StockCap_Quebec_3: s[Quebec,N,3] + s[Quebec,L,3] <= 20
 StockCap_TR_1: s[TR,N,1] + s[TR,L,1] <= 50
 StockCap_TR_2: s[TR,N,2] + s[TR,L,2] <= 50
 StockCap_TR_3: s[TR,N,3] + s[TR,L,3] <= 50
 Cacao_1: 0.6 x[Montreal,N,1] + 0.4 x[Montreal,L,1] + 0.6 x[Quebec,N,1]
   + 0.4 x[Quebec,L,1] - a_c[1] <= 0
 Lait_1: 0.4 x[Montreal,N,1] + 0.6 x[Montreal,L,1] + 0.4 x[Quebec,N,1]
   + 0.6 x[Quebec,L,1] - a_l[1] <= 0
 Cacao_2: 0.6 x[Montreal,N,2] + 0.4 x[Montreal,L,2] + 0.6 x[Quebec,N,2]
   + 0.4 x[Quebec,L,2] - a_c[2] <= 0
 Lait_2: 0.4 x[Montreal,N,2] + 0.6 x[Montreal,L,2] + 0.4 x[Quebec,N,2]
   + 0.6 x[Quebec,L,2] - a_l[2] <= 0
 Cacao_3: 0.6 x[Montreal,N,3] + 0.4 x[Montreal,L,3] + 0.6 x[Quebec,N,3]
   + 0.4 x[Quebec,L,3] - a_c[3] <= 0
 Lait_3: 0.4 x[Montreal,N,3] + 0.6 x[Montreal,L,3] + 0.4 x[Quebec,N,3]
   + 0.6 x[Quebec,L,3] - a_l[3] <= 0
Bounds
End
