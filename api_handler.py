import requests
import json
from datetime import datetime # Per formattare la data dell'ultimo aggiornamento

COINGECKO_API_BASE_URL = "https://api.coingecko.com/api/v3"

def get_asset_price(asset_id, currency):
    """
    Recupera il prezzo corrente, la variazione 24h, il volume 24h 
    e l'ultimo aggiornamento per un dato asset_id e valuta.
    """
    url = f"{COINGECKO_API_BASE_URL}/simple/price"
    params = {
        'ids': asset_id,
        'vs_currencies': currency,
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true',
        'include_last_updated_at': 'true'
    }

    try:
        response = requests.get(url, params=params, timeout=10) # Timeout di 10 secondi
        response.raise_for_status()  # Solleva un'eccezione per errori HTTP (4xx o 5xx)
        data = response.json()

        if asset_id in data and currency in data[asset_id]:
            asset_data = data[asset_id]
            price = asset_data.get(currency)
            change_24h = asset_data.get(f'{currency}_24h_change')
            volume_24h = asset_data.get(f'{currency}_24h_vol')
            last_updated_timestamp = asset_data.get('last_updated_at')
            
            last_updated_str = "N/D"
            if last_updated_timestamp:
                last_updated_dt = datetime.fromtimestamp(last_updated_timestamp)
                last_updated_str = last_updated_dt.strftime('%Y-%m-%d %H:%M:%S')

            return {
                "price": price,
                "change_24h": change_24h,
                "volume_24h": volume_24h,
                "last_updated": last_updated_str,
                "currency": currency.upper()
            }
        else:
            return {"error": f"Dati non trovati per {asset_id} in {currency}."}

    except requests.exceptions.Timeout:
        return {"error": "Richiesta API scaduta (timeout)."}
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"Errore HTTP: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Errore nella richiesta API: {req_err}"}
    except json.JSONDecodeError:
        return {"error": "Errore nella decodifica della risposta JSON dall'API."}
    except Exception as e:
        return {"error": f"Un errore imprevisto è occorso: {e}"}
    
def get_watchlist_prices(asset_ids_list, vs_currencies_list):
    """
    Recupera i prezzi e altri dati per una lista di asset_ids
    contro una lista di valute.
    """
    if not asset_ids_list or not vs_currencies_list:
        return {"error": "La lista degli ID asset e delle valute non può essere vuota."}

    ids_string = ",".join(asset_ids_list)
    vs_currencies_string = ",".join(vs_currencies_list)

    url = f"{COINGECKO_API_BASE_URL}/simple/price"
    params = {
        'ids': ids_string,
        'vs_currencies': vs_currencies_string,
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true',
        'include_last_updated_at': 'true'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Formattiamo i dati per ogni asset richiesto
        results = {}
        for asset_id in asset_ids_list:
            if asset_id in data:
                asset_data = data[asset_id]
                formatted_asset_data = {}
                for currency in vs_currencies_list:
                    if currency in asset_data:
                        price = asset_data.get(currency)
                        change_24h = asset_data.get(f'{currency}_24h_change')
                        volume_24h = asset_data.get(f'{currency}_24h_vol')
                        
                        formatted_asset_data[currency] = {
                            "price": price,
                            "change_24h": change_24h,
                            "volume_24h": volume_24h,
                        }
                
                last_updated_timestamp = asset_data.get('last_updated_at')
                last_updated_str = "N/D"
                if last_updated_timestamp:
                    last_updated_dt = datetime.fromtimestamp(last_updated_timestamp)
                    last_updated_str = last_updated_dt.strftime('%Y-%m-%d %H:%M:%S')
                formatted_asset_data['last_updated'] = last_updated_str
                results[asset_id] = formatted_asset_data
            else:
                results[asset_id] = {"error": f"Dati non trovati per {asset_id}."}
        return results

    except requests.exceptions.Timeout:
        return {"error": "Richiesta API watchlist scaduta (timeout)."}
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"Errore HTTP watchlist: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Errore richiesta API watchlist: {req_err}"}
    except json.JSONDecodeError:
        return {"error": "Errore decodifica JSON watchlist."}
    except Exception as e:
        return {"error": f"Errore imprevisto watchlist: {e}"}
    
def get_market_cap_ranking(vs_currency='usd', top_n=10, page=1):
    """
    Recupera le prime top_n criptovalute ordinate per capitalizzazione di mercato.
    """
    url = f"{COINGECKO_API_BASE_URL}/coins/markets"
    params = {
        'vs_currency': vs_currency,
        'order': 'market_cap_desc', # Ordina per capitalizzazione di mercato decrescente
        'per_page': top_n,          # Numero di risultati per pagina
        'page': page,               # Pagina dei risultati da recuperare
        'sparkline': 'false',       # Non includere dati sparkline
        'price_change_percentage': '1h,24h,7d' # Includi variazioni di prezzo
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json() # Questa è una lista di dizionari
        
        # Estraiamo e formattiamo i dati che ci interessano
        ranked_list = []
        for rank_idx, coin_data in enumerate(data, start=1): # Usiamo rank_idx per il rank se non fornito o per controllo
            rank = coin_data.get('market_cap_rank', rank_idx)
            asset_id = coin_data.get('id')
            symbol = coin_data.get('symbol', '').upper()
            name = coin_data.get('name')
            current_price = coin_data.get('current_price')
            market_cap = coin_data.get('market_cap')
            total_volume = coin_data.get('total_volume')
            price_change_24h = coin_data.get('price_change_percentage_24h')
            # Aggiungiamo anche la variazione a 1h e 7d se vogliamo, visto che l'API la fornisce
            price_change_1h = None
            price_change_7d = None
            if coin_data.get('price_change_percentage_1h_in_currency') is not None:
                 price_change_1h = coin_data.get('price_change_percentage_1h_in_currency')
            if coin_data.get('price_change_percentage_7d_in_currency') is not None:
                 price_change_7d = coin_data.get('price_change_percentage_7d_in_currency')

            ranked_list.append({
                "rank": rank,
                "id": asset_id,
                "symbol": symbol,
                "name": name,
                "current_price": current_price,
                "market_cap": market_cap,
                "total_volume_24h": total_volume,
                "price_change_24h": price_change_24h,
                "price_change_1h": price_change_1h,
                "price_change_7d": price_change_7d,
                "vs_currency": vs_currency.upper()
            })
        return ranked_list

    except requests.exceptions.Timeout:
        return {"error": "Richiesta API Market Cap scaduta (timeout)."}
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"Errore HTTP Market Cap: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Errore richiesta API Market Cap: {req_err}"}
    except json.JSONDecodeError:
        return {"error": "Errore decodifica JSON Market Cap."}
    except Exception as e:
        return {"error": f"Errore imprevisto Market Cap: {e}"}
    
def get_historical_market_data(asset_id, vs_currency, days='max', interval='daily'):
    """
    Recupera i dati storici (prezzi, market cap, volumi) per un asset.
    'days' può essere un numero o 'max'.
    'interval' può essere 'daily' o, per periodi brevi, anche orario (ma l'API lo fornisce solo per certi 'days').
    """
    url = f"{COINGECKO_API_BASE_URL}/coins/{asset_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': interval # 'daily' per dati giornalieri
        # 'precision': 'full' # per la massima precisione decimale, opzionale
    }

    try:
        response = requests.get(url, params=params, timeout=20) # Timeout più lungo per dati potenzialmente grandi
        response.raise_for_status()
        data = response.json() # Contiene 'prices', 'market_caps', 'total_volumes'
        
        # I dati sono liste di [timestamp, valore]
        # Li trasformiamo in un formato più leggibile
        formatted_data = {
            "asset_id": asset_id,
            "vs_currency": vs_currency,
            "data_points": []
        }
        
        # Assumiamo che tutte le liste abbiano la stessa lunghezza e gli stessi timestamp
        # Prendiamo i prezzi come riferimento per la lunghezza
        if 'prices' in data and data['prices']:
            for i in range(len(data['prices'])):
                timestamp_ms = data['prices'][i][0]
                # Converti timestamp da millisecondi a secondi per datetime
                dt_object = datetime.fromtimestamp(timestamp_ms / 1000)
                date_str = dt_object.strftime("%Y-%m-%d %H:%M:%S") # O solo "%Y-%m-%d" se 'daily'

                price = data['prices'][i][1]
                market_cap = data['market_caps'][i][1] if i < len(data.get('market_caps', [])) else None
                total_volume = data['total_volumes'][i][1] if i < len(data.get('total_volumes', [])) else None
                
                formatted_data["data_points"].append({
                    "timestamp": timestamp_ms,
                    "date": date_str,
                    "price": price,
                    "market_cap": market_cap,
                    "total_volume": total_volume
                })
        else:
            return {"error": f"Nessun dato storico sui prezzi trovato per {asset_id}."}
            
        return formatted_data

    except requests.exceptions.Timeout:
        return {"error": "Richiesta API Dati Storici scaduta (timeout)."}
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"Errore HTTP Dati Storici: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Errore richiesta API Dati Storici: {req_err}"}
    except json.JSONDecodeError:
        return {"error": "Errore decodifica JSON Dati Storici."}
    except Exception as e:
        return {"error": f"Errore imprevisto Dati Storici: {e}"}

# Esempio di come usare la nuova funzione (puoi testarlo qui)
if __name__ == "__main__":
    print("--- Test get_asset_price ---")
    test_asset = "bitcoin"
    test_currency = "usd"
    price_info = get_asset_price(test_asset, test_currency)
    if "error" in price_info:
        print(f"Errore per {test_asset}: {price_info['error']}")
    else:
        print(f"Informazioni per {test_asset.capitalize()}:")
        print(f"  Prezzo: {price_info.get('price')} {price_info.get('currency')}")
        # Assicurati che change_24h sia un numero prima di formattarlo
        change_24h_val = price_info.get('change_24h')
        if isinstance(change_24h_val, (int, float)):
            print(f"  Variazione 24h: {change_24h_val:.2f}%")
        else:
            print(f"  Variazione 24h: {change_24h_val}") # Stampa N/D o il valore come è
        
        volume_24h_val = price_info.get('volume_24h')
        if isinstance(volume_24h_val, (int, float)):
            print(f"  Volume 24h: {volume_24h_val:,.2f} {price_info.get('currency')}")
        else:
            print(f"  Volume 24h: {volume_24h_val} {price_info.get('currency')}")
            
        print(f"  Ultimo aggiornamento: {price_info.get('last_updated')}")

    test_asset_error = "nonexistentcoin"
    price_info_error = get_asset_price(test_asset_error, test_currency)
    if "error" in price_info_error:
        print(f"\nTest Errore per '{test_asset_error}': {price_info_error['error']}")

    print("\n--- Test get_watchlist_prices ---")
    watchlist_test_ids = ["bitcoin", "ethereum", "cardano"]
    watchlist_test_currencies = ["usd", "eur"]
    watchlist_data = get_watchlist_prices(watchlist_test_ids, watchlist_test_currencies)

    if isinstance(watchlist_data, dict) and "error" in watchlist_data: # Controllo se è un dizionario di errore globale
        print(f"Errore Watchlist: {watchlist_data['error']}")
    elif isinstance(watchlist_data, dict): # Se è un dizionario di risultati
        for asset_id, data_by_currency in watchlist_data.items():
            print(f"\nAsset: {asset_id.capitalize()}")
            if isinstance(data_by_currency, dict) and "error" in data_by_currency:
                print(f"  Errore per {asset_id}: {data_by_currency['error']}")
                continue
            
            # Gestione per la struttura dati di get_watchlist_prices
            last_updated_val = data_by_currency.get('last_updated', 'N/D')
            for currency_key, details in data_by_currency.items():
                if currency_key == 'last_updated': # Salta la chiave 'last_updated' qui
                    continue
                print(f"  Valuta: {currency_key.upper()}")
                print(f"    Prezzo: {details.get('price', 'N/D')}")
                
                change_24h_detail = details.get('change_24h')
                if isinstance(change_24h_detail, (int, float)):
                     print(f"    Variazione 24h: {change_24h_detail:.2f}%")
                else:
                    print(f"    Variazione 24h: {change_24h_detail}")

                volume_24h_detail = details.get('volume_24h')
                if isinstance(volume_24h_detail, (int, float)):
                    print(f"    Volume 24h: {volume_24h_detail:,.2f}")
                else:
                    print(f"    Volume 24h: {volume_24h_detail}")

            print(f"  Ultimo aggiornamento: {last_updated_val}")
    else:
        print("Errore: formato dati watchlist non riconosciuto.")


    print("\n--- Test get_market_cap_ranking ---")
    top_coins = get_market_cap_ranking(vs_currency='eur', top_n=3) # Ridotto a 3 per brevità output

    if isinstance(top_coins, dict) and "error" in top_coins:
        print(f"Errore Market Cap: {top_coins['error']}")
    elif isinstance(top_coins, list):
        print(f"Top 3 coins in EUR:")
        for coin in top_coins:
            print(f"  Rank: {coin.get('rank', 'N/A')}, Nome: {coin.get('name', 'N/A')} ({coin.get('symbol', 'N/A')}), "
                  f"Prezzo: {coin.get('current_price', 'N/A')} {coin.get('vs_currency', '')}, "
                  f"Mkt Cap: {coin.get('market_cap', 'N/A')} {coin.get('vs_currency', '')}")
    else:
        print("Errore: formato dati market cap non riconosciuto.")
    
    print("\n--- Test Dati Storici ---")
    historical_data = get_historical_market_data(asset_id='bitcoin', vs_currency='usd', days='7')

    if isinstance(historical_data, dict) and "error" in historical_data:
        print(f"Errore Dati Storici: {historical_data['error']}")
    elif isinstance(historical_data, dict) and "data_points" in historical_data:
        print(f"Dati storici per {historical_data['asset_id']} in {historical_data['vs_currency']} (primi 3 punti):")
        for point in historical_data["data_points"][:3]: # Stampa solo i primi 3 per brevità
            print(f"  Data: {point['date']}, Prezzo: {point['price']:.2f}, "
                  f"Mkt Cap: {point['market_cap']:.0f}, Volume: {point['total_volume']:.0f}")
        print(f"  ... e altri {len(historical_data['data_points']) - 3} punti.")
    else:
        print("Errore: formato dati storici non riconosciuto.")