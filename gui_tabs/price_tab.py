import tkinter as tk
from tkinter import ttk, messagebox
import threading # Importiamo il modulo per il threading
import queue     # Importiamo il modulo per le code (comunicazione tra thread)

# Manteniamo l'import dell'api_handler come prima
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_handler
import config_manager

class PriceTab(ttk.Frame):
    def __init__(self, parent_notebook, *args, **kwargs):
        super().__init__(parent_notebook, *args, **kwargs)
        self.padding = kwargs.get('padding', (10, 10, 10, 10))
        
        # --- CARICAMENTO CONFIGURAZIONE ---
        self.app_config = config_manager.load_config()
        self.default_asset_id = self.app_config.get(
            "price_tab_default_asset_id", 
            config_manager.DEFAULT_CONFIG["price_tab_default_asset_id"]
        )
        self.default_currency = self.app_config.get(
            "price_tab_default_currency", 
            config_manager.DEFAULT_CONFIG["price_tab_default_currency"]
        )
        # --- FINE CARICAMENTO CONFIGURAZIONE ---
        
        self.api_queue = queue.Queue()
        self.common_currencies = ["usd", "eur", "gbp", "jpy", "btc", "eth", "cad", "aud", "chf"] # Manteniamo questa lista per ora
        
        self.create_widgets()
        self.process_api_queue()

    def create_widgets(self):
        input_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="ID Criptovaluta (es. bitcoin):").pack(side=tk.LEFT, padx=(0, 5))
        self.asset_id_entry = ttk.Entry(input_frame, width=20)
        self.asset_id_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.asset_id_entry.insert(0, self.default_asset_id) 

        ttk.Label(input_frame, text="Valuta:").pack(side=tk.LEFT, padx=(5, 5))
        self.currency_combobox = ttk.Combobox(input_frame, values=self.common_currencies, width=8, state="readonly")
        self.currency_combobox.pack(side=tk.LEFT, padx=(0, 10))
        if self.default_currency in self.common_currencies:
            self.currency_combobox.set(self.default_currency)
        elif self.common_currencies:
            self.currency_combobox.set(self.common_currencies[0]) 

        self.fetch_button = ttk.Button(input_frame, text="Mostra Prezzo", command=self.start_fetch_price_thread) # Modificato il comando
        self.fetch_button.pack(side=tk.LEFT)

        # ... la creazione delle etichette per i risultati rimane la stessa ...
        results_frame = ttk.LabelFrame(self, text="Risultati", padding=self.padding)
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.price_label = ttk.Label(results_frame, text="Prezzo: -", font=("Helvetica", 12))
        self.price_label.pack(pady=5, anchor=tk.W)

        self.change_24h_label = ttk.Label(results_frame, text="Variazione 24h: -", font=("Helvetica", 12))
        self.change_24h_label.pack(pady=5, anchor=tk.W)
        
        self.volume_label = ttk.Label(results_frame, text="Volume 24h: -", font=("Helvetica", 12))
        self.volume_label.pack(pady=5, anchor=tk.W)

        self.last_updated_label = ttk.Label(results_frame, text="Ultimo Aggiornamento: -", font=("Helvetica", 10))
        self.last_updated_label.pack(pady=10, anchor=tk.W)

        # Etichetta per lo stato del caricamento
        self.status_label = ttk.Label(results_frame, text="", font=("Helvetica", 10, "italic"))
        self.status_label.pack(pady=5, anchor=tk.W)

    def start_fetch_price_thread(self):
        """Avvia la chiamata API in un thread separato."""
        asset_id = self.asset_id_entry.get().strip().lower()
        currency = self.currency_combobox.get().strip().lower()

        if not asset_id or not currency:
            self.status_label.config(text="Errore: ID Asset e Valuta non possono essere vuoti.")
            # Potremmo usare anche una tkinter.messagebox qui
            return

        # Disabilita il pulsante e mostra un messaggio di caricamento
        self.fetch_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Caricamento dati per {asset_id}...")
        self.price_label.config(text="Prezzo: -") # Pulisce i risultati precedenti
        self.change_24h_label.config(text="Variazione 24h: -")
        self.volume_label.config(text="Volume 24h: -")
        self.last_updated_label.config(text="Ultimo Aggiornamento: -")
        
        # Crea e avvia il thread che eseguirà la chiamata API
        # Passiamo la coda, asset_id e currency come argomenti alla funzione target del thread
        api_thread = threading.Thread(target=self.fetch_price_in_thread, 
                                      args=(self.api_queue, asset_id, currency),
                                      daemon=True) # daemon=True fa sì che il thread si chiuda quando l'app principale si chiude
        api_thread.start()

    def fetch_price_in_thread(self, q, asset_id, currency):
        """
        Questa funzione viene eseguita nel thread separato.
        Fa la chiamata API e mette il risultato (o l'errore) nella coda.
        """
        print(f"THREAD: Richiedo prezzo per {asset_id} in {currency}...")
        price_info = api_handler.get_asset_price(asset_id, currency)
        q.put(price_info) # Mette il risultato nella coda
        print(f"THREAD: Risultato messo in coda: {price_info}")

    def process_api_queue(self):
        """
        Controlla la coda per i risultati dall'API e aggiorna la GUI.
        Viene chiamata periodicamente usando self.after().
        """
        try:
            # Prova a prendere un messaggio dalla coda senza bloccare (nowait)
            message = self.api_queue.get_nowait()

            if "error" in message:
                error_message = message['error']
                self.price_label.config(text="Prezzo: Errore")
                self.change_24h_label.config(text=f"Dettaglio: {error_message[:70]}")
                self.volume_label.config(text="Volume 24h: -")
                self.last_updated_label.config(text="Ultimo Aggiornamento: -")
                self.status_label.config(text=f"Errore API: {error_message[:70]}")
                print(f"Errore API dalla coda: {error_message}")
                messagebox.showerror("Errore API", f"Impossibile recuperare i dati:\n{error_message}")
            else:
                price_str = f"{message.get('price', 'N/D'):,.2f}" if isinstance(message.get('price'), (int, float)) else "N/D"
                change_str = f"{message.get('change_24h', 0):.2f}%" if isinstance(message.get('change_24h'), (int, float)) else "N/D"
                volume_str = f"{message.get('volume_24h', 'N/D'):,.2f}" if isinstance(message.get('volume_24h'), (int, float)) else "N/D"
            
                self.price_label.config(text=f"Prezzo: {price_str} {message.get('currency', '')}")
                self.change_24h_label.config(text=f"Variazione 24h: {change_str}")
                self.volume_label.config(text=f"Volume 24h: {volume_str} {message.get('currency', '')}")
                self.last_updated_label.config(text=f"Ultimo Aggiornamento: {message.get('last_updated', 'N/D')}")
                self.status_label.config(text=f"Dati per {self.asset_id_entry.get()} aggiornati!")

            # Riabilita il pulsante indipendentemente dal risultato
            self.fetch_button.config(state=tk.NORMAL)

        except queue.Empty: # Se la coda è vuota, non fare nulla
            pass
        finally:
            # Richiama questa funzione dopo 100 millisecondi per continuare a controllare la coda
            self.after(100, self.process_api_queue)