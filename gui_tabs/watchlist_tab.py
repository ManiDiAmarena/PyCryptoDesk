import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue

# Import dell'api_handler come nel price_tab
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import api_handler
import config_manager

class WatchlistTab(ttk.Frame):
    def __init__(self, parent_notebook, *args, **kwargs):
        super().__init__(parent_notebook, *args, **kwargs)
        self.padding = kwargs.get('padding', (10, 10, 10, 10))

        self.app_config = config_manager.load_config() # Carica l'intera configurazione
        
        # Usa i valori dalla configurazione, con fallback ai default del config_manager
        # se per qualche motivo non fossero nel file (es. file config vecchio o modificato male)
        self.watchlist_ids = self.app_config.get(
            "watchlist_ids", 
            config_manager.DEFAULT_CONFIG["watchlist_ids"]
        )
        self.target_currency = self.app_config.get(
            "default_vs_currency", 
            config_manager.DEFAULT_CONFIG["default_vs_currency"]
        )
        
        self.api_queue = queue.Queue()
        self.create_widgets()
        self.process_api_queue()
        self.start_fetch_watchlist_thread() # Carica i dati all'avvio della scheda
    
    def add_asset_to_watchlist(self):
        new_asset_id = self.new_asset_entry.get().strip().lower()

        if not new_asset_id:
            messagebox.showwarning("Input Vuoto", "Inserisci un ID asset da aggiungere.")
            return

        if new_asset_id in self.watchlist_ids:
            messagebox.showinfo("Asset Esistente", f"'{new_asset_id.capitalize()}' è già nella watchlist.")
            self.new_asset_entry.delete(0, tk.END) # Pulisce l'entry
            return
        
        # Qui potremmo aggiungere una validazione API opzionale per l'asset ID
        # Ma per ora procediamo direttamente con l'aggiunta

        self.watchlist_ids.append(new_asset_id)
        self.app_config["watchlist_ids"] = self.watchlist_ids # Aggiorna la lista nel dizionario di config

        if config_manager.save_config(self.app_config):
            messagebox.showinfo("Watchlist Aggiornata", f"'{new_asset_id.capitalize()}' aggiunto alla watchlist e configurazione salvata.")
            self.new_asset_entry.delete(0, tk.END) # Pulisce l'entry
            self.start_fetch_watchlist_thread() # Ricarica e aggiorna il Treeview
        else:
            messagebox.showerror("Errore Salvataggio", "Impossibile salvare la configurazione aggiornata.")
            # Rimuovi l'asset aggiunto localmente se il salvataggio fallisce
            if new_asset_id in self.watchlist_ids:
                self.watchlist_ids.remove(new_asset_id)
    
    def remove_selected_from_watchlist(self):
        selected_iids = self.tree.selection() # Ottiene gli iid degli elementi selezionati

        if not selected_iids:
            messagebox.showwarning("Nessuna Selezione", "Seleziona uno o più asset da rimuovere dalla watchlist.")
            return

        assets_removed_count = 0
        asset_names_removed = []

        for item_iid in selected_iids:
            # Grazie all'uso di iid=asset_id, item_iid è l'ID originale lowercase dell'asset
            # a meno che non sia una riga di errore (che inizierà con "error_")
            if item_iid.startswith("error_"): 
                print(f"Tentativo di rimuovere una riga di errore '{item_iid}', ignorato.")
                continue # Non rimuovere le righe di errore in questo modo

            if item_iid in self.watchlist_ids:
                self.watchlist_ids.remove(item_iid)
                assets_removed_count += 1
                asset_names_removed.append(item_iid.capitalize())
        
        if assets_removed_count > 0:
            self.app_config["watchlist_ids"] = self.watchlist_ids # Aggiorna la config
            if config_manager.save_config(self.app_config):
                removed_names_str = ", ".join(asset_names_removed)
                messagebox.showinfo("Watchlist Aggiornata", 
                                    f"{assets_removed_count} asset ({removed_names_str}) rimossi dalla watchlist e configurazione salvata.")
                self.start_fetch_watchlist_thread() # Ricarica e aggiorna il Treeview
            else:
                messagebox.showerror("Errore Salvataggio", "Impossibile salvare la configurazione dopo la rimozione.")
                # Se il salvataggio fallisce, dovremmo ripristinare self.watchlist_ids? 
                # Per ora, non lo facciamo per semplicità, ma in un'app reale sarebbe da considerare.
                # Per ora, ricarichiamo comunque la watchlist per riflettere lo stato attuale di self.watchlist_ids
                self.start_fetch_watchlist_thread() 
        else:
            # Questo caso potrebbe verificarsi se gli iid selezionati non erano più in self.watchlist_ids
            # o se sono state selezionate solo righe di errore non rimovibili
            messagebox.showinfo("Nessuna Modifica", "Nessun asset valido selezionato per la rimozione o asset già rimossi.")

    def create_widgets(self):
        # --- Frame Superiore per Refresh e Status ---
        top_controls_frame = ttk.Frame(self)
        top_controls_frame.pack(fill=tk.X, pady=(0,5)) # Leggero padding sotto

        self.refresh_button = ttk.Button(top_controls_frame, text="Aggiorna Watchlist", command=self.start_fetch_watchlist_thread)
        self.refresh_button.pack(side=tk.LEFT, padx=(0,10))
        
        self.status_label = ttk.Label(top_controls_frame, text="", font=("Helvetica", 10, "italic"))
        self.status_label.pack(side=tk.LEFT, padx=10)
        if not self.app_config.get("watchlist_ids"): 
            self.status_label.config(text="Watchlist vuota. Aggiungi asset qui sotto.")

        # --- NUOVO: Frame per Aggiungere/Rimuovere Asset ---
        edit_frame = ttk.Frame(self, padding=(0, 5, 0, 10)) # Padding sopra e sotto
        edit_frame.pack(fill=tk.X)

        ttk.Label(edit_frame, text="ID Asset da Aggiungere:").pack(side=tk.LEFT, padx=(0,5))
        self.new_asset_entry = ttk.Entry(edit_frame, width=20)
        self.new_asset_entry.pack(side=tk.LEFT, padx=(0,10))

        self.add_button = ttk.Button(edit_frame, text="Aggiungi", command=self.add_asset_to_watchlist)
        self.add_button.pack(side=tk.LEFT, padx=(0,5))

        self.remove_button = ttk.Button(edit_frame, text="Rimuovi Selezionato", command=self.remove_selected_from_watchlist)
        self.remove_button.pack(side=tk.LEFT, padx=(5,0))
        # --- FINE NUOVO FRAME ---

        # Treeview per mostrare i dati della watchlist (come prima)
        columns = ('asset_id', 'price', 'change_24h', 'volume_24h', 'last_updated')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=15)
        # ... (configurazione treeview, headings, columns, scrollbar rimane come prima) ...
        self.tree.heading('asset_id', text='Asset ID')
        self.tree.heading('price', text=f'Prezzo ({self.target_currency.upper()})')
        self.tree.heading('change_24h', text='Variazione 24h (%)')
        self.tree.heading('volume_24h', text=f'Volume 24h ({self.target_currency.upper()})')
        self.tree.heading('last_updated', text='Ultimo Agg.')

        self.tree.column('asset_id', width=120, anchor=tk.W)
        self.tree.column('price', width=120, anchor=tk.E)
        self.tree.column('change_24h', width=150, anchor=tk.E)
        self.tree.column('volume_24h', width=180, anchor=tk.E)
        self.tree.column('last_updated', width=150, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def start_fetch_watchlist_thread(self):
        self.refresh_button.config(state=tk.DISABLED)
        self.status_label.config(text="Aggiornamento watchlist...")

        # Pulisce il treeview prima di ricaricare
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        api_thread = threading.Thread(target=self.fetch_watchlist_in_thread,
                                      args=(self.api_queue, self.watchlist_ids, [self.target_currency]),
                                      daemon=True)
        api_thread.start()

    def fetch_watchlist_in_thread(self, q, asset_ids_list, vs_currencies_list):
        print(f"THREAD WATCHLIST: Richiedo dati per {asset_ids_list} in {vs_currencies_list}...")
        data = api_handler.get_watchlist_prices(asset_ids_list, vs_currencies_list)
        q.put(data)
        print(f"THREAD WATCHLIST: Dati messi in coda: {len(data) if not 'error' in data else 'ERRORE'}")


    def process_api_queue(self):
        try:
            message = self.api_queue.get_nowait()
            current_status_text = "" 

            if isinstance(message, dict) and "error" in message:
                error_msg = message['error']
                current_status_text = f"Errore API Watchlist: {error_msg[:70]}"
                print(f"Errore API Watchlist dalla coda: {error_msg}")
                messagebox.showerror("Errore API Watchlist", f"Impossibile aggiornare la watchlist:\n{error_msg}")
            elif isinstance(message, dict): 
                items_processed = 0
                for asset_id, data_by_currency in message.items(): # asset_id qui è già lowercase
                    items_processed += 1
                    if "error" in data_by_currency:
                        # --- MODIFICA QUI: Aggiungi iid anche per le righe di errore ---
                        self.tree.insert('', tk.END, iid=f"error_{asset_id}", values=( # iid univoco per errori
                            asset_id.capitalize(), 
                            "Errore", 
                            data_by_currency['error'][:30], 
                            "-", 
                            "-"
                        ))
                        continue

                    details = data_by_currency.get(self.target_currency)
                    if details:
                        price_str = f"{details.get('price', 'N/D'):,.2f}" if isinstance(details.get('price'), (int, float)) else "N/D"
                        change_str = f"{details.get('change_24h', 0):.2f}" if isinstance(details.get('change_24h'), (int, float)) else "N/D"
                        volume_str = f"{details.get('volume_24h', 'N/D'):,.2f}" if isinstance(details.get('volume_24h'), (int, float)) else "N/D"
                        
                        # --- MODIFICA QUI: Aggiungi iid=asset_id ---
                        self.tree.insert('', tk.END, iid=asset_id, values=( # Usa l'asset_id originale come iid
                            asset_id.capitalize(), # Visualizza capitalizzato
                            price_str,
                            change_str,
                            volume_str,
                            data_by_currency.get('last_updated', 'N/D')
                        ))
                        # --- FINE MODIFICA ---
                if items_processed > 0:
                    current_status_text = "Watchlist aggiornata!"
                else: 
                    current_status_text = "Nessun dato ricevuto per la watchlist."
            else: 
                current_status_text = "Risposta API Watchlist non riconosciuta."
                messagebox.showwarning("Risposta Sconosciuta", "L'API ha restituito una risposta non prevista per la Watchlist.")

            self.status_label.config(text=current_status_text)
            self.refresh_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass
        except Exception as e:
            self.status_label.config(text=f"Errore UI Watchlist: {e}")
            messagebox.showerror("Errore Interfaccia", f"Si è verificato un errore nell'interfaccia Watchlist:\n{e}")
            print(f"Errore in process_api_queue (WatchlistTab): {e}")
            if hasattr(self, 'refresh_button'):
                self.refresh_button.config(state=tk.NORMAL)
        finally:
            self.after(100, self.process_api_queue)