#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Esempio di GUI in Tkinter - Applicazione Python
"""

import tkinter as tk
from tkinter import ttk, messagebox

class AppTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Applicazione Tkinter - GUI Python")
        self.root.geometry("400x300")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Label
        self.label = ttk.Label(
            main_frame, 
            text="Benvenuto in Tkinter!",
            font=("Arial", 16)
        )
        self.label.grid(row=0, column=0, pady=10)
        
        # Entry per input
        self.entry = ttk.Entry(main_frame, width=30)
        self.entry.grid(row=1, column=0, pady=5)
        self.entry.insert(0, "Inserisci qui...")
        
        # Label per messaggio
        self.message_label = ttk.Label(main_frame, text="", font=("Arial", 14))
        self.message_label.grid(row=2, column=0, pady=5)
        
        # Button di invio
        self.send_button = ttk.Button(
            main_frame, 
            text="Invia", 
            command=self.on_send
        )
        self.send_button.grid(row=3, column=0, pady=10)
        
        # Button di reset
        self.reset_button = ttk.Button(
            main_frame, 
            text="Resetta",
            command=self.on_reset
        )
        self.reset_button.grid(row=4, column=0, pady=5)
        
        # Frame per informazioni
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=5, column=0, pady=10, sticky="ew")
        
        ttk.Label(info_frame, text="Versione:").grid(row=0, column=0, padx=5, sticky="w")
        ttk.Label(info_frame, text="Versione Python:").grid(row=0, column=1, padx=20, sticky="w")
        ttk.Label(info_frame, text="Tecnologia:").grid(row=0, column=2, padx=5, sticky="w")
        
    def on_send(self):
        input_text = self.entry.get().strip()
        if input_text:
            self.message_label.configure(text=f"Messaggio ricevuto: {input_text}")
            self.entry.delete(0, 'end')
        else:
            messagebox.showwarning("Avviso", "Inserire qualcosa di valido!")
    
    def on_reset(self):
        self.message_label.configure(text="")
        self.entry.delete(0, 'end')


def main():
    root = tk.Tk()
    app = AppTkinter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
