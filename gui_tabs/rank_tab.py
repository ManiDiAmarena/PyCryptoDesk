import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue

# Import dell'api_handler
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_handler
import config_manager

class RankTab(ttk.Frame):
    def __init__(self, parent_notebook, *args, **kwargs):
        super().__init__(parent_notebook, *args, **kwargs)
        self.padding = kwargs.get('padding', (10, 10, 10, 10))
        
        self.app_config = config_manager.load_config()
        self.default_top_n = self.app_config.get(
            "default_rank_top_n",
            config_manager.DEFAULT_CONFIG["default_rank_top_n"]
        )
        self.default_currency = self.app_config.get(
            "default_vs_currency", # Usiamo la chiave generica per la valuta
            config_manager.DEFAULT_CONFIG["default_vs_currency"]
        )
        
        self.api_queue = queue.Queue()
        self.common_currencies = ["usd", "eur", "gbp", "jpy", "btc", "eth", "cad", "aud", "chf"]
        
        self.create_widgets()
        self.process_api_queue()
        self.start_fetch_rank_thread()

    def create_widgets(self):
        controls_frame = ttk.Frame(self, padding=(0,0,0,10))
        controls_frame.pack(fill=tk.X)

        ttk.Label(controls_frame, text="Numero risultati (Top N):").pack(side=tk.LEFT, padx=(0,5))
        self.top_n_spinbox = ttk.Spinbox(controls_frame, from_=5, to=100, increment=5, width=5)
        # --- USA VALORE DA CONFIG ---
        self.top_n_spinbox.set(self.default_top_n) 
        # --- FINE USA VALORE DA CONFIG ---
        self.top_n_spinbox.pack(side=tk.LEFT, padx=(0,10))

        ttk.Label(controls_frame, text="Valuta:").pack(side=tk.LEFT, padx=(5,5)) 
        self.currency_combobox = ttk.Combobox(controls_frame, values=self.common_currencies, width=8, state="readonly")
        # --- USA VALORE DA CONFIG ---
        if self.default_currency in self.common_currencies:
            self.currency_combobox.set(self.default_currency)
        elif self.common_currencies:
            self.currency_combobox.set(self.common_currencies[0])
        # --- FINE USA VALORE DA CONFIG ---
        self.currency_combobox.pack(side=tk.LEFT, padx=(0,10))

        self.fetch_button = ttk.Button(controls_frame, text="Mostra Classifica", command=self.start_fetch_rank_thread)
        self.fetch_button.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(controls_frame, text="", font=("Helvetica", 10, "italic"))
        self.status_label.pack(side=tk.LEFT, padx=10)

        # --- Treeview per la classifica ---
        columns = ('rank', 'name', 'price', 'change_1h', 'change_24h', 'change_7d', 'market_cap', 'volume_24h')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=20)

        # Intestazioni
        self.tree.heading('rank', text='Rank')
        self.tree.heading('name', text='Nome (Simbolo)')
        self.tree.heading('price', text='Prezzo')
        self.tree.heading('change_1h', text='1h %')
        self.tree.heading('change_24h', text='24h %')
        self.tree.heading('change_7d', text='7gg %')
        self.tree.heading('market_cap', text='Market Cap')
        self.tree.heading('volume_24h', text='Volume 24h')

        # Larghezza colonne e allineamento
        col_widths = {'rank': 50, 'name': 200, 'price': 120, 'change_1h': 80, 
                      'change_24h': 80, 'change_7d': 80, 'market_cap': 150, 'volume_24h': 150}
        col_anchors = {'rank': tk.CENTER, 'name': tk.W, 'price': tk.E, 'change_1h': tk.E,
                       'change_24h': tk.E, 'change_7d': tk.E, 'market_cap': tk.E, 'volume_24h': tk.E}

        for col, width in col_widths.items():
            self.tree.column(col, width=width, anchor=col_anchors[col], stretch=tk.NO)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def start_fetch_rank_thread(self):
        try:
            top_n = int(self.top_n_spinbox.get())
            vs_currency = self.currency_combobox.get().strip().lower()
            if top_n <= 0 or not vs_currency:
                messagebox.showerror("Errore Input", "Numero risultati deve essere > 0 e valuta non vuota.")
                return
        except ValueError:
            messagebox.showerror("Errore Input", "Numero risultati non valido.")
            return
            
        self.fetch_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Caricamento Top {top_n} in {vs_currency.upper()}...")
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        api_thread = threading.Thread(target=self.fetch_rank_in_thread,
                                      args=(self.api_queue, vs_currency, top_n),
                                      daemon=True)
        api_thread.start()

    def fetch_rank_in_thread(self, q, vs_currency, top_n):
        print(f"THREAD RANK: Richiedo Top {top_n} in {vs_currency}...")
        data = api_handler.get_market_cap_ranking(vs_currency, top_n)
        q.put({"data": data, "currency": vs_currency.upper()}) # Passiamo anche la valuta per le intestazioni
        print(f"THREAD RANK: Dati messi in coda.")

    def process_api_queue(self):
        try:
            message_package = self.api_queue.get_nowait()
            message_data = message_package.get("data") # 'data' contiene la lista di coin o il dizionario di errore
            currency_display = message_package.get("currency", "")
            
            self.status_label.config(text="") # Pulisce lo status label

            if isinstance(message_data, dict) and "error" in message_data:
                error_msg = message_data['error']
                self.status_label.config(text=f"Errore API Rank: {error_msg[:70]}")
                # --- AGGIUNTA MESSAGEBOX PER ERRORE API ---
                messagebox.showerror("Errore API Classifica", f"Impossibile caricare la classifica:\n{error_msg}")
                # --- FINE AGGIUNTA ---
            elif isinstance(message_data, list):
                # ... (la logica per popolare il Treeview rimane invariata) ...
                self.tree.heading('price', text=f'Prezzo ({currency_display})')
                self.tree.heading('market_cap', text=f'Market Cap ({currency_display})')
                self.tree.heading('volume_24h', text=f'Volume 24h ({currency_display})')

                for coin in message_data:
                    price_str = f"{coin.get('current_price', 'N/D'):,.2f}" if isinstance(coin.get('current_price'), (int, float)) else "N/D"
                    mc_str = f"{coin.get('market_cap', 'N/D'):,.0f}" if isinstance(coin.get('market_cap'), (int, float)) else "N/D" 
                    vol_str = f"{coin.get('total_volume_24h', 'N/D'):,.0f}" if isinstance(coin.get('total_volume_24h'), (int, float)) else "N/D"
                    
                    chg_1h_str = f"{coin.get('price_change_1h', 0):.2f}%" if isinstance(coin.get('price_change_1h'), (int, float)) else "N/D"
                    chg_24h_str = f"{coin.get('price_change_24h', 0):.2f}%" if isinstance(coin.get('price_change_24h'), (int, float)) else "N/D"
                    chg_7d_str = f"{coin.get('price_change_7d', 0):.2f}%" if isinstance(coin.get('price_change_7d'), (int, float)) else "N/D"

                    self.tree.insert('', tk.END, values=(
                        coin.get('rank', 'N/D'),
                        f"{coin.get('name', 'N/D')} ({coin.get('symbol', 'N/D')})",
                        price_str,
                        chg_1h_str,
                        chg_24h_str,
                        chg_7d_str,
                        mc_str,
                        vol_str
                    ))
                self.status_label.config(text="Classifica aggiornata!")
                # Non aggiungiamo messagebox.showinfo qui perché l'aggiornamento della tabella è già un feedback visivo forte.
            else:
                self.status_label.config(text="Errore: Risposta API non valida per Rank.")
                messagebox.showwarning("Risposta Sconosciuta", "L'API ha restituito una risposta non prevista per la Classifica.")


            self.fetch_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass
        except Exception as e:
            self.status_label.config(text=f"Errore UI Rank: {e}")
            messagebox.showerror("Errore Interfaccia", f"Si è verificato un errore nell'interfaccia Classifica:\n{e}")
            print(f"Errore in process_api_queue (RankTab): {e}")
            if hasattr(self, 'fetch_button'):
                self.fetch_button.config(state=tk.NORMAL)
        finally:
            self.after(100, self.process_api_queue)