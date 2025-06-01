import json
import os

CONFIG_FILE_PATH = "config.json"

DEFAULT_CONFIG = {
    "watchlist_ids": ["bitcoin", "ethereum", "cardano", "solana", "dogecoin", "tron"],
    "default_vs_currency": "usd",
    "default_rank_top_n": 20,
    "default_download_days": 30,
    "price_tab_default_asset_id": "bitcoin",
    "price_tab_default_currency": "usd", # Potrebbe essere uguale a default_vs_currency
    "converter_tab_default_amount": "1",
    "converter_tab_default_from_asset": "bitcoin",
    "converter_tab_default_to_currency": "eur", # Magari diversa per mostrare la differenza
    "download_tab_default_asset_id": "bitcoin",
    "download_tab_default_file_format": "CSV"
    # Potremmo aggiungere altre impostazioni qui in futuro
    # come le valute preferite per le ComboBox, tema dell'app, ecc.
}

def load_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        print(f"File di configurazione '{CONFIG_FILE_PATH}' non trovato. Creazione con valori di default...")
        save_config(DEFAULT_CONFIG) 
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            # Aggiungiamo un semplice meccanismo di "migrazione" o aggiornamento:
            # se mancano chiavi nel file caricato, le aggiungiamo dai default.
            updated = False
            for key, value in DEFAULT_CONFIG.items():
                if key not in config_data:
                    config_data[key] = value
                    updated = True
            if updated:
                print("Configurazione aggiornata con nuove chiavi di default. Salvataggio...")
                save_config(config_data)
            return config_data
    except json.JSONDecodeError:
        print(f"Errore nella decodifica di '{CONFIG_FILE_PATH}'. Il file potrebbe essere corrotto.")
        print("Utilizzo e salvataggio della configurazione di default.")
        save_config(DEFAULT_CONFIG) 
        return DEFAULT_CONFIG
    except Exception as e:
        print(f"Errore imprevisto durante il caricamento della configurazione: {e}")
        print("Utilizzo e salvataggio della configurazione di default.")
        save_config(DEFAULT_CONFIG) 
        return DEFAULT_CONFIG

def save_config(config_data):
    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"Configurazione salvata in '{CONFIG_FILE_PATH}'")
        return True
    except Exception as e:
        print(f"Errore durante il salvataggio della configurazione: {e}")
        return False

# Esempio di come usare le funzioni (puoi testarlo eseguendo questo file direttamente)
if __name__ == "__main__":
    print("Test del config_manager...")
    
    # Simula la prima esecuzione (cancella il file se esiste per testare la creazione)
    if os.path.exists(CONFIG_FILE_PATH):
        print(f"Rimuovo il file '{CONFIG_FILE_PATH}' esistente per il test...")
        os.remove(CONFIG_FILE_PATH)
        
    print("\nCaricamento configurazione (dovrebbe creare il file di default):")
    current_config = load_config()
    print("Configurazione caricata/creata:", current_config)
    
    print(f"\nVerifica se '{CONFIG_FILE_PATH}' è stato creato:")
    print(f"Esiste? {os.path.exists(CONFIG_FILE_PATH)}")

    print("\nModifica di un valore e salvataggio:")
    current_config["watchlist_ids"].append("polkadot")
    current_config["default_vs_currency"] = "eur"
    if save_config(current_config):
        print("Ricaricamento della configurazione per verificare le modifiche:")
        reloaded_config = load_config()
        print("Configurazione ricaricata:", reloaded_config)
        if reloaded_config["default_vs_currency"] == "eur" and "polkadot" in reloaded_config["watchlist_ids"]:
            print("Test di modifica e ricaricamento riuscito!")
        else:
            print("ERRORE nel test di modifica e ricaricamento.")
    else:
        print("ERRORE nel salvataggio della configurazione modificata.")