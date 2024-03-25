import numpy as np
import pandas as pd
from pulp import *
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class OptimizationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Production Planning Optimization Pro Deco")
        self.root.configure(bg="#4C2A85") 
        self.create_widgets()

    def create_widgets(self):
        # Add labels, entry fields, and buttons
        optimize_button = ttk.Button(self.root, text="Run Optimization", command=self.solve_optimization)
        optimize_button.pack(pady=10)
        button_frame = tk.Frame(self.root, bg="#4C2A85")
        button_frame.pack()
        pro_deco_button = ttk.Button(button_frame, text="Show Pro Deco Graphics", command=self.show_pro_deco_graphics)
        pro_deco_button.pack(side=tk.LEFT,pady=10)

       

        produit_p1_button = ttk.Button(button_frame, text="Show Produit P1 Graphics", command=self.show_produit_p1_graphics)
        produit_p1_button.pack(side=tk.LEFT, padx=10)

        produit_p2_button = ttk.Button(button_frame, text="Show Produit P2 Graphics", command=self.show_produit_p2_graphics)
        produit_p2_button.pack(side=tk.LEFT, padx=10)

        self.results_text = tk.Text(self.root, wrap=tk.WORD, width=80, height=20)
        self.results_text.pack(padx=10, pady=10)
    def solve_optimization(self):
     df = pd.read_csv("Projet.csv",sep=';')
     #Remove rows where all values in specific columns are NaN
     columns_to_check = ['01/04/2024', '01/05/2024', '01/06/2024', '01/07/2024', '01/08/2024', '01/09/2024']
     df_cleaned = df.dropna(subset=columns_to_check, how='all')
     df_cleaned = df_cleaned.drop(columns=['Unnamed: 7'], axis=1)
     demandes_P1 = np.array([1400.0, 1700.0, 1000.0, 1100.0, 1300.0, 1500.0])
     demandes_P2 = np.array([2400.0, 1800.0, 1200.0, 700.0, 900.0, 1900.0])
     # Convert to integers
     demandes_P1_int = demandes_P1.astype(int)
     demandes_P2_int = demandes_P2.astype(int)
     #***************minhoni ybda model*********************
     model=LpProblem("planification_de_la_production",LpMinimize)
     #variables de decision
     mois = range(1, 7)
     decalage=range(0,7)
     x1 = LpVariable.dicts('production_p1',(t for t in mois), lowBound=0, cat='Integer') #production du mois 1 jusqu'à 6
     x2 = LpVariable.dicts('production_p2', (t for t in mois) , lowBound=0, cat='Integer')
     S1 = LpVariable.dicts('stock_p1', (t for t in decalage), lowBound=0, cat='Integer')#stock du mois 0 jusqu'à 6
     S2 = LpVariable.dicts('stock_p2', (t for t in decalage), lowBound=0, cat='Integer')
     R1 = LpVariable.dicts('quantite_rupture_p1', (t for t in decalage), lowBound=0, cat='Integer')#rupture du mois 0 jusqu'à 6
     R2 = LpVariable.dicts('quantite_rupture_p2', (t for t in decalage), lowBound=0, cat='Integer')
     ST1= LpVariable.dicts('quantite_soustraitance_p1', (t for t in mois), lowBound=0, cat='Integer')#soustraitance du mois 1 jusqu'à 6
     ST2= LpVariable.dicts('quantite_soustraitance_p2', (t for t in mois), lowBound=0, cat='Integer')
     E=[LpVariable(f'E{j}', lowBound=0, cat='Integer') for j in decalage] #effective du mois 0 jusqu'à 6
     L=[LpVariable(f'L{j}', lowBound=0, cat='Integer') for j in mois]#licenciement du mois 1 jusqu'à 6
     NE=[LpVariable(f'NE{j}', lowBound=0, cat='Integer') for j in mois]#nombre d'embeuche du mois 1 jusqu'à 6

     #fonction objective
     model += lpSum(45*(x1[t]+x2[t])+8*(S1[t]+S2[t])+40*(R1[t]+R2[t])+(80+45)*ST1[t]+(60+45)*ST2[t]+
               800*NE[t-1]+1600*L[t-1]+(18*20*8)*E[t]
               for t in range(1,7)) #x1,x2,S1,S2,ST1,ST2,E de 1 à 6
                                                                                                             #L,NE de 0 à 5
    
     # Constraints
     model += S1[0] == 0, "Initial_Stock_P1"
     model += S2[0] == 0, "Initial_Stock_P2"
     model += (lpSum(x1[t] + ST1[t] for t in mois)) >= 8000, "Production_Soustraitance_P1_Constraint"
     model += (lpSum(x2[t] + ST2[t] for t in mois)) >= 8900, "Production_Soustraitance_P2_Constraint"
     model += E[0] == 65, "Initial_Effective"
     model += E[1] == 65, "Effective_Month_1"
     model += R1[0] == 0, "Initial_Rupture_P1"
     model += R2[0] == 0, "Initial_Rupture_P2"
     for t in range(2, 7):
          model += S1[t] - R1[t] == S1[t - 1] - R1[t - 1] + x1[t] - demandes_P1_int[t - 1] + ST1[t], f"Balance_P1_Month_{t}"
          model += S2[t] - R2[t] == S2[t - 1] - R2[t - 1] + x2[t] - demandes_P2_int[t - 1] + ST2[t], f"Balance_P2_Month_{t}"

     for t in range(1, 7):
         model += ((3.5 * x1[t]) + (2.5 * x2[t])) <= 8 * 20 * E[t], f"Working_Hours_Constraint_{t}"

     for t in range(2, 7):
         model += E[t] == E[t-1] - L[t-1] + NE[t-1], f"Effective_Workforce_Evolution_{t}"

     model.solve()
     total_cost = round(value(model.objective), 2)
     # Extract results
     results = f"Status Optimal: {LpStatus[model.status]}\n"
     results += f"Cout total: {total_cost}\n\n"
     for t in range(1, 7):
            
            results += f"\n***********************Mois {t}****************************\n "
            results += f"P1 Production: {int(value(x1[t]))}, P2 Production: {int(value(x2[t]))}\n "
            results += f"P1 Stock: {int(value(S1[t]))}, P2 Stock: {int(value(S2[t]))}\n "
            results += f"P1 Rupture: {int(value(R1[t]))}, P2 Rupture: {int(value(R2[t]))}\n"
            results += f" P1 Soustraitance: {int(value(ST1[t]))}, P2 Soustraitance: {int(value(ST2[t]))}\n"
            results += f" Effectif: {int(value(E[t]) if t < 6 else 0)}\n "
            results += f"Licenciement: {int(value(L[t-1]) if t < 6 else 0)}\n"
            results += f" Nombre d'embauche: {int(value(NE[t-1]) if t < 6 else 0)}\n "
     self.results_text.delete(1.0, tk.END)  # Clear previous results
     self.results_text.insert(tk.END, results)

    def show_pro_deco_graphics(self):
        self.show_graphics("Pro Deco Graphics", {"Avril": 65, "Mai": 65, "Juin": 46, "Juillet": 46, "Aout": 46, "Septembre": 46},
                           {"Avril": 0, "Mai": 0, "Juin": 19, "Juillet": 0, "Aout": 0, "Sep": 0},
                           {"Avril": 0, "Mai": 0, "Juin": 0, "Juillet": 0, "Aout": 0, "Septembre": 0})

    def show_produit_p1_graphics(self):
        production = {"Avril": 1255, "Mai": 1960, "Juin": 1245, "Juillet": 1602, "Aout": 1460, "Septembre": 745}
        self.show_graphics_in_window("Produit P1 Graphics", production)

    def show_produit_p2_graphics(self):
        production = {"Avril": 2403, "Mai": 1794, "Juin": 1201, "Juillet": 701, "Aout": 900, "Septembre": 1901}
        self.show_graphics_in_window("Produit P2 Graphics", production)

    def show_graphics_in_window(self, title, data):
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(data.keys(), data.values())
        ax.set_title(f"{title} - Production par mois")
        ax.set_xlabel("Mois")
        ax.set_ylabel("Production")

        graphics_window = tk.Toplevel(self.root)
        graphics_window.title(f"{title} Graphics")
        graphics_window.configure(bg="#4C2A85")

        canvas = FigureCanvasTkAgg(fig, graphics_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

    def show_graphics(self, title, effectif, licenciement, embauche):
        plt.rcParams["axes.prop_cycle"] = plt.cycler(
            color=["#4C2A85", "#BE96FF", "#957DAD", "#5E366E", "#A98CCC"])

        fig1, ax1 = plt.subplots(figsize=(5, 4))
        ax1.bar(effectif.keys(), effectif.values())
        ax1.set_title(f"{title} - Effectif par mois")
        ax1.set_xlabel("Mois")
        ax1.set_ylabel("Effectif")

        fig2, ax2 = plt.subplots(figsize=(5, 4))
        ax2.barh(list(licenciement.keys()), licenciement.values())
        ax2.set_title(f"{title} - Licenciement par mois")
        ax2.set_xlabel("Licenciement")

        ax2.set_xlim(left=0, right=20)
        ax2.set_xticks(range(0, 21, 10))

        fig4, ax4 = plt.subplots(figsize=(5, 4))
        ax4.plot(list(embauche.keys()), list(embauche.values()))
        ax4.set_title(f"{title} - Embauche par mois ")
        ax4.set_xlabel("mois")
        ax4.set_ylabel("Embauche")

        graphics_window = tk.Toplevel(self.root)
        graphics_window.title(f"{title} Graphics")
        graphics_window.configure(bg="#4C2A85")

        side_frame = tk.Frame(graphics_window, bg="#4C2A85")
        side_frame.pack(side="left", fill="y")

        label_text = f"Analyse\n{title}\n\n\ncout optimal=\n1712036.0"
        label = tk.Label(side_frame, text=label_text, bg="#4C2A85", fg="#FFF", font=25)
        label.pack(pady=50, padx=20)

        charts_frame = tk.Frame(graphics_window)
        charts_frame.pack()

        upper_frame = tk.Frame(charts_frame)
        upper_frame.pack(fill="both", expand=True)

        canvas1 = FigureCanvasTkAgg(fig1, upper_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side="left", fill="both", expand=True)

        canvas2 = FigureCanvasTkAgg(fig2, upper_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side="left", fill="both", expand=True)

        lower_frame = tk.Frame(charts_frame)
        lower_frame.pack(fill="both", expand=True)

        canvas4 = FigureCanvasTkAgg(fig4, lower_frame)
        canvas4.draw()
        canvas4.get_tk_widget().pack(side="left", fill="both", expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = OptimizationApp(root)
    root.mainloop()
