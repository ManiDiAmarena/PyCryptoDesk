import tkinter as tk
from tkinter import ttk, messagebox # Aggiungiamo messagebox per gli errori di input
import threading
import queue

# Import dell'api_handler
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_handler
import config_manager

class ConverterTab(ttk.Frame):
    def __init__(self, parent_notebook, *args, **kwargs):
        super().__init__(parent_notebook, *args, **kwargs)
        self.padding = kwargs.get('padding', (10, 10, 10, 10))
        
        self.app_config = config_manager.load_config()
        self.default_amount = self.app_config.get(
            "converter_tab_default_amount",
            config_manager.DEFAULT_CONFIG["converter_tab_default_amount"]
        )
        self.default_from_asset = self.app_config.get(
            "converter_tab_default_from_asset",
            config_manager.DEFAULT_CONFIG["converter_tab_default_from_asset"]
        )
        self.default_to_currency = self.app_config.get(
            "converter_tab_default_to_currency",
            config_manager.DEFAULT_CONFIG["converter_tab_default_to_currency"]
        )

        self.api_queue = queue.Queue()
        self.common_currencies = ["usd", "eur", "gbp", "jpy", "btc", "eth", "cad", "aud", "chf"]
        
        self.create_widgets()
        self.process_api_queue()

    def create_widgets(self):
        input_section = ttk.Frame(self, padding=self.padding)
        input_section.pack(fill=tk.X, pady=5)

        ttk.Label(input_section, text="Importo da convertire:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.amount_entry = ttk.Entry(input_section, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)
        # --- USA VALORE DA CONFIG ---
        self.amount_entry.insert(0, self.default_amount)
        # --- FINE USA VALORE DA CONFIG ---

        ttk.Label(input_section, text="Da Criptovaluta (ID es. bitcoin):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.from_asset_entry = ttk.Entry(input_section, width=20)
        self.from_asset_entry.grid(row=1, column=1, padx=5, pady=5)
        # --- USA VALORE DA CONFIG ---
        self.from_asset_entry.insert(0, self.default_from_asset)
        # --- FINE USA VALORE DA CONFIG ---

        ttk.Label(input_section, text="A Valuta:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.to_currency_combobox = ttk.Combobox(input_section, values=self.common_currencies, width=8, state="readonly")
        self.to_currency_combobox.grid(row=2, column=1, padx=5, pady=5)
        # --- USA VALORE DA CONFIG ---
        if self.default_to_currency in self.common_currencies:
            self.to_currency_combobox.set(self.default_to_currency)
        elif self.common_currencies: # Fallback al primo della lista se il default non c'è
            self.to_currency_combobox.set(self.common_currencies[0])
        # --- FINE USA VALORE DA CONFIG ---
        
        self.convert_button = ttk.Button(input_section, text="Converti", command=self.start_conversion_thread)
        self.convert_button.grid(row=3, column=0, columnspan=2, pady=10)

        # --- Frame per i risultati ---
        result_section = ttk.LabelFrame(self, text="Risultato Conversione", padding=self.padding)
        result_section.pack(fill=tk.X, expand=True, pady=5)

        self.result_label = ttk.Label(result_section, text="Risultato: -", font=("Helvetica", 14))
        self.result_label.pack(pady=10)

        self.rate_label = ttk.Label(result_section, text="Tasso di cambio (1 From Asset = X To Currency): -", font=("Helvetica", 10, "italic"))
        self.rate_label.pack(pady=5)
        
        self.status_label = ttk.Label(result_section, text="", font=("Helvetica", 10, "italic"))
        self.status_label.pack(pady=5)

    def start_conversion_thread(self):
        try:
            amount_str = self.amount_entry.get().strip()
            from_asset = self.from_asset_entry.get().strip().lower()
            to_currency = self.to_currency_combobox.get().strip().lower()

            if not amount_str or not from_asset or not to_currency:
                messagebox.showerror("Errore Input", "Tutti i campi sono obbligatori.")
                return

            amount = float(amount_str) # Converte l'importo in float, può sollevare ValueError
            if amount <= 0:
                messagebox.showerror("Errore Input", "L'importo deve essere positivo.")
                return

        except ValueError:
            messagebox.showerror("Errore Input", "L'importo inserito non è un numero valido.")
            return
        
        self.convert_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Conversione in corso per {amount} {from_asset}...")
        self.result_label.config(text="Risultato: -")
        self.rate_label.config(text="Tasso di cambio: -")

        api_thread = threading.Thread(target=self.fetch_conversion_in_thread,
                                      args=(self.api_queue, amount, from_asset, to_currency),
                                      daemon=True)
        api_thread.start()

    def fetch_conversion_in_thread(self, q, amount, from_asset, to_currency):
        print(f"THREAD CONVERTER: Richiedo tasso per {from_asset} in {to_currency}...")
        # Usiamo get_asset_price per ottenere il tasso di 1 'from_asset' in 'to_currency'
        # La funzione get_asset_price già ci ritorna un dizionario che include 'price' e 'currency'
        rate_info = api_handler.get_asset_price(from_asset, to_currency) 
        
        result_package = {
            "amount": amount,
            "from_asset": from_asset,
            "to_currency": to_currency, # la valuta di destinazione
            "rate_info": rate_info # contiene 'price', 'currency' (che sarà to_currency), 'error', ecc.
        }
        q.put(result_package)
        print(f"THREAD CONVERTER: Dati messi in coda.")

    def process_api_queue(self):
        try:
            message = self.api_queue.get_nowait()
            # Rimuoviamo il testo dallo status_label all'inizio dell'elaborazione del messaggio
            self.status_label.config(text="") 

            amount = message.get("amount")
            from_asset_display = message.get("from_asset", "").capitalize()
            to_currency_display = message.get("to_currency", "").upper()
            rate_info = message.get("rate_info", {})

            if "error" in rate_info:
                error_msg = rate_info['error']
                self.result_label.config(text="Risultato: Errore")
                self.rate_label.config(text=f"Dettaglio: {error_msg[:70]}")
                self.status_label.config(text=f"Errore API.") # Messaggio di stato più conciso
                # --- AGGIUNTA MESSAGEBOX PER ERRORE API ---
                messagebox.showerror("Errore API Conversione", f"Impossibile ottenere il tasso di cambio:\n{error_msg}")
                # --- FINE AGGIUNTA ---
            else:
                current_rate = rate_info.get("price")
                if current_rate is not None and isinstance(current_rate, (int, float)):
                    converted_amount = amount * current_rate
                    
                    result_text = f"{converted_amount:,.8f} {to_currency_display}"
                    rate_text = f"(1 {from_asset_display} = {current_rate:,.8f} {to_currency_display})"
                    
                    self.result_label.config(text=f"Risultato: {result_text}")
                    self.rate_label.config(text=rate_text)
                    status_final_text = "Conversione completata!"
                    self.status_label.config(text=status_final_text)
                    # --- AGGIUNTA MESSAGEBOX PER SUCCESSO (Opzionale) ---
                    messagebox.showinfo("Conversione Riuscita", f"{amount} {from_asset_display} = {result_text}\n{rate_text}")
                    # --- FINE AGGIUNTA ---
                else:
                    self.result_label.config(text="Risultato: Errore")
                    self.rate_label.config(text="Tasso di cambio non disponibile.")
                    self.status_label.config(text="Errore: dati di tasso mancanti.")
                    messagebox.showwarning("Dati Mancanti", "L'API non ha fornito un tasso di cambio valido.") # AGGIUNTO

            self.convert_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass
        except Exception as e:
            self.status_label.config(text=f"Errore UI: {e}")
            messagebox.showerror("Errore Interfaccia", f"Si è verificato un errore nell'interfaccia Convertitore:\n{e}")
            print(f"Errore in process_api_queue (ConverterTab): {e}")
            if hasattr(self, 'convert_button'):
                 self.convert_button.config(state=tk.NORMAL)
        finally:
            self.after(100, self.process_api_queue)