import tkinter as tk
from tkinter import ttk

from gui_tabs.price_tab import PriceTab
from gui_tabs.watchlist_tab import WatchlistTab
from gui_tabs.converter_tab import ConverterTab
from gui_tabs.rank_tab import RankTab
from gui_tabs.download_tab import DownloadTab
from gui_tabs.chart_tab import ChartTab # NUOVO IMPORT

def setup_gui():
    root = tk.Tk()
    root.title("PyCryptoDesk")
    # Potremmo aver bisogno di più spazio per il grafico, aumentiamo un po' le dimensioni
    root.geometry("1150x750") 
    root.minsize(800, 600) # Minimo per non stringere troppo i grafici    

    style = ttk.Style()
    try:
        style.theme_use('clam')
    except tk.TclError:
        print("Tema 'clam' non trovato, uso il default.")

    notebook = ttk.Notebook(root, padding="10 10 10 10")

    price_fetch_tab = PriceTab(notebook, padding="10")
    notebook.add(price_fetch_tab, text='Prezzo Singolo')

    watchlist_view_tab = WatchlistTab(notebook, padding="10")
    notebook.add(watchlist_view_tab, text='Watchlist')

    converter_tool_tab = ConverterTab(notebook, padding="10")
    notebook.add(converter_tool_tab, text='Convertitore Valute')

    rank_view_tab = RankTab(notebook, padding="10")
    notebook.add(rank_view_tab, text='Classifica Market Cap')

    download_data_tab = DownloadTab(notebook, padding="10")
    notebook.add(download_data_tab, text='Download Storico')

    # NUOVA SCHEDA GRAFICO
    chart_display_tab = ChartTab(notebook, padding="10")
    notebook.add(chart_display_tab, text='Grafico')


    notebook.pack(expand=True, fill='both')
    root.mainloop()

if __name__ == "__main__":
    setup_gui()