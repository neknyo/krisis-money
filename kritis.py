import customtkinter as ctk
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import tkinter.ttk as ttk

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

SPENDING_FILE = "spending.csv"
INCOME_FILE = "income.csv"

# ----------------------------
# not so important functions ithink
# ----------------------------
def load_csv(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file, names=cols, header=None)
    else:
        df = pd.DataFrame(columns=cols)
    return df

def save_csv(df, file):
    df.to_csv(file, index=False, header=False)

# ----------------------------
# ther real deal Core Functions
# ----------------------------
def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    
    df = load_csv(SPENDING_FILE, ["date", "time", "amount", "category"])
    if not df.empty:
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%m/%d/%Y %H:%M', errors='coerce')
        df.sort_values(by='datetime', ascending=False, inplace=True)
        df.drop(columns=['datetime'], inplace=True)

    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))
    
    update_balance()
    show_spending_graphs_animated()


def add_spending():
    df = load_csv(SPENDING_FILE, ["date", "time", "amount", "category"])
    now = datetime.now()
    try:
        amt = float(amount_entry.get())
    except ValueError:
        ctk.CTkMessagebox(title="Error", message="Enter a valid number for amount.", icon="cancel")
        return
    new_row = {
        "date": now.strftime("%d/%m/%y"),
        "time": now.strftime("%H:%M"),
        "amount": amt,
        "category": category_entry.get()
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(df, SPENDING_FILE)
    refresh_table()
    amount_entry.delete(0, "end")
    category_entry.set(categories[0])

def remove_spending():
    selected_item = tree.selection()
    if not selected_item:
        ctk.CTkMessagebox(title="Warning", message="Select a row to remove.", icon="warning")
        return

    selected_values = tree.item(selected_item[0])['values']
    df = load_csv(SPENDING_FILE, ["date", "time", "amount", "category"])

    df['amount'] = df['amount'].astype(float)
    row_to_drop = df[
        (df['date'] == str(selected_values[0])) &
        (df['time'] == str(selected_values[1])) &
        (df['amount'] == float(selected_values[2])) &
        (df['category'] == str(selected_values[3]))
    ]

    if not row_to_drop.empty:
        df = df.drop(row_to_drop.index[0])

    save_csv(df, SPENDING_FILE)
    refresh_table()

def open_income_window():
    income_win = ctk.CTkToplevel(root)
    income_win.title("Add Income")
    income_win.geometry("400x200")

    ctk.CTkLabel(income_win, text="Income:").pack(pady=10)
    entry = ctk.CTkEntry(income_win, placeholder_text="Enter income")
    entry.pack(pady=5)

    def save_income():
        df = load_csv(INCOME_FILE, ["date", "time", "amount", "note"])
        now = datetime.now()
        try:
            amt = float(entry.get())
        except ValueError:
            ctk.CTkMessagebox(title="Error", message="Enter a valid number for income.", icon="cancel")
            return
        new_row = {
            "date": now.strftime("%-d/%-m/%Y"),
            "time": now.strftime("%H:%M"),
            "amount": amt,
            "note": "Income logged"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df, INCOME_FILE)
        refresh_table()
        income_win.destroy()

    ctk.CTkButton(income_win, text="Save Income", command=save_income, corner_radius=5).pack(pady=10)

def update_balance():
    spend_df = load_csv(SPENDING_FILE, ["date", "time", "amount", "category"])
    income_df = load_csv(INCOME_FILE, ["date", "time", "amount", "note"])

    total_spending = pd.to_numeric(spend_df["amount"], errors='coerce').sum()
    total_income = pd.to_numeric(income_df["amount"], errors='coerce').sum()
    balance = total_income - total_spending

    balance_label.configure(text=f"Balance: {balance:,.2f}")

#----------------------
# kok gini sih yatuhan
#----------------------

def show_spending_graphs_animated():
    for widget in graph_frame.winfo_children():
        widget.destroy()

    df = load_csv(SPENDING_FILE, ["date", "time", "amount", "category"])
    if df.empty:
        ctk.CTkLabel(graph_frame, text="No spending data to display").pack(pady=10)
        return

    df["amount"] = pd.to_numeric(df["amount"], errors='coerce').fillna(0)
    
    df['date_obj'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
    df.dropna(subset=['date_obj'], inplace=True)
    
    if df.empty:
        ctk.CTkLabel(graph_frame, text="No valid date entries found.").pack(pady=10)
        return

    daily_spending = df.groupby(df['date_obj'].dt.strftime('%m/%d'))["amount"].sum()
    category_spending = df.groupby("category")["amount"].sum()

    plt.style.use('dark_background')
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    fig.patch.set_facecolor('#454548')

    # ---------------------
    # barely working bar Chart 
    # ---------------------
    axes[0].set_facecolor('#454548')
    bars = axes[0].bar(daily_spending.index, [0]*len(daily_spending), color="#1f77b4")
    axes[0].set_title("Daily Spending", color='white')
    axes[0].tick_params(axis='x', rotation=45, colors='white', labelsize=8)
    axes[0].tick_params(axis='y', colors='white', labelsize=8)
    
    axes[0].set_ylim(0, 200000)

    #–––––––––––––––
    # kinda working Pie Chart 
    #–––––––––––––––
    axes[1].set_facecolor('#454548')
    wedges, texts, autotexts = axes[1].pie(category_spending, labels=category_spending.index, autopct="%1.1f%%", startangle=140)
    for text in texts:
        text.set_color('white')
    for autotext in autotexts:
        autotext.set_color('black')
    axes[1].set_title("Spending by Category", color='white')

    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def animate(frame):
        # Adjust animation to the new fixed scale
        for bar, height in zip(bars, daily_spending.values):
            # We don't need to change the height logic, set_ylim handles the view
            bar.set_height(height * frame / 20)
    
    canvas.anim = FuncAnimation(fig, animate, frames=20, interval=50, repeat=False)


# ----------------------------
# Setup UI
# ----------------------------
refreshimg = ctk.CTkImage(Image.open("img/Refresh.png"), size=(20, 20))
deleteimg = ctk.CTkImage(Image.open("img/Delete.png"), size=(22, 18))
incomeimg = ctk.CTkImage(Image.open("img/Income.png"), size=(20, 20))

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Kritis Muani Log")
root.geometry("900x700")

main_frame = ctk.CTkFrame(root, fg_color="#1a1f22", corner_radius=0)
main_frame.pack(fill="both", expand=True)

sidebar = ctk.CTkFrame(main_frame, width=63, fg_color="#1a1f22", corner_radius=0)
sidebar.pack(side="left", fill="y", padx=(5,0), pady=5)
sidebar.pack_propagate(False)

content = ctk.CTkFrame(main_frame, fg_color="#454548", corner_radius=8)
content.pack(side="left", fill="both", expand=True, padx=5, pady=5)

ctk.CTkButton(sidebar, image=refreshimg, text="", command=refresh_table, fg_color="#160707", hover_color="#260d0d", corner_radius=10, width=50).pack(pady=8)
ctk.CTkButton(sidebar, image=deleteimg, text="", command=remove_spending, fg_color="#160707", hover_color="#260d0d", corner_radius=10, width=50).pack(pady=8)
ctk.CTkButton(sidebar, image=incomeimg, text="", command=open_income_window, fg_color="#160707", hover_color="#260d0d", corner_radius=10, width=50).pack(side="bottom", pady=30)

tree_frame = ctk.CTkFrame(content, fg_color="transparent")
tree_frame.pack(fill="both", expand=True, padx=10, pady=(10,5))

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", relief="flat")
style.configure("Treeview.Heading", background="#454548", foreground="white", font=("Arial", 12, "bold"), relief="flat")
style.map("Treeview", background=[("selected", "#1f6aa5")])

tree = ttk.Treeview(tree_frame, columns=("date", "time", "amount", "category"), show="headings")
tree.heading("date", text="Date")
tree.heading("time", text="Time")
tree.heading("amount", text="Amount")
tree.heading("category", text="Category")
tree.column("date", width=100, anchor="center")
tree.column("time", width=80, anchor="center")
tree.column("amount", width=120, anchor="center")
tree.column("category", width=150, anchor="center")
tree.pack(fill="both", expand=True)

form_frame = ctk.CTkFrame(content, fg_color="transparent")
form_frame.pack(pady=5, fill="x", padx=10)
ctk.CTkLabel(form_frame, text="Amount:").pack(side="left", padx=(10,5))
amount_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter amount", corner_radius=10)
amount_entry.pack(side="left", padx=5, expand=True, fill='x')
ctk.CTkLabel(form_frame, text="Category:").pack(side="left", padx=(10,5))
categories = ["...", "Entertainment", "Supplies", "Food", "Bills", "Transport", "Miscellaneous", "Others"]
category_entry = ctk.CTkComboBox(form_frame, values=categories, corner_radius=10)
category_entry.pack(side="left", padx=5, expand=True, fill='x')
category_entry.set(categories[0])
ctk.CTkButton(form_frame, text="Add Spending", command=add_spending, corner_radius=10).pack(side="left", padx=10)

balance_label = ctk.CTkLabel(content, text="Balance: 0.00", font=("Arial", 16, "bold"))
balance_label.pack(pady=5)

graph_frame = ctk.CTkFrame(content, fg_color="transparent")
graph_frame.pack(fill="both", expand=True, padx=10, pady=(5,10))

refresh_table()
root.mainloop()
