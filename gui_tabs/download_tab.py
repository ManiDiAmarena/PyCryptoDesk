import tkinter as tk
from tkinter import ttk, messagebox, filedialog # filedialog per salvare file
import threading
import queue
import csv # Per salvare in CSV
import json # Per salvare in JSON

# Import dell'api_handler
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_handler
import config_manager

class DownloadTab(ttk.Frame):
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
        self.default_file_format = self.app_config.get(
            "download_tab_default_file_format",
            config_manager.DEFAULT_CONFIG["download_tab_default_file_format"]
        )
        
        self.api_queue = queue.Queue()
        self.common_currencies = ["usd", "eur", "gbp", "jpy", "btc", "eth", "cad", "aud", "chf"]
        self.file_formats = ["CSV", "JSON"] # Lista per la ComboBox del formato
        
        self.create_widgets()
        self.process_api_queue()

    def create_widgets(self):
        input_section = ttk.Frame(self, padding=self.padding)
        input_section.pack(fill=tk.X, pady=5)

        ttk.Label(input_section, text="ID Criptovaluta:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.asset_id_entry = ttk.Entry(input_section, width=20)
        self.asset_id_entry.grid(row=0, column=1, padx=5, pady=5)
        # --- USA VALORE DA CONFIG ---
        self.asset_id_entry.insert(0, self.default_asset_id)
        # --- FINE USA VALORE DA CONFIG ---

        ttk.Label(input_section, text="Valuta di riferimento:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.vs_currency_combobox = ttk.Combobox(input_section, values=self.common_currencies, width=8, state="readonly")
        self.vs_currency_combobox.grid(row=1, column=1, padx=5, pady=5)
        # --- USA VALORE DA CONFIG ---
        if self.default_vs_currency in self.common_currencies:
            self.vs_currency_combobox.set(self.default_vs_currency)
        elif self.common_currencies:
            self.vs_currency_combobox.set(self.common_currencies[0])
        # --- FINE USA VALORE DA CONFIG ---

        ttk.Label(input_section, text="Giorni di storico:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.days_spinbox = ttk.Spinbox(input_section, from_=1, to=3650, increment=1, width=8)
        self.days_spinbox.grid(row=2, column=1, padx=5, pady=5)
        # --- USA VALORE DA CONFIG ---
        self.days_spinbox.set(self.default_days)
        # --- FINE USA VALORE DA CONFIG ---

        ttk.Label(input_section, text="Formato File:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.format_combobox = ttk.Combobox(input_section, values=self.file_formats, width=8, state="readonly")
        self.format_combobox.grid(row=3, column=1, padx=5, pady=5)
        # --- USA VALORE DA CONFIG ---
        if self.default_file_format.upper() in self.file_formats:
            self.format_combobox.set(self.default_file_format.upper())
        elif self.file_formats:
            self.format_combobox.set(self.file_formats[0])
        # --- FINE USA VALORE DA CONFIG ---

        self.download_button = ttk.Button(input_section, text="Scarica Dati Storici", command=self.start_download_thread)
        self.download_button.grid(row=4, column=0, columnspan=2, pady=10)

        # --- Frame per lo stato ---
        status_section = ttk.LabelFrame(self, text="Stato Download", padding=self.padding)
        status_section.pack(fill=tk.X, expand=True, pady=5)
        self.status_label = ttk.Label(status_section, text="Pronto per scaricare.", justify=tk.LEFT)
        self.status_label.pack(pady=5, anchor=tk.W)

    def start_download_thread(self):
        asset_id = self.asset_id_entry.get().strip().lower()
        vs_currency = self.vs_currency_combobox.get().strip().lower()
        file_format = self.format_combobox.get().lower()
        try:
            days = int(self.days_spinbox.get())
            if days <= 0:
                messagebox.showerror("Errore Input", "Il numero di giorni deve essere positivo.")
                return
        except ValueError:
            messagebox.showerror("Errore Input", "Numero di giorni non valido.")
            return

        if not asset_id or not vs_currency:
            messagebox.showerror("Errore Input", "ID Asset e Valuta di riferimento sono obbligatori.")
            return

        self.download_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Scaricamento dati per {asset_id} ({days} giorni)...")

        api_thread = threading.Thread(target=self.fetch_and_save_in_thread,
                                      args=(self.api_queue, asset_id, vs_currency, days, file_format),
                                      daemon=True)
        api_thread.start()

    def fetch_and_save_in_thread(self, q, asset_id, vs_currency, days, file_format):
        print(f"THREAD DOWNLOAD: Richiedo dati storici per {asset_id}...")
        historical_data = api_handler.get_historical_market_data(asset_id, vs_currency, str(days))
        
        if isinstance(historical_data, dict) and "error" in historical_data:
            q.put(historical_data) # Manda l'errore alla coda
            return
        
        if not (isinstance(historical_data, dict) and "data_points" in historical_data and historical_data["data_points"]):
            q.put({"error": "Nessun punto dati ricevuto o formato non valido."})
            return

        # Chiedi all'utente dove salvare il file (questo deve avvenire nel thread principale)
        # Quindi passiamo i dati alla coda e lasciamo che process_api_queue gestisca il salvataggio
        q.put({"data_to_save": historical_data, "format": file_format, "asset_id": asset_id, "days": days})


    def save_data_to_file(self, data_package):
        historical_data = data_package.get("data_to_save")
        file_format = data_package.get("format")
        asset_id = data_package.get("asset_id", "data")
        days = data_package.get("days", "N")

        default_filename = f"{asset_id}_{days}d_storico.{file_format}"
        
        if file_format == "csv":
            filetypes = [('File CSV', '*.csv')]
        elif file_format == "json":
            filetypes = [('File JSON', '*.json')]
        else:
            error_msg = f"Formato file '{file_format}' non supportato."
            self.status_label.config(text=f"Errore: {error_msg}")
            messagebox.showerror("Errore Formato File", error_msg)
            return False # Indica fallimento

        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            filetypes=filetypes,
            initialfile=default_filename,
            title=f"Salva dati storici come {file_format.upper()}"
        )

        if not filepath: # L'utente ha annullato
            self.status_label.config(text="Salvataggio annullato dall'utente.")
            return False # Indica fallimento o annullamento

        try:
            data_points = historical_data.get("data_points", [])
            if not data_points:
                self.status_label.config(text="Nessun dato da salvare.")
                return False

            if file_format == "csv":
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data_points[0].keys())
                    writer.writeheader()
                    writer.writerows(data_points)
            elif file_format == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(historical_data, f, indent=4) # Salviamo tutto il pacchetto formattato
            
            self.status_label.config(text=f"Dati salvati con successo in:\n{filepath}")
            return True # Indica successo
        except Exception as e:
            self.status_label.config(text=f"Errore durante il salvataggio:\n{e}")
            messagebox.showerror("Errore Salvataggio", f"Impossibile salvare il file:\n{e}")
            return False


    def process_api_queue(self):
        try:
            message = self.api_queue.get_nowait()
            
            if "data_to_save" in message: # È un messaggio con dati da salvare
                # La chiamata a filedialog DEVE avvenire nel thread principale
                if self.save_data_to_file(message):
                    pass # Il messaggio di successo/errore è gestito da save_data_to_file
                else:
                    # Se save_data_to_file ritorna False (es. annullato o errore)
                    if "Salvataggio annullato" not in self.status_label.cget("text"): # Evita doppio messaggio
                         self.status_label.config(text="Operazione di salvataggio fallita o annullata.")

            elif "error" in message: # È un messaggio di errore dall'API
                error_msg = message['error']
                self.status_label.config(text=f"Errore API Download: {error_msg[:100]}")
                messagebox.showerror("Errore API Download", f"Impossibile scaricare i dati:\n{error_msg}")
            else:
                self.status_label.config(text="Risposta API non riconosciuta.")

            self.download_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass
        except Exception as e:
            self.status_label.config(text=f"Errore UI Download: {e}")
            print(f"Errore in process_api_queue (DownloadTab): {e}")
            if hasattr(self, 'download_button'):
                self.download_button.config(state=tk.NORMAL)
        finally:
            self.after(100, self.process_api_queue)