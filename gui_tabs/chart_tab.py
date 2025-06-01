# In gui_tabs/chart_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
from datetime import datetime # Per convertire i timestamp

# Import dell'api_handler e config_manager
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_handler
import config_manager

# --- SCOMMENTA E AGGIUNGI QUESTI IMPORT ---
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd # Useremo pandas per gestire i dati per il grafico
# --- FINE IMPORT MATPLOTLIB/PANDAS ---


class ChartTab(ttk.Frame):
    def __init__(self, parent_notebook, *args, **kwargs):
        super().__init__(parent_notebook, *args, **kwargs)
        self.padding = kwargs.get('padding', (10, 10, 10, 10))
        
        self.app_config = config_manager.load_config()
        self.default_asset_id = self.app_config.get(
            "download_tab_default_asset_id", 
            config_manager.DEFAULT_CONFIG["download_tab_default_asset_id"]
        )
        self.default_vs_currency = self.app_config.get(
            "default_vs_currency",
            config_manager.DEFAULT_CONFIG["default_vs_currency"]
        )
        self.default_days = self.app_config.get(
            "default_download_days", 
            config_manager.DEFAULT_CONFIG["default_download_days"]
        )
        
        self.api_queue = queue.Queue()
        # Carichiamo le valute comuni dal config o usiamo un default
        common_currencies_from_config = self.app_config.get("common_currencies")
        if common_currencies_from_config and isinstance(common_currencies_from_config, list):
            self.common_currencies = common_currencies_from_config
        else: # Fallback se non presente o non è una lista
            self.common_currencies = ["usd", "eur", "gbp", "jpy", "btc", "eth"]


        self.chart_canvas_widget = None # Cambiato nome per chiarezza rispetto a self.chart_canvas in matplotlib

        self.create_widgets()
        self.process_api_queue()

    # ... (create_widgets rimane come prima) ...
    def create_widgets(self):
        controls_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        controls_frame.pack(fill=tk.X)

        ttk.Label(controls_frame, text="ID Criptovaluta:").pack(side=tk.LEFT, padx=(0, 5))
        self.asset_id_entry = ttk.Entry(controls_frame, width=15)
        self.asset_id_entry.insert(0, self.default_asset_id)
        self.asset_id_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(controls_frame, text="Valuta:").pack(side=tk.LEFT, padx=(5, 5))
        self.vs_currency_combobox = ttk.Combobox(controls_frame, values=self.common_currencies, width=8, state="readonly")
        if self.default_vs_currency in self.common_currencies:
            self.vs_currency_combobox.set(self.default_vs_currency)
        elif self.common_currencies:
            self.vs_currency_combobox.set(self.common_currencies[0])
        self.vs_currency_combobox.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(controls_frame, text="Periodo (giorni):").pack(side=tk.LEFT, padx=(5, 5))
        self.days_options = ["7", "30", "90", "180", "365", "max"]
        self.days_combobox = ttk.Combobox(controls_frame, values=self.days_options, width=5, state="readonly")
        default_days_str = str(self.default_days)
        if default_days_str in self.days_options:
            self.days_combobox.set(default_days_str)
        else:
            self.days_combobox.set("30") 
        self.days_combobox.pack(side=tk.LEFT, padx=(0, 10))
        
        self.show_chart_button = ttk.Button(controls_frame, text="Mostra Grafico", command=self.start_fetch_chart_data_thread)
        self.show_chart_button.pack(side=tk.LEFT, padx=(10,0))

        self.status_label = ttk.Label(self, text="Inserisci i dati e clicca 'Mostra Grafico'.", font=("Helvetica", 10, "italic"))
        self.status_label.pack(pady=5)

        self.chart_display_frame = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        self.chart_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chart_placeholder_label = ttk.Label(self.chart_display_frame, text="L'area del grafico apparirà qui.", font=("Helvetica", 12, "italic"))
        self.chart_placeholder_label.pack(padx=20, pady=20, expand=True)

    # --- NUOVA FUNZIONE PER DISEGNARE IL GRAFICO ---
    def _draw_chart(self, api_response_data):
        asset_id = api_response_data.get("asset_id", "N/A")
        vs_currency = api_response_data.get("vs_currency", "N/A").upper()
        data_points = api_response_data.get("data_points", [])

        if not data_points:
            self.status_label.config(text="Nessun dato da plottare.")
            messagebox.showwarning("Dati Grafico Mancanti", "Non ci sono dati sufficienti per generare il grafico.")
            return

        try:
            # Prepara i dati con Pandas
            df = pd.DataFrame(data_points)
            # Converti timestamp (millisecondi) in oggetti datetime
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms') 
            df.set_index('date', inplace=True) # Imposta la data come indice

            # Pulisci il grafico precedente, se esiste
            if self.chart_canvas_widget:
                self.chart_canvas_widget.get_tk_widget().destroy()
            
            # Rimuovi il placeholder label se esiste ancora
            if hasattr(self, 'chart_placeholder_label') and self.chart_placeholder_label.winfo_exists():
                self.chart_placeholder_label.destroy()

            # Crea la figura e l'asse di Matplotlib
            # figsize è in pollici, dpi è dots per inch
            fig = Figure(figsize=(7, 5), dpi=100) # Puoi aggiustare questi valori
            ax = fig.add_subplot(1, 1, 1) # 1 riga, 1 colonna, 1° subplot

            # Plotta i prezzi
            ax.plot(df.index, df['price'], color='dodgerblue', linewidth=1.5)

            # Formattazione del grafico
            ax.set_title(f"Andamento Prezzo di {asset_id.capitalize()} ({vs_currency})", fontsize=14)
            ax.set_xlabel("Data", fontsize=10)
            ax.set_ylabel(f"Prezzo in {vs_currency}", fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Migliora la formattazione delle date sull'asse X
            fig.autofmt_xdate() 

            # Incorpora il grafico in Tkinter
            self.chart_canvas_widget = FigureCanvasTkAgg(fig, master=self.chart_display_frame)
            self.chart_canvas_widget.draw()
            self.chart_canvas_widget.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            self.status_label.config(text=f"Grafico per {asset_id.capitalize()} visualizzato.")

        except Exception as e:
            self.status_label.config(text=f"Errore durante la creazione del grafico: {e}")
            messagebox.showerror("Errore Grafico", f"Si è verificato un errore durante la generazione del grafico:\n{e}")
            print(f"Errore _draw_chart: {e}")


    # ... (start_fetch_chart_data_thread e fetch_chart_data_in_thread rimangono invariati) ...
    def start_fetch_chart_data_thread(self):
        asset_id = self.asset_id_entry.get().strip().lower()
        vs_currency = self.vs_currency_combobox.get().strip().lower()
        days = self.days_combobox.get().strip() 

        if not asset_id or not vs_currency or not days:
            messagebox.showerror("Errore Input", "Tutti i campi (Asset, Valuta, Periodo) sono obbligatori.")
            return

        self.show_chart_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Caricamento dati grafico per {asset_id} ({days} giorni)...")
        
        if self.chart_canvas_widget: # Riferimento corretto
            self.chart_canvas_widget.get_tk_widget().destroy()
            self.chart_canvas_widget = None # Resetta il riferimento
        if hasattr(self, 'chart_placeholder_label') and self.chart_placeholder_label.winfo_exists():
            self.chart_placeholder_label.destroy()

        api_thread = threading.Thread(target=self.fetch_chart_data_in_thread,
                                      args=(self.api_queue, asset_id, vs_currency, days),
                                      daemon=True)
        api_thread.start()

    def fetch_chart_data_in_thread(self, q, asset_id, vs_currency, days):
        print(f"THREAD CHART: Richiedo dati storici per {asset_id}, {days} giorni, in {vs_currency}...")
        historical_data = api_handler.get_historical_market_data(asset_id, vs_currency, days)
        q.put(historical_data) # Mettiamo l'intero dizionario, include asset_id e vs_currency
        print(f"THREAD CHART: Dati storici messi in coda.")


    # --- MODIFICHE A process_api_queue ---
    def process_api_queue(self):
        try:
            message = self.api_queue.get_nowait() # 'message' qui è la risposta da get_historical_market_data

            if isinstance(message, dict) and "error" in message:
                error_msg = message['error']
                self.status_label.config(text=f"Errore API Grafico: {error_msg[:100]}")
                messagebox.showerror("Errore API Grafico", f"Impossibile caricare i dati per il grafico:\n{error_msg}")
                # Se c'è un errore, rimetti il placeholder se non c'è già un canvas
                if not self.chart_canvas_widget and not (hasattr(self, 'chart_placeholder_label') and self.chart_placeholder_label.winfo_exists()):
                    self.chart_placeholder_label = ttk.Label(self.chart_display_frame, text="L'area del grafico apparirà qui.", font=("Helvetica", 12, "italic"))
                    self.chart_placeholder_label.pack(padx=20, pady=20, expand=True)

            elif isinstance(message, dict) and "data_points" in message:
                # --- CHIAMATA ALLA NUOVA FUNZIONE DI PLOTTING ---
                self._draw_chart(message) 
                # Lo status_label viene aggiornato dentro _draw_chart o se ci sono errori lì
            else:
                self.status_label.config(text="Risposta API per grafico non riconosciuta.")
                messagebox.showwarning("Risposta Sconosciuta", "L'API ha restituito una risposta non prevista per il grafico.")
                # Rimetti il placeholder
                if not self.chart_canvas_widget and not (hasattr(self, 'chart_placeholder_label') and self.chart_placeholder_label.winfo_exists()):
                    self.chart_placeholder_label = ttk.Label(self.chart_display_frame, text="L'area del grafico apparirà qui.", font=("Helvetica", 12, "italic"))
                    self.chart_placeholder_label.pack(padx=20, pady=20, expand=True)


            self.show_chart_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass
        except Exception as e:
            self.status_label.config(text=f"Errore UI Grafico: {e}")
            messagebox.showerror("Errore Interfaccia Grafico", f"Si è verificato un errore nell'interfaccia Grafico:\n{e}")
            print(f"Errore in process_api_queue (ChartTab): {e}")
            if hasattr(self, 'show_chart_button'): 
                 self.show_chart_button.config(state=tk.NORMAL)
            # Rimetti il placeholder in caso di eccezione UI grave
            if not self.chart_canvas_widget and not (hasattr(self, 'chart_placeholder_label') and self.chart_placeholder_label.winfo_exists()):
                self.chart_placeholder_label = ttk.Label(self.chart_display_frame, text="L'area del grafico apparirà qui.", font=("Helvetica", 12, "italic"))
                self.chart_placeholder_label.pack(padx=20, pady=20, expand=True)
        finally:
            self.after(100, self.process_api_queue)